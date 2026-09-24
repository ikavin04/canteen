from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import json
import uuid
import random
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

import hmac
import hashlib
from dotenv import load_dotenv

# Load environment variables from backend/.env if present
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
CORS(app, supports_credentials=True)

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'canteen')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Kavin04')
DB_PORT = os.environ.get('DB_PORT', '5432')

# Razorpay Configuration
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    razorpay = None
    RAZORPAY_AVAILABLE = False

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        db_url = DATABASE_URL
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return psycopg2.connect(db_url)
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        hdr_uid = request.headers.get('X-User-Id')
        if hdr_uid and str(hdr_uid).isdigit():
            session['user_id'] = int(hdr_uid)

        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        hdr_uid = request.headers.get('X-User-Id')
        hdr_role = request.headers.get('X-User-Role')
        if hdr_uid and str(hdr_uid).isdigit() and hdr_role:
            session['user_id'] = int(hdr_uid)
            session['role'] = hdr_role

        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def generate_unique_order_id(user_type, conn):
    """Generate a unique order ID based on user type with format ORD-{PREFIX}{6-digit-number}"""
    # Define prefixes based on user type
    prefix_map = {
        'Student': 'STU',
        'Staff': 'FAC', 
        'Faculty': 'FAC',
        'Guest': 'GUE'
    }
    
    prefix = prefix_map.get(user_type, 'GUE')  # Default to guest prefix if type not found
    
    # Keep trying until we get a unique order ID
    max_attempts = 100  # Prevent infinite loop
    for _ in range(max_attempts):
        # Generate random 6-digit number
        random_number = random.randint(100000, 999999)
        order_id = f'ORD-{prefix}{random_number}'
        
        # Check if this order ID already exists
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM orders WHERE order_id = %s', (order_id,))
        count = cur.fetchone()[0]
        cur.close()
        
        if count == 0:
            return order_id
    
    # Fallback if we can't generate unique ID (very unlikely)
    return f'ORD-{prefix}{uuid.uuid4().hex[:6].upper()}'


