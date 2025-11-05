"""
Smart Canteen - Main Flask Application
A digital canteen management system with user and admin roles
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from models import db, User, MenuItem, Order, OrderItem
from config import Config
from functools import wraps
from datetime import datetime
from sqlalchemy import func, desc, or_
import secrets
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

def generate_order_id():
    """Generate unique order ID"""
    import random
    import string
    while True:
        order_id = 'ORD-' + ''.join(random.choices(string.digits, k=6))
        if not Order.query.filter_by(order_id=order_id).first():
            return order_id


def generate_order_bill_pdf(order):
    """Generate PDF bill for an order"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("KGiSL Institute of Technology", title_style))
    story.append(Paragraph("Smart Canteen - Order Bill", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Order details
    order_info = [
        ['Order ID:', order.order_id],
        ['Customer:', order.customer.username],
        ['Date:', order.timestamp.strftime('%B %d, %Y at %I:%M %p')],
        ['Transaction ID:', order.transaction_id],
        ['Payment Method:', order.payment_method],
        ['Status:', order.status]
    ]
    
    order_table = Table(order_info, colWidths=[2*inch, 3*inch])
    order_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(order_table)
    story.append(Spacer(1, 20))
    
    # Items table
    story.append(Paragraph("Order Items:", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    items_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
    for item in order.order_items:
        items_data.append([
            item.menu_item.item_name,
            str(item.quantity),
            f'₹{item.unit_price:.2f}',
            f'₹{item.total_price:.2f}'
        ])
    
    # Add total row
    items_data.append(['', '', 'Total Amount:', f'₹{order.total_amount:.2f}'])
    
    items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(items_table)
    story.append(Spacer(1, 30))
    
    # Footer
    footer_text = "Thank you for using Smart Canteen! Please show this bill when collecting your order."
    story.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Create tables and seed initial data
with app.app_context():
    # Drop existing tables if they exist (for schema update)
    # Comment this out after first run to preserve data
    # db.drop_all()
    
    db.create_all()
    
    # Create default admin if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@canteen.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        print("Default admin created: username=admin, password=admin123")
    
    # Add sample menu items if none exist
    if MenuItem.query.count() == 0:
        sample_items = [
            MenuItem(item_name='Chicken Burger', description='Grilled chicken patty with lettuce and tomato', 
                    price=120.00, category='Main Course', availability=True),
            MenuItem(item_name='Vegetable Sandwich', description='Fresh vegetables with mayo', 
                    price=80.00, category='Snacks', availability=True),
            MenuItem(item_name='Coffee', description='Hot brewed coffee', 
                    price=30.00, category='Beverages', availability=True),
            MenuItem(item_name='Tea', description='Indian masala tea', 
                    price=20.00, category='Beverages', availability=True),
            MenuItem(item_name='Pasta', description='Italian style pasta with tomato sauce', 
                    price=150.00, category='Main Course', availability=True),
            MenuItem(item_name='French Fries', description='Crispy golden fries', 
                    price=60.00, category='Snacks', availability=True),
            MenuItem(item_name='Fruit Juice', description='Fresh mixed fruit juice', 
                    price=40.00, category='Beverages', availability=True),
            MenuItem(item_name='Biryani', description='Aromatic basmati rice with spices', 
                    price=180.00, category='Main Course', availability=True)
        ]
        
        for item in sample_items:
            db.session.add(item)
        
        print("Sample menu items added")
    
    # Create sample user if none exist (for testing)
    if User.query.filter_by(role='user').count() == 0:
        test_user = User(username='student1', email='student1@college.edu', role='user')
        test_user.set_password('password123')
        db.session.add(test_user)
        print("Sample user created: username=student1, password=password123")
    
    db.session.commit()


# Authentication decorators
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Access denied. Admin privileges required', 'danger')
            return redirect(url_for('user_dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


# Routes

@app.route('/')
def index():
    """Landing page"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(username=username, email=email, role='user')
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session.permanent = True
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))


@app.route('/user/dashboard')
@login_required
def user_dashboard():
    """User dashboard - view menu and place orders"""
    user = User.query.get(session['user_id'])
    
    if user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    # Get available menu items
    category_filter = request.args.get('category', None)
    
    if category_filter:
        menu_items = MenuItem.query.filter_by(availability=True, category=category_filter).all()
    else:
        menu_items = MenuItem.query.filter_by(availability=True).all()
    
    # Get categories for filter
    categories = db.session.query(MenuItem.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('user_dashboard.html', 
                         user=user, 
                         menu_items=menu_items,
                         categories=categories,
                         selected_category=category_filter)


@app.route('/user/cart')
@login_required
def view_cart():
    """View shopping cart"""
    user = User.query.get(session['user_id'])
    return render_template('cart.html', user=user)


@app.route('/user/orders')
@login_required
def user_orders():
    """View user's order history"""
    user = User.query.get(session['user_id'])
    
    orders = Order.query.filter_by(user_id=user.id).order_by(desc(Order.timestamp)).all()
    
    return render_template('user_orders.html', user=user, orders=orders)


@app.route('/user/orders/bill/<int:order_id>')
@login_required
def download_user_bill(order_id):
    """Download user's order bill (only if Ready or Completed)"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Security check: user can only download their own bills
        if order.user_id != session['user_id']:
            flash('Access denied', 'danger')
            return redirect(url_for('user_orders'))
        
        # Only allow download if order is Ready or Completed
        if order.status not in ['Ready', 'Completed']:
            flash('Bill not available yet. Order must be ready first.', 'warning')
            return redirect(url_for('user_orders'))
        
        pdf_buffer = generate_order_bill_pdf(order)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'bill_{order.order_id}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash('Failed to generate bill', 'danger')
        return redirect(url_for('user_orders'))


@app.route('/user/place_order', methods=['POST'])
@login_required
def place_order():
    """Place a new order with multiple items"""
    try:
        data = request.get_json()
        cart_items = data.get('cart_items', [])
        
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        user_id = session['user_id']
        order_id = generate_order_id()
        transaction_id = f'TXN{secrets.token_hex(8).upper()}'
        
        # Calculate total amount
        total_amount = 0
        order_items_data = []
        
        for item in cart_items:
            menu_item = MenuItem.query.get(item['id'])
            
            if not menu_item or not menu_item.availability:
                return jsonify({'success': False, 'message': f'Item {item["name"]} is not available'}), 400
            
            item_total = menu_item.price * item['quantity']
            total_amount += item_total
            
            order_items_data.append({
                'menu_item': menu_item,
                'quantity': item['quantity'],
                'unit_price': menu_item.price,
                'total_price': item_total
            })
        
        # Create the main order
        new_order = Order(
            order_id=order_id,
            user_id=user_id,
            total_amount=total_amount,
            status='Uncompleted',
            payment_method='UPI',
            payment_status='Paid',
            transaction_id=transaction_id
        )
        
        db.session.add(new_order)
        db.session.flush()  # Get the order ID
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=new_order.id,
                item_id=item_data['menu_item'].id,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Order placed successfully!',
            'order_id': order_id,
            'transaction_id': transaction_id,
            'total_amount': total_amount
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to place order'}), 500


@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    """Mock payment page"""
    if request.method == 'POST':
        # Simulate payment processing
        return jsonify({'success': True, 'transaction_id': f'TXN{secrets.token_hex(8).upper()}'})
    
    return render_template('payment.html')


# Admin Routes

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard - overview"""
    # Get statistics
    total_users = User.query.filter_by(role='user').count()
    total_menu_items = MenuItem.query.count()
    available_menu_items = MenuItem.query.filter_by(availability=True).count()
    unavailable_menu_items = MenuItem.query.filter_by(availability=False).count()
    total_orders = Order.query.count()
    
    # Revenue calculation
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    
    # Recent orders
    recent_orders = Order.query.order_by(desc(Order.timestamp)).limit(10).all()
    
    # Uncompleted orders count
    uncompleted_orders = Order.query.filter_by(status='Uncompleted').count()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_menu_items=total_menu_items,
                         available_menu_items=available_menu_items,
                         unavailable_menu_items=unavailable_menu_items,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders,
                         uncompleted_orders=uncompleted_orders)


@app.route('/admin/menu', methods=['GET'])
@admin_required
def admin_menu():
    """Admin menu management page"""
    menu_items = MenuItem.query.order_by(MenuItem.category, MenuItem.item_name).all()
    return render_template('admin_menu.html', menu_items=menu_items)


@app.route('/admin/menu/add', methods=['POST'])
@admin_required
def add_menu_item():
    """Add new menu item"""
    try:
        item_name = request.form.get('item_name', '').strip()
        description = request.form.get('description', '').strip()
        price = float(request.form.get('price', 0))
        category = request.form.get('category', '').strip()
        availability = request.form.get('availability') == 'on'
        
        if not item_name or price <= 0:
            flash('Item name and valid price are required', 'danger')
            return redirect(url_for('admin_menu'))
        
        new_item = MenuItem(
            item_name=item_name,
            description=description,
            price=price,
            category=category,
            availability=availability
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        flash(f'Menu item "{item_name}" added successfully', 'success')
        return redirect(url_for('admin_menu'))
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to add menu item', 'danger')
        return redirect(url_for('admin_menu'))


@app.route('/admin/menu/edit/<int:item_id>', methods=['POST'])
@admin_required
def edit_menu_item(item_id):
    """Edit existing menu item"""
    try:
        item = MenuItem.query.get_or_404(item_id)
        
        item.item_name = request.form.get('item_name', '').strip()
        item.description = request.form.get('description', '').strip()
        item.price = float(request.form.get('price', 0))
        item.category = request.form.get('category', '').strip()
        item.availability = request.form.get('availability') == 'on'
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Menu item "{item.item_name}" updated successfully', 'success')
        return redirect(url_for('admin_menu'))
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to update menu item', 'danger')
        return redirect(url_for('admin_menu'))


@app.route('/admin/menu/toggle_availability/<int:item_id>', methods=['POST'])
@admin_required
def toggle_menu_availability(item_id):
    """Toggle menu item availability"""
    try:
        item = MenuItem.query.get_or_404(item_id)
        item.availability = not item.availability
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        status = "available" if item.availability else "unavailable"
        flash(f'Menu item "{item.item_name}" is now {status}', 'success')
        return redirect(url_for('admin_menu'))
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to update menu item availability', 'danger')
        return redirect(url_for('admin_menu'))


@app.route('/admin/menu/delete/<int:item_id>', methods=['POST'])
@admin_required
def delete_menu_item(item_id):
    """Delete menu item"""
    try:
        item = MenuItem.query.get_or_404(item_id)
        item_name = item.item_name
        
        db.session.delete(item)
        db.session.commit()
        
        flash(f'Menu item "{item_name}" deleted successfully', 'success')
        return redirect(url_for('admin_menu'))
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete menu item', 'danger')
        return redirect(url_for('admin_menu'))


@app.route('/admin/orders')
@admin_required
def admin_orders():
    """View all orders with search and filter"""
    status_filter = request.args.get('status', None)
    search_query = request.args.get('search', '').strip()
    
    query = Order.query
    
    # Apply search filter
    if search_query:
        query = query.filter(
            or_(
                Order.order_id.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%')
            )
        ).join(User)
    
    # Apply status filter
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders = query.order_by(desc(Order.timestamp)).all()
    
    return render_template('admin_orders.html', 
                         orders=orders, 
                         status_filter=status_filter,
                         search_query=search_query)


@app.route('/admin/orders/update/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Update order status and auto-send bill when Ready"""
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        
        if new_status in ['Uncompleted', 'Ready', 'Completed']:
            old_status = order.status
            order.status = new_status
            
            if new_status == 'Ready':
                order.ready_at = datetime.utcnow()
                # Auto-generate bill when order is marked as Ready
                try:
                    pdf_buffer = generate_order_bill_pdf(order)
                    # In a real application, you would send this via email or notification
                    # For now, we'll create a session flag to show the bill download link
                    session[f'bill_ready_{order_id}'] = True
                    flash(f'Order {order.order_id} is Ready! Bill has been generated automatically.', 'success')
                except Exception as pdf_error:
                    flash(f'Order {order.order_id} status updated to {new_status}, but bill generation failed.', 'warning')
            elif new_status == 'Completed':
                order.completed_at = datetime.utcnow()
                flash(f'Order {order.order_id} status updated to {new_status}', 'success')
            else:
                flash(f'Order {order.order_id} status updated to {new_status}', 'success')
            
            db.session.commit()
        else:
            flash('Invalid status', 'danger')
        
        return redirect(url_for('admin_orders'))
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to update order status', 'danger')
        return redirect(url_for('admin_orders'))


@app.route('/admin/orders/bill/<int:order_id>')
@admin_required
def download_order_bill(order_id):
    """Generate and download order bill PDF"""
    try:
        order = Order.query.get_or_404(order_id)
        
        pdf_buffer = generate_order_bill_pdf(order)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'bill_{order.order_id}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash('Failed to generate bill', 'danger')
        return redirect(url_for('admin_orders'))


@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Analytics dashboard with charts"""
    # Revenue by date (last 30 days)
    from sqlalchemy import func, cast, Date
    
    revenue_by_date = db.session.query(
        cast(Order.timestamp, Date).label('date'),
        func.sum(Order.total_amount).label('revenue')
    ).group_by('date').order_by('date').limit(30).all()
    
    # Most ordered items
    most_ordered = db.session.query(
        MenuItem.item_name,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(OrderItem).group_by(MenuItem.item_name).order_by(desc('total_quantity')).limit(10).all()
    
    # Orders by status
    orders_by_status = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status).all()
    # Prepare JSON-serializable lists for the frontend
    revenue_labels = [r.date.strftime('%Y-%m-%d') for r in revenue_by_date]
    revenue_values = [float(r.revenue) for r in revenue_by_date]

    most_ordered_labels = [m[0] for m in most_ordered]
    most_ordered_values = [int(m[1]) for m in most_ordered]

    status_labels = [s[0] for s in orders_by_status]
    status_values = [int(s[1]) for s in orders_by_status]

    return render_template('admin_analytics.html',
                         revenue_labels=revenue_labels,
                         revenue_values=revenue_values,
                         most_ordered_labels=most_ordered_labels,
                         most_ordered_values=most_ordered_values,
                         status_labels=status_labels,
                         status_values=status_values)


# API Endpoints for AJAX

@app.route('/api/order_status/<int:order_id>')
@login_required
def get_order_status(order_id):
    """Get order status via API"""
    order = Order.query.get_or_404(order_id)
    
    # Check if user owns this order or is admin
    if order.user_id != session['user_id'] and session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'id': order.id,
        'status': order.status,
        'timestamp': order.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/menu_items')
def get_menu_items():
    """Get all available menu items via API"""
    items = MenuItem.query.filter_by(availability=True).all()
    
    return jsonify([{
        'id': item.id,
        'item_name': item.item_name,
        'description': item.description,
        'price': item.price,
        'category': item.category
    } for item in items])


@app.route('/api/user/<int:user_id>/recent_orders')
@login_required
def get_user_recent_orders(user_id):
    """Get user's recent orders for notification checking"""
    # Security check: users can only access their own orders, admins can access any
    if session['user_id'] != user_id and session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get orders from last 24 hours
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    recent_orders = Order.query.filter(
        Order.user_id == user_id,
        Order.timestamp >= yesterday,
        Order.status.in_(['Uncompleted', 'Ready'])  # Only active orders
    ).order_by(desc(Order.timestamp)).limit(10).all()
    
    return jsonify([{
        'id': order.id,
        'order_id': order.order_id,
        'status': order.status,
        'total_amount': order.total_amount,
        'timestamp': order.timestamp.isoformat(),
        'items_count': len(order.order_items)
    } for order in recent_orders])


# Error handlers

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
