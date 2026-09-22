# Smart Canteen - Complete Web Stack Application

A full-stack web application for canteen management with Flask backend and PostgreSQL database.

## 🚀 Features

### User Features
- 📝 User registration and authentication
- 🍔 Browse menu items by category
- 🛒 Shopping cart with quantity management
- 💳 Multiple payment methods (UPI, Card, Cash, Wallet)
- 📊 Order history and tracking
- 🔔 Real-time order status updates

### Admin Features
- 📈 Dashboard with statistics and analytics
- 🍕 Complete menu management (Add, Edit, Delete, Toggle availability)
- 📦 Order management and status updates
- 👥 User management
- 💰 Revenue tracking

## 🏗️ Technology Stack

### Frontend
- HTML5, CSS3, JavaScript (ES6+)
- Responsive design (mobile-friendly)
- LocalStorage for cart management
- Fetch API for backend communication

### Backend
- **Flask** - Python web framework
- **PostgreSQL** - Relational database
- **Flask-CORS** - Cross-origin resource sharing
- **psycopg2** - PostgreSQL adapter
- **Gunicorn** - Production WSGI server

### Database
- PostgreSQL 12+
- Three main tables: users, menu_items, orders
- JSONB for flexible order item storage
- Indexes for optimized queries

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

## ⚡ Quick Start

### Automated Setup (Recommended)

**Windows:**
```bash
setup.bat
```

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

1. **Install PostgreSQL and create database:**
   ```bash
   psql -U postgres
   CREATE DATABASE canteen;
   \q
   ```

2. **Initialize database tables:**
   ```bash
   cd backend
   psql -U postgres -d canteen -f init_db.sql
   ```

3. **Setup Python environment:**
   ```bash
   cd backend
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set your DB_PASSWORD
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the application:**
   - Main page: http://localhost:5000
   - Login: http://localhost:5000/login.html
   - Admin: http://localhost:5000/admin.html

## 🔑 Default Accounts

### Admin Account
- Username: `admin`
- Password: `admin123`
- Access: Full admin panel with menu and order management

### User Account
- Username: `user`
- Password: `user123`
- Access: User dashboard and ordering

## 📁 Project Structure

```
smart_canteen/
├── backend/
│   ├── app.py                 # Flask application
│   ├── requirements.txt       # Python dependencies
│   ├── init_db.sql           # Database initialization
│   ├── .env.example          # Environment template
│   └── README.md             # Backend documentation
├── index.html                # Landing page
├── login.html                # Login page
├── register.html             # Registration page
├── admin.html                # Admin dashboard
├── user_dashboard.html       # User dashboard
├── user_orders.html          # User order history
├── payment.html              # Payment page
├── order_confirmation.html   # Order confirmation
├── app.js                    # Frontend JavaScript
├── styles.css                # CSS styles
├── setup.bat                 # Windows setup script
├── setup.sh                  # Mac/Linux setup script
├── SETUP.md                  # Detailed setup guide
├── API_REFERENCE.md          # API documentation
├── TESTING.md                # Testing guide
└── README.md                 # This file
```

## 🔌 API Endpoints

### User Management
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - User login

### Menu Management
- `GET /api/menu` - Get all menu items
- `POST /api/menu` - Add menu item (Admin)
- `PUT /api/menu/<id>` - Update menu item (Admin)
- `DELETE /api/menu/<id>` - Delete menu item (Admin)

### Order Management
- `POST /api/checkout` - Place order
- `GET /api/orders` - Get orders (with filters)
- `PATCH /api/orders/<order_id>/status` - Update status (Admin)

### Statistics
- `GET /api/stats` - Get dashboard statistics (Admin)

See [API_REFERENCE.md](API_REFERENCE.md) for complete documentation.

## 🗄️ Database Schema

### Users Table
- User authentication and role management
- Fields: id, username, email, password, role, created_at

### Menu Items Table
- Menu item details and availability
- Fields: id, item_name, price, category, description, availability, image_url, created_at, updated_at

### Orders Table
- Order tracking and management
- Fields: id, order_id, user_id, items (JSONB), total_amount, status, payment_method, payment_status, transaction_id, created_at, updated_at

## 🧪 Testing

See [TESTING.md](TESTING.md) for comprehensive testing guide.

Quick test:
```bash
# Test API health
curl http://localhost:5000/api/health

# Test menu endpoint
curl http://localhost:5000/api/menu

# Test login
curl -X POST http://localhost:5000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 🚀 Production Deployment

1. **Security:**
   - Implement password hashing (bcrypt/argon2)
   - Use environment variables for secrets
   - Enable HTTPS/SSL
   - Update CORS settings
   - Add rate limiting

2. **Run with Gunicorn:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Database:**
   - Use connection pooling
   - Enable regular backups
   - Optimize indexes

## 📚 Documentation

- [SETUP.md](SETUP.md) - Detailed installation guide
- [API_REFERENCE.md](API_REFERENCE.md) - Complete API documentation
- [TESTING.md](TESTING.md) - Testing procedures
- [backend/README.md](backend/README.md) - Backend documentation

## 🐛 Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `pg_ctl status`
- Check credentials in .env file
- Ensure database exists: `psql -U postgres -l`

### Port 5000 Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9
```

### Module Not Found
- Activate virtual environment
- Run: `pip install -r requirements.txt`

## 🎨 Font

This project uses a custom font named Aleoverasans. To apply the font:
1. Place `Aleoverasans.woff2` file in `fonts/` folder
2. The site will fall back to system fonts if not available

## 📄 License

This project is for educational purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 👨‍💻 Author

Smart Canteen - Digital Dining Solution

## 📞 Support

For issues and questions:
1. Check the documentation files
2. Review the TESTING.md guide
3. Examine database and application logs
4. Check browser console for frontend errors

---

**Version:** 2.0.0  
**Last Updated:** February 2, 2026  
**Status:** Production Ready ✅