def init_db():
    """Create users, menu_items, and orders tables if they don't exist, and seed demo accounts."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                user_type TEXT DEFAULT 'Student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create menu_items table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id SERIAL PRIMARY KEY,
                item_name TEXT NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                availability BOOLEAN DEFAULT true,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create orders table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            items JSONB NOT NULL,
            total_amount NUMERIC(10, 2) NOT NULL,
            status TEXT DEFAULT 'Pending',
            payment_method TEXT,
            payment_status TEXT DEFAULT 'Pending',
            transaction_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Insert demo users with hashed passwords
        admin_hash = generate_password_hash('admin123')
        user_hash = generate_password_hash('user123')
        cur.execute("""
        INSERT INTO users (username, email, password, role) 
        VALUES ('admin', 'admin@canteen.com', %s, 'admin')
        ON CONFLICT (username) DO UPDATE SET password = EXCLUDED.password
        """, (admin_hash,))
        
        cur.execute("""
        INSERT INTO users (username, email, password, role) 
        VALUES ('user', 'user@canteen.com', %s, 'user')
        ON CONFLICT (username) DO UPDATE SET password = EXCLUDED.password
        """, (user_hash,))
        
        # One-time migration: re-hash any existing plain-text passwords
        cur.execute("SELECT id, password FROM users")
        for u_id, u_pw in cur.fetchall():
            if not (u_pw.startswith('scrypt:') or u_pw.startswith('pbkdf2:') or u_pw.startswith('argon2:')):
                cur.execute("UPDATE users SET password = %s WHERE id = %s", (generate_password_hash(u_pw), u_id))
        
        # Ensure unique constraint on item_name for safe idempotent upsert
        try:
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'menu_items_item_name_key'
                    ) THEN
                        ALTER TABLE menu_items ADD CONSTRAINT menu_items_item_name_key UNIQUE (item_name);
                    END IF;
                END $$;
            """)
        except Exception:
            pass

        # 30 Curated Canteen Menu Items (Breakfast, Snacks, Beverages, Main Course, Desserts)
        menu_seed_items = [
            ('Tea', 20.00, 'Beverages', 'Aromatic hot Indian masala chai infused with ginger, cardamom, and clove.', True, 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=500'),
            ('Filter Coffee', 30.00, 'Beverages', 'Traditional South Indian filter coffee brewed with fresh chicory blend and frothy milk.', True, 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500'),
            ('Cold Coffee', 55.00, 'Beverages', 'Rich blended iced coffee topped with chocolate syrup and creamy foam.', True, 'https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?w=500'),
            ('Fresh Lime Soda', 35.00, 'Beverages', 'Zesty, fizzy sparkling soda with fresh squeezed lemon juice and mint.', True, 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500'),
            ('Mango Lassi', 45.00, 'Beverages', 'Thick and chilled yogurt smoothie blended with sweet Alphonso mango pulp.', True, 'https://images.unsplash.com/photo-1553787499-6f9133860278?w=500'),
            ('Badam Milk', 40.00, 'Beverages', 'Warm aromatic milk simmered with crushed almonds, saffron strands, and cardamom.', True, 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500'),
            ('Samosa', 25.00, 'Snacks', 'Crisp, golden-fried triangular pastries stuffed with spiced potatoes and green peas.', True, 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500'),
            ('Paneer Puff', 35.00, 'Snacks', 'Flaky, layered puff pastry filled with mildly spiced marinated paneer cubes.', True, 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500'),
            ('French Fries', 60.00, 'Snacks', 'Crispy golden potato fingers tossed in sea salt, served with herb ketchup.', True, 'https://images.unsplash.com/photo-1576107232684-1279f3908594?w=500'),
            ('Veg Cutlet', 30.00, 'Snacks', 'Hearty pan-fried vegetable patties coated in crispy breadcrumbs with mint dip.', True, 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=500'),
            ('Onion Pakoda', 35.00, 'Snacks', 'Crunchy gram flour fritters studded with sliced onions, green chilies, and curry leaves.', True, 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=500'),
            ('Mirchi Bajji', 30.00, 'Snacks', 'Plump green banana peppers dipped in spiced chickpea batter and fried golden crisp.', True, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500'),
            ('Vegetable Sandwich', 70.00, 'Snacks', 'Fresh multigrain bread layered with cucumber, tomato, beetroot, and mint chutney.', True, 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500'),
            ('Masala Dosa', 70.00, 'Breakfast', 'Crisp golden fermented rice crepe smeared with red chutney and spiced potato mash.', True, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500'),
            ('Idli Vada Combo', 55.00, 'Breakfast', 'Two feather-light steamed rice cakes paired with a crisp medu vada and hot sambar.', True, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500'),
            ('Poori Masala', 65.00, 'Breakfast', 'Three puffy deep-fried golden pooris served with flavorful potato sagu.', True, 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=500'),
            ('Ven Pongal', 50.00, 'Breakfast', 'Comforting rice and yellow moong dal cooked with pure ghee, black pepper, and cashews.', True, 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500'),
            ('Medu Vada', 40.00, 'Breakfast', 'Two crunchy savory lentil donuts infused with peppercorns, curry leaves, and ginger.', True, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500'),
            ('Aloo Paratha', 60.00, 'Breakfast', 'Golden griddle-toasted whole wheat flatbread filled with seasoned mashed potatoes.', True, 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=500'),
            ('Chicken Burger', 120.00, 'Main Course', 'Grilled juicy chicken patty with cheddar cheese slice, fresh lettuce, and garlic mayo.', True, 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500'),
            ('Veg Burger', 85.00, 'Main Course', 'Crispy spiced vegetable patty topped with melted cheese, tomato, and tangy secret sauce.', True, 'https://images.unsplash.com/photo-1550547660-d9450f859349?w=500'),
            ('Chicken Biryani', 160.00, 'Main Course', 'Fragrant long-grain basmati rice slow-cooked with spiced marinated chicken and onion raita.', True, 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500'),
            ('Veg Dum Biryani', 110.00, 'Main Course', 'Aromatic basmati rice layered with garden veggies, saffron, fried onions, and salan.', True, 'https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=500'),
            ('Paneer Butter Masala with Roti', 130.00, 'Main Course', 'Velvety butter-tomato gravy with soft paneer cubes, served with 3 warm phulkas.', True, 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500'),
            ('Dal Tadka with Jeera Rice', 95.00, 'Main Course', 'Yellow toor dal tempered with garlic and cumin, paired with aromatic ghee jeera rice.', True, 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500'),
            ('Pasta', 130.00, 'Main Course', 'Italian penne pasta tossed in creamy parmesan Alfredo sauce with herbs and olives.', True, 'https://images.unsplash.com/photo-1621996346565-e3d5d6281699?w=500'),
            ('Pizza Slice', 90.00, 'Main Course', 'Generous slice of stone-baked pizza loaded with molten mozzarella and bell peppers.', True, 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500'),
            ('Gulab Jamun', 40.00, 'Desserts', 'Warm melt-in-mouth milk solid spheres immersed in fragrant cardamom rose sugar syrup.', True, 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500'),
            ('Ice Cream', 45.00, 'Desserts', 'Creamy double-vanilla ice cream cup topped with crunchy waffle cone crisps.', True, 'https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=500'),
            ('Chocolate Brownie', 75.00, 'Desserts', 'Warm dense Belgian chocolate fudge brownie with dark chocolate drizzle.', True, 'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500')
        ]

        for item in menu_seed_items:
            try:
                cur.execute("""
                    INSERT INTO menu_items (item_name, price, category, description, availability, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (item_name) DO UPDATE SET
                        price = EXCLUDED.price,
                        category = EXCLUDED.category,
                        description = EXCLUDED.description,
                        image_url = EXCLUDED.image_url
                """, item)
            except Exception:
                # Fallback if unique constraint is missing
                cur.execute("SELECT 1 FROM menu_items WHERE LOWER(item_name) = LOWER(%s)", (item[0],))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO menu_items (item_name, price, category, description, availability, image_url)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, item)
        conn.commit()
        cur.close()
        conn.close()
        print("Database tables initialized successfully.")
        print("Demo users: admin/admin123 (admin), user/user123 (user)")
    except Exception as e:
        print('init_db error:', e)


# Ensure DB tables exist on startup
init_db()

# Serve frontend files (project root is one level up from backend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))


@app.route('/')
def index():
    # Serve index.html from project root if present, otherwise show API status
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIR, 'index.html')
    return jsonify({'status': 'ok', 'message': 'Smart Canteen API running'})


@app.route('/favicon.ico')
def favicon():
    fav = os.path.join(FRONTEND_DIR, 'favicon.ico')
    if os.path.exists(fav):
        return send_from_directory(FRONTEND_DIR, 'favicon.ico')
    # return empty 204 so browser console doesn't keep logging 404
    return ('', 204)


@app.route('/<path:filename>')
def serve_static(filename):
    # If an API route was requested and not found, return JSON 404
    if filename.startswith('api/') or request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'API endpoint not found'}), 404
    # Serve other frontend static files (css, js, html)
    file_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, filename)
    page_404 = os.path.join(FRONTEND_DIR, '404.html')
    if os.path.exists(page_404):
        return send_from_directory(FRONTEND_DIR, '404.html'), 404
    return jsonify({'success': False, 'message': 'Page not found'}), 404

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'API endpoint not found'}), 404
    page_404 = os.path.join(FRONTEND_DIR, '404.html')
    if os.path.exists(page_404):
        return send_from_directory(FRONTEND_DIR, '404.html'), 404
    return jsonify({'success': False, 'message': 'Page not found'}), 404

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'razorpay_enabled': bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET),
        'razorpay_sdk': RAZORPAY_AVAILABLE
    })


@app.route('/api/users/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type', 'Student')
    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'username,email,password required'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        hashed_password = generate_password_hash(password)
        cur.execute('INSERT INTO users (username, email, password, user_type) VALUES (%s,%s,%s,%s) RETURNING id, username, email, role, user_type', (username, email, hashed_password, user_type))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'user': {'id': row[0], 'username': row[1], 'email': row[2], 'role': row[3], 'user_type': row[4]}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/users/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'success': False, 'message': 'username and password required'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT id, username, email, password, role, user_type FROM users WHERE username=%s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        # Store user in session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'user_type': user['user_type']
        }
        return jsonify({'success': True, 'user': user_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/users/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route('/api/users', methods=['GET'])
@admin_required
def api_get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT id, username, email, role, user_type, created_at FROM users ORDER BY created_at DESC')
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.get_json() or {}
    cart = data.get('cart', [])
    payment_method = data.get('payment_method', 'UPI')
    
    # Handle both direct user_id and nested user object
    user_id = data.get('user_id')
    if not user_id:
        user = data.get('user') or {}
        user_id = user.get('id') if isinstance(user, dict) else None

    if not cart:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400

    # Basic server-side validation for cart items
    for item in cart:
        if not all(k in item for k in ('id', 'name', 'price', 'quantity')):
            return jsonify({'success': False, 'message': 'Invalid cart item format'}), 400
        try:
            qty = int(item['quantity'])
            price = float(item['price'])
            if qty <= 0:
                return jsonify({'success': False, 'message': 'Item quantity must be greater than 0'}), 400
            if price < 0:
                return jsonify({'success': False, 'message': 'Item price cannot be negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid price or quantity in cart'}), 400

    # Validate item existence in database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        item_ids = [int(item['id']) for item in cart if str(item.get('id')).isdigit()]
        if len(item_ids) != len(cart):
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid item ID format'}), 400
        
        cur.execute("SELECT id FROM menu_items WHERE id = ANY(%s)", (item_ids,))
        found_ids = {row[0] for row in cur.fetchall()}
        for i_id in item_ids:
            if i_id not in found_ids:
                cur.close()
                conn.close()
                return jsonify({'success': False, 'message': f'Item ID {i_id} does not exist'}), 400
        
        total_amount = sum(float(i['price']) * int(i['quantity']) for i in cart)
        
        # Get user type for order ID generation
        cur.execute('SELECT user_type FROM users WHERE id = %s', (user_id,))
        user_row = cur.fetchone()
        if not user_row:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        user_type = user_row[0]
        
        # Generate unique order ID based on user type
        order_id = generate_unique_order_id(user_type, conn)
        transaction_id = 'TXN' + uuid.uuid4().hex[:10].upper()
        
        # Insert the order
        cur.execute("INSERT INTO orders (order_id, user_id, items, total_amount, status, payment_method, payment_status, transaction_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING order_id",
                    (order_id, user_id, Json(cart), total_amount, 'Uncompleted', payment_method, 'Paid', transaction_id))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Payment processed', 'orderId': row[0] if row else order_id, 'amount': total_amount})
    except Exception as e:
        print('DB error:', e)
        if 'conn' in locals() and conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== RAZORPAY PAYMENT APIs ====================

@app.route('/api/payment/razorpay/create-order', methods=['POST'])
def razorpay_create_order():
    """Create a Razorpay order or simulated order for dual-mode execution."""
    data = request.get_json() or {}
    cart = data.get('cart', [])
    user_id = data.get('user_id')
    if not user_id:
        user = data.get('user') or {}
        user_id = user.get('id') if isinstance(user, dict) else None

    if not cart:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400

    try:
        amount = float(data.get('amount') or sum(float(i['price']) * int(i['quantity']) for i in cart))
        amount_in_paise = int(round(amount * 100))
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid amount calculation'}), 400

    is_live_key = (
        RAZORPAY_AVAILABLE and
        RAZORPAY_KEY_ID and
        RAZORPAY_KEY_SECRET and
        not RAZORPAY_KEY_ID.startswith('rzp_test_your') and
        len(RAZORPAY_KEY_ID) > 10
    )

    if is_live_key:
        try:
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            receipt_id = f"rcpt_{uuid.uuid4().hex[:10]}"
            rzp_order = client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': receipt_id,
                'payment_capture': 1
            })
            return jsonify({
                'success': True,
                'mode': 'live',
                'order_id': rzp_order['id'],
                'amount': amount_in_paise,
                'currency': 'INR',
                'key_id': RAZORPAY_KEY_ID
            })
        except Exception as e:
            print('Razorpay API call error (falling back to dual-mode simulator):', e)

    # Demo mode fallback ensures the checkout never breaks
    mock_order_id = f"order_rzp_{uuid.uuid4().hex[:14]}"
    return jsonify({
        'success': True,
        'mode': 'demo',
        'order_id': mock_order_id,
        'amount': amount_in_paise,
        'currency': 'INR',
        'key_id': RAZORPAY_KEY_ID if RAZORPAY_KEY_ID else 'rzp_test_smartcanteen'
    })


@app.route('/api/payment/razorpay/verify', methods=['POST'])
def razorpay_verify_payment():
    """Verify Razorpay payment signature and record order."""
    data = request.get_json() or {}
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature', '')
    cart = data.get('cart', [])
    user_id = data.get('user_id')
    if not user_id:
        user = data.get('user') or {}
        user_id = user.get('id') if isinstance(user, dict) else None

    if not cart or not user_id:
        return jsonify({'success': False, 'message': 'Cart and user ID required'}), 400

    # Record payment failure when reported by gateway
    if data.get('payment_status') in ('Failed', 'failed') or data.get('status') == 'failed':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT user_type FROM users WHERE id = %s', (user_id,))
            user_row = cur.fetchone()
            user_type = user_row[0] if user_row else 'Student'
            order_id = generate_unique_order_id(user_type, conn)
            total_amount = sum(float(i['price']) * int(i['quantity']) for i in cart)
            cur.execute("""
                INSERT INTO orders (order_id, user_id, items, total_amount, status, payment_method, payment_status, transaction_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING order_id
            """, (order_id, user_id, Json(cart), total_amount, 'Cancelled', 'Razorpay', 'Failed', razorpay_payment_id or 'TXN_FAILED'))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': data.get('error_message') or 'Payment failed at gateway',
                'orderId': row[0] if row else order_id,
                'payment_status': 'Failed'
            }), 200
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.close()
            return jsonify({'success': False, 'message': str(e)}), 500

    if not razorpay_payment_id:
        return jsonify({'success': False, 'message': 'Payment ID required'}), 400

    is_live_key = (
        RAZORPAY_KEY_ID and
        RAZORPAY_KEY_SECRET and
        not RAZORPAY_KEY_ID.startswith('rzp_test_your') and
        len(RAZORPAY_KEY_ID) > 10
    )

    if is_live_key and razorpay_signature:
        expected_sig = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, razorpay_signature):
            return jsonify({'success': False, 'message': 'Invalid payment signature'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT user_type FROM users WHERE id = %s', (user_id,))
        user_row = cur.fetchone()
        user_type = user_row[0] if user_row else 'Student'

        order_id = generate_unique_order_id(user_type, conn)
        total_amount = sum(float(i['price']) * int(i['quantity']) for i in cart)

        cur.execute("""
            INSERT INTO orders (order_id, user_id, items, total_amount, status, payment_method, payment_status, transaction_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING order_id
        """, (order_id, user_id, Json(cart), total_amount, 'Uncompleted', 'Razorpay', 'Paid', razorpay_payment_id))

        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Payment verified and order placed successfully',
            'orderId': row[0] if row else order_id,
            'amount': total_amount
        })
    except Exception as e:
        print('Payment verify DB error:', e)
        if 'conn' in locals() and conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/orders', methods=['GET'])
def api_get_orders():
    # support query params: user_id, username, order_id, or admin=true
    order_id = request.args.get('order_id')
    user_id = request.args.get('user_id')
    username = request.args.get('username')
    is_admin = request.args.get('admin') in ('1', 'true', 'True')
    
    # Require admin authentication for admin order view
    if is_admin:
        if 'user_id' not in session:
            hdr_uid = request.headers.get('X-User-Id')
            hdr_role = request.headers.get('X-User-Role')
            if hdr_uid and str(hdr_uid).isdigit() and hdr_role == 'admin':
                session['user_id'] = int(hdr_uid)
                session['role'] = 'admin'
            else:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
            
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if is_admin:
            cur.execute('SELECT o.*, u.username FROM orders o LEFT JOIN users u ON o.user_id = u.id ORDER BY created_at DESC')
            rows = cur.fetchall()
        elif order_id:
            cur.execute('SELECT o.*, u.username FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE o.order_id = %s ORDER BY created_at DESC', (order_id,))
            rows = cur.fetchall()
        elif user_id:
            try:
                uid = int(user_id)
            except (ValueError, TypeError):
                cur.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Invalid user_id'}), 400
            cur.execute('SELECT o.* FROM orders o WHERE o.user_id = %s ORDER BY created_at DESC', (uid,))
            rows = cur.fetchall()
        elif username:
            cur.execute('SELECT o.* FROM orders o JOIN users u ON o.user_id = u.id WHERE u.username = %s ORDER BY created_at DESC', (username,))
            rows = cur.fetchall()
        else:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'user_id, username, order_id or admin query param required'}), 400
        cur.close()
        conn.close()
        return jsonify({'success': True, 'orders': rows})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/orders/<order_id>/status', methods=['PATCH'])
@admin_required
def api_update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    if not new_status:
        return jsonify({'success': False, 'message': 'status required'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE order_id = %s RETURNING order_id', (new_status, order_id))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if not row:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        return jsonify({'success': True, 'orderId': row[0]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== MENU MANAGEMENT APIs ====================

@app.route('/api/menu', methods=['GET'])
def api_get_menu():
    """Get all menu items or filter by availability"""
    available_only = request.args.get('available') in ('1', 'true', 'True')
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if available_only:
            cur.execute('SELECT * FROM menu_items WHERE availability = true ORDER BY category, item_name')
        else:
            cur.execute('SELECT * FROM menu_items ORDER BY category, item_name')
        items = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'menu': items})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/recommendations', methods=['GET', 'POST'])
def api_recommendations():
    """
    RAG-powered culinary recommendation endpoint.
    Retrieves complementary menu items for items in cart or a queried item,
    augmented with gastronomic knowledge reasoning and synergy explanations.
    """
    query_items = []
    
    if request.method == 'POST':
        data = request.get_json() or {}
        cart_items = data.get('cart', []) or data.get('cart_items', [])
        single_item = data.get('item') or data.get('item_name')
        if single_item:
            if isinstance(single_item, str):
                query_items.append({'item_name': single_item})
            elif isinstance(single_item, dict):
                query_items.append(single_item)
        for c in cart_items:
            item_name = c.get('item_name') or c.get('name')
            if item_name:
                query_items.append({
                    'id': c.get('id'),
                    'item_name': item_name,
                    'category': c.get('category', '')
                })
    else:
        # GET request: ?item=Tea or ?item_id=1
        item_name = request.args.get('item') or request.args.get('item_name')
        item_id = request.args.get('item_id')
        if item_name:
            query_items.append({'item_name': item_name})
        elif item_id:
            try:
                query_items.append({'id': int(item_id)})
            except ValueError:
                pass

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT id, item_name, price, category, description, availability, image_url FROM menu_items WHERE availability = true')
        menu_items = cur.fetchall()
        cur.close()
        conn.close()
        
        # If query_items has IDs without names, fill from menu_items
        for q in query_items:
            if not q.get('item_name') and q.get('id'):
                for m in menu_items:
                    if m['id'] == q['id']:
                        q['item_name'] = m['item_name']
                        q['category'] = m['category']
                        break

        # Import RAG recommender pipeline
        from rag_recommender import get_rag_recommendations
        recommendations = get_rag_recommendations(query_items, menu_items, limit=3)
        
        return jsonify({
            'success': True,
            'query_items': query_items,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/menu', methods=['POST'])
@admin_required
def api_add_menu_item():
    """Add a new menu item (Admin only)"""
    data = request.get_json() or {}
    item_name = data.get('item_name')
    price = data.get('price')
    category = data.get('category')
    description = data.get('description', '')
    availability = data.get('availability', True)
    image_url = data.get('image_url', '')
    
    if not all([item_name, price, category]):
        return jsonify({'success': False, 'message': 'item_name, price, and category are required'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO menu_items (item_name, price, category, description, availability, image_url) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            RETURNING *
        """, (item_name, price, category, description, availability, image_url))
        new_item = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'item': new_item}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/menu/<int:item_id>', methods=['GET'])
def api_get_menu_item(item_id):
    """Get a specific menu item"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM menu_items WHERE id = %s', (item_id,))
        item = cur.fetchone()
        cur.close()
        conn.close()
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        return jsonify({'success': True, 'item': item})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/menu/<int:item_id>', methods=['PUT'])
@admin_required
def api_update_menu_item(item_id):
    """Update a menu item (Admin only)"""
    data = request.get_json() or {}
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        if 'item_name' in data:
            update_fields.append('item_name = %s')
            values.append(data['item_name'])
        if 'price' in data:
            update_fields.append('price = %s')
            values.append(data['price'])
        if 'category' in data:
            update_fields.append('category = %s')
            values.append(data['category'])
        if 'description' in data:
            update_fields.append('description = %s')
            values.append(data['description'])
        if 'availability' in data:
            update_fields.append('availability = %s')
            values.append(data['availability'])
        if 'image_url' in data:
            update_fields.append('image_url = %s')
            values.append(data['image_url'])
        
        if not update_fields:
            return jsonify({'success': False, 'message': 'No fields to update'}), 400
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        values.append(item_id)
        
        query = f"UPDATE menu_items SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
        cur.execute(query, values)
        updated_item = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if not updated_item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        return jsonify({'success': True, 'item': updated_item})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
@admin_required
def api_delete_menu_item(item_id):
    """Delete a menu item (Admin only)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM menu_items WHERE id = %s RETURNING id', (item_id,))
        deleted = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if not deleted:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        return jsonify({'success': True, 'message': 'Item deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== STATS APIs ====================

@app.route('/api/stats', methods=['GET'])
@admin_required
def api_get_stats():
    """Get statistics for admin dashboard"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total users
        cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'user'")
        total_users = cur.fetchone()['count']
        
        # Total orders
        cur.execute("SELECT COUNT(*) as count FROM orders")
        total_orders = cur.fetchone()['count']
        
        # Total revenue
        cur.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM orders WHERE payment_status = 'Paid'")
        total_revenue = float(cur.fetchone()['revenue'])
        
        # Pending orders
        cur.execute("SELECT COUNT(*) as count FROM orders WHERE status IN ('Pending', 'Uncompleted', 'Preparing')")
        pending_orders = cur.fetchone()['count']
        
        # Available menu items
        cur.execute("SELECT COUNT(*) as count FROM menu_items WHERE availability = true")
        available_items = cur.fetchone()['count']
        
        # Unavailable menu items
        cur.execute("SELECT COUNT(*) as count FROM menu_items WHERE availability = false")
        unavailable_items = cur.fetchone()['count']
        
        # Orders today
        cur.execute("SELECT COUNT(*) as count FROM orders WHERE DATE(created_at) = CURRENT_DATE")
        orders_today = cur.fetchone()['count']
        
        # Revenue today
        cur.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM orders WHERE DATE(created_at) = CURRENT_DATE AND payment_status = 'Paid'")
        revenue_today = float(cur.fetchone()['revenue'])
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'totalUsers': total_users,
                'totalOrders': total_orders,
                'totalRevenue': total_revenue,
                'pendingOrders': pending_orders,
                'availableItems': available_items,
                'unavailableItems': unavailable_items,
                'ordersToday': orders_today,
                'revenueToday': revenue_today
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)

