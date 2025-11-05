# Smart Canteen - Digital Food Ordering System

A complete digital-first, cashless canteen management system built with Flask, SQLite/PostgreSQL, and professional frontend using HTML/CSS/JavaScript. The application supports two distinct user roles with comprehensive functionality for both administrators and users (students/staff).

## Features

### User Features (Students/Staff)
- **Secure Authentication**: Registration and login with bcrypt password hashing
- **Menu Browsing**: View daily menu with categories, prices, and availability
- **Shopping Cart**: Add items to cart with quantity management
- **Order Placement**: Place pre-orders with mock UPI payment integration
- **Order Tracking**: Real-time order status updates (Pending → Preparing → Ready → Completed)
- **Order History**: View past orders with detailed receipts and transaction IDs

### Admin Features
- **Dashboard**: Overview with key statistics and recent orders
- **Menu Management**: Full CRUD operations for menu items with categories
- **Order Management**: View all orders, update statuses, and filter by status
- **Analytics**: Interactive charts showing revenue trends, popular items, and order statistics
- **User Management**: View registered users and order patterns

### Technical Features
- **Role-based Access Control**: Separate interfaces and permissions for admin/user roles
- **Session Management**: Secure session handling with automatic logout
- **Responsive Design**: Professional UI that works on desktop and mobile
- **Real-time Updates**: Auto-refresh functionality for order status
- **Error Handling**: Comprehensive error pages and flash messaging
- **Database Flexibility**: Supports both SQLite (development) and PostgreSQL (production)

## Technology Stack

- **Backend**: Flask 2.0+, SQLAlchemy, Werkzeug
- **Database**: SQLite (default) / PostgreSQL
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js for analytics visualization
- **Security**: bcrypt password hashing, session management

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Quick Start (SQLite - No Database Setup Required)

1. **Clone/Download the project** and navigate to the directory:
   ```powershell
   cd smart_canteen
   ```

2. **Create a virtual environment**:
   ```powershell
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   ```powershell
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   
   # Windows Command Prompt
   .venv\Scripts\activate.bat
   
   # Linux/Mac
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```powershell
   python app.py
   ```

6. **Open your browser** and go to: `http://127.0.0.1:5000`

### Default Credentials

The application comes with pre-configured accounts:

**Admin Account:**
- Username: `admin`
- Password: `admin123`

**Test User Account:**
- Username: `student1`
- Password: `password123`

### PostgreSQL Setup (Current Configuration)

The application is currently configured to use PostgreSQL:

1. **Database**: `soipro`
2. **User**: `postgres`
3. **Connection**: `postgresql://postgres:Kavin04@localhost:5432/soipro`

To change the database configuration:

1. **Update config.py** or set environment variable:
   ```powershell
   # Windows
   $env:DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
   ```

3. **Update requirements** if needed:
   ```powershell
   pip install psycopg2-binary
   ```

## Usage Guide

### For Students/Staff Users:

1. **Register**: Create an account with username, email, and password
2. **Browse Menu**: View available items, filter by categories
3. **Add to Cart**: Click "Add to Cart" on desired items
4. **Place Order**: Review cart and proceed to mock payment
5. **Track Orders**: Monitor order status in "My Orders" section

### For Administrators:

1. **Login**: Use admin credentials to access admin panel
2. **Manage Menu**: Add, edit, or remove menu items with pricing
3. **Process Orders**: Update order statuses as food is prepared
4. **View Analytics**: Monitor revenue, popular items, and order trends
5. **Monitor System**: Track user registrations and system usage

## Sample Data

The application automatically creates sample data on first run:
- 8 sample menu items across different categories
- Admin and test user accounts
- Categories: Main Course, Snacks, Beverages

## Project Structure

```
smart_canteen/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── smart_canteen.db     # SQLite database (auto-created)
├── templates/           # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── user_dashboard.html
│   ├── user_orders.html
│   ├── cart.html
│   ├── payment.html
│   ├── admin_dashboard.html
│   ├── admin_menu.html
│   ├── admin_orders.html
│   ├── admin_analytics.html
│   ├── 404.html
│   └── 500.html
└── static/              # Static assets
    ├── css/
    │   └── style.css    # Main stylesheet
    └── js/
        └── cart.js      # Cart functionality
```

## Configuration

### Environment Variables

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Flask secret key for sessions (change in production)

### Development vs Production

The `config.py` file contains settings that should be adjusted for production:
- Set a secure `SECRET_KEY`
- Use PostgreSQL instead of SQLite
- Enable HTTPS and secure cookies
- Add rate limiting and additional security measures

## API Endpoints

The application includes several API endpoints for AJAX operations:

- `GET /api/menu_items` - Fetch available menu items
- `GET /api/order_status/<id>` - Get order status
- `POST /user/place_order` - Place new order
- `POST /payment` - Mock payment processing

## Security Features

- **Password Hashing**: All passwords are hashed using Werkzeug's bcrypt
- **Session Management**: Secure session handling with timeout
- **CSRF Protection**: Built-in Flask session security
- **Input Validation**: Server-side validation for all forms
- **SQL Injection Prevention**: SQLAlchemy ORM prevents SQL injection
- **Role-based Access**: Decorator-based route protection

## Development Notes

### Mock Payment System
The current payment system is a simulation for testing purposes. For production:
1. Replace the `/payment` route with real payment gateway integration
2. Update the `payment.html` template with actual payment forms
3. Add proper payment status handling and webhooks

### Real-time Updates
Currently uses auto-refresh (30-second intervals). For better real-time experience:
1. Implement WebSocket connections
2. Add push notifications
3. Use Server-Sent Events (SSE) for live order updates

### Performance Optimization
For high-traffic deployment:
1. Add database indexing
2. Implement caching (Redis)
3. Use a production WSGI server (Gunicorn)
4. Add load balancing
5. Optimize database queries with pagination

## Troubleshooting

### Common Issues:

1. **Database Connection Error**: Ensure SQLite permissions or PostgreSQL is running
2. **Import Errors**: Check virtual environment activation and dependencies
3. **Port Already in Use**: Change port in `app.py` or kill existing process
4. **Template Not Found**: Verify template files are in correct directory structure

### Logs and Debugging:
- Flask debug mode is enabled by default
- Check terminal output for detailed error messages
- Use browser developer tools for frontend issues

## Future Enhancements

- **Mobile App**: React Native or Flutter mobile application
- **Payment Integration**: Razorpay, Stripe, or other payment gateways
- **Email Notifications**: Order confirmation and status updates
- **Inventory Management**: Stock tracking and low-stock alerts
- **Multi-location Support**: Support for multiple canteen branches
- **Advanced Analytics**: More detailed reporting and insights
- **QR Code Ordering**: QR code-based table ordering
- **Loyalty Program**: Points and rewards system

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Note**: This is a educational/demonstration project. For production deployment, ensure proper security auditing, performance testing, and compliance with local regulations.

