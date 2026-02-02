from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import send_from_directory
import json
import uuid
from psycopg2.extras import Json

app = Flask(__name__)
CORS(app)

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'canteen')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Kavin04')
DB_PORT = os.environ.get('DB_PORT', '5432')

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
    return conn


def init_db():
    """Create users, menu_items, and orders tables if they don't exist."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Drop existing tables to recreate with correct schema
        cur.execute("DROP TABLE IF EXISTS orders CASCADE")
        cur.execute("DROP TABLE IF EXISTS menu_items CASCADE")
        cur.execute("DROP TABLE IF EXISTS users CASCADE")
        
        # Create users table
        cur.execute("""
            CREATE TABLE users (
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
            CREATE TABLE menu_items (
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
        CREATE TABLE orders (
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
        
        # Insert demo users if they don't exist
        cur.execute("""
        INSERT INTO users (username, email, password, role) 
        VALUES ('admin', 'admin@canteen.com', 'admin123', 'admin')
        ON CONFLICT (username) DO NOTHING
        """)
        
        cur.execute("""
        INSERT INTO users (username, email, password, role) 
        VALUES ('user', 'user@canteen.com', 'user123', 'user')
        ON CONFLICT (username) DO NOTHING
        """)
        
        # Insert demo menu items if table is empty
        cur.execute("SELECT COUNT(*) FROM menu_items")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("""
            INSERT INTO menu_items (item_name, price, category, description, availability) VALUES
            ('Chicken Burger', 120.00, 'Main Course', 'Juicy chicken burger with fresh vegetables', true),
            ('Vegetable Sandwich', 80.00, 'Snacks', 'Healthy vegetable sandwich with multigrain bread', true),
            ('Coffee', 30.00, 'Beverages', 'Hot brewed coffee', true),
            ('Tea', 25.00, 'Beverages', 'Hot masala tea', true),
            ('Pasta', 150.00, 'Main Course', 'Italian pasta with white sauce', true),
            ('French Fries', 60.00, 'Snacks', 'Crispy golden french fries', true),
            ('Fresh Juice', 40.00, 'Beverages', 'Fresh fruit juice', true),
            ('Pizza Slice', 100.00, 'Main Course', 'Cheesy pizza slice', true),
            ('Samosa', 20.00, 'Snacks', 'Crispy vegetable samosa (2 pieces)', true),
            ('Ice Cream', 50.00, 'Desserts', 'Vanilla ice cream cup', true)
            """)
        
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
    # Serve other frontend static files (css, js, html)
    file_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(FRONTEND_DIR, filename)
    return jsonify({'message': 'Not Found'}), 404

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


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
        cur.execute('INSERT INTO users (username, email, password, user_type) VALUES (%s,%s,%s,%s) RETURNING id, username, email, role, user_type', (username, email, password, user_type))
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
        cur.execute('SELECT id, username, email, role, user_type FROM users WHERE username=%s AND password=%s', (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        return jsonify({'success': True, 'user': user})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users', methods=['GET'])
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

    # Basic server-side validation for cart items
    for item in cart:
        if not all(k in item for k in ('id', 'name', 'price', 'quantity')):
            return jsonify({'success': False, 'message': 'Invalid cart item format'}), 400
    try:
        total_amount = sum(float(i['price']) * int(i['quantity']) for i in cart)
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid price/quantity in cart'}), 400

    # Create order record
    order_id = 'ORD-' + uuid.uuid4().hex[:10].upper()
    transaction_id = 'TXN' + uuid.uuid4().hex[:10].upper()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO orders (order_id, user_id, items, total_amount, status, payment_method, payment_status, transaction_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING order_id",
                    (order_id, user_id, Json(cart), total_amount, 'Uncompleted', payment_method, 'Paid', transaction_id))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Payment processed', 'orderId': row[0] if row else order_id, 'amount': total_amount})
    except Exception as e:
        print('DB error:', e)
        # fallback: return demo response
        return jsonify({'success': True, 'message': 'Payment processed (demo)', 'orderId': order_id, 'amount': total_amount})


@app.route('/api/orders', methods=['GET'])
def api_get_orders():
    # support query params: user_id or username or admin=true
    user_id = request.args.get('user_id')
    username = request.args.get('username')
    is_admin = request.args.get('admin') in ('1', 'true', 'True')
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if is_admin:
            cur.execute('SELECT o.*, u.username FROM orders o LEFT JOIN users u ON o.user_id = u.id ORDER BY created_at DESC')
            rows = cur.fetchall()
        elif user_id:
            cur.execute('SELECT o.* FROM orders o WHERE o.user_id = %s ORDER BY created_at DESC', (int(user_id),))
            rows = cur.fetchall()
        elif username:
            cur.execute('SELECT o.* FROM orders o JOIN users u ON o.user_id = u.id WHERE u.username = %s ORDER BY created_at DESC', (username,))
            rows = cur.fetchall()
        else:
            return jsonify({'success': False, 'message': 'user_id, username or admin query param required'}), 400
        cur.close()
        conn.close()
        return jsonify({'success': True, 'orders': rows})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/orders/<order_id>/status', methods=['PATCH'])
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


@app.route('/api/menu', methods=['POST'])
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
