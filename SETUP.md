# Smart Canteen - Setup Guide

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Node.js (optional, for additional tooling)

## Installation Steps

### 1. Database Setup

#### Install PostgreSQL
- Windows: Download from https://www.postgresql.org/download/windows/
- Mac: `brew install postgresql`
- Linux: `sudo apt-get install postgresql postgresql-contrib`

#### Create Database
```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE canteen;

# Exit psql
\q
```

#### Initialize Database Tables
```bash
# Navigate to backend folder
cd backend

# Run the initialization script
psql -U postgres -d canteen -f init_db.sql
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and update the values:
# - DB_PASSWORD: Your PostgreSQL password
# - DB_USER: Your PostgreSQL username (default: postgres)
# - DB_NAME: Database name (default: canteen)
# - DB_HOST: Database host (default: localhost)
# - DB_PORT: Database port (default: 5432)
```

### 3. Run the Application

#### Start Backend Server
```bash
cd backend
python app.py
```

The Flask backend will start on `http://localhost:5000`

#### Access the Application
Open your web browser and navigate to:
- Main page: `http://localhost:5000`
- Login page: `http://localhost:5000/login.html`
- Admin panel: `http://localhost:5000/admin.html`

## Default User Accounts

### Admin Account
- Username: `admin`
- Password: `admin123`
- Access: Full admin panel access

### Regular User Account
- Username: `user`
- Password: `user123`
- Access: User dashboard and ordering

## API Endpoints

### User Management
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - User login

### Menu Management
- `GET /api/menu` - Get all menu items
- `POST /api/menu` - Add new menu item (Admin)
- `GET /api/menu/<id>` - Get specific menu item
- `PUT /api/menu/<id>` - Update menu item (Admin)
- `DELETE /api/menu/<id>` - Delete menu item (Admin)

### Order Management
- `POST /api/checkout` - Place new order
- `GET /api/orders` - Get orders (with filters)
- `PATCH /api/orders/<order_id>/status` - Update order status (Admin)

### Statistics
- `GET /api/stats` - Get admin dashboard statistics

## Project Structure

```
smart_canteen/
├── backend/
│   ├── app.py              # Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── init_db.sql        # Database initialization script
│   ├── .env.example       # Environment variables template
│   └── README.md          # Backend documentation
├── index.html             # Main landing page
├── login.html             # Login page
├── register.html          # Registration page
├── admin.html             # Admin dashboard
├── user_dashboard.html    # User dashboard
├── user_orders.html       # User orders page
├── payment.html           # Payment page
├── order_confirmation.html # Order confirmation
├── app.js                 # Frontend JavaScript
├── styles.css             # CSS styles
└── README.md             # This file
```

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `password` - User password (store hashed in production!)
- `role` - User role (user/admin)
- `created_at` - Account creation timestamp

### Menu Items Table
- `id` - Primary key
- `item_name` - Item name
- `price` - Item price
- `category` - Item category
- `description` - Item description
- `availability` - Item availability status
- `image_url` - Item image URL
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Orders Table
- `id` - Primary key
- `order_id` - Unique order identifier
- `user_id` - Foreign key to users
- `items` - Order items (JSON)
- `total_amount` - Total order amount
- `status` - Order status
- `payment_method` - Payment method
- `payment_status` - Payment status
- `transaction_id` - Transaction ID
- `created_at` - Order creation timestamp
- `updated_at` - Last update timestamp

## Development

### Running in Development Mode
The application is already configured for development mode with:
- Auto-reload enabled
- Debug mode enabled
- CORS enabled for frontend-backend communication

### Environment Variables
- `DB_HOST` - Database host (default: localhost)
- `DB_NAME` - Database name (default: canteen)
- `DB_USER` - Database user (default: postgres)
- `DB_PASSWORD` - Database password
- `DB_PORT` - Database port (default: 5432)
- `PORT` - Flask server port (default: 5000)
- `FLASK_ENV` - Flask environment (default: development)

## Production Deployment

### Security Considerations
1. **Never commit .env file** - Use environment variables
2. **Hash passwords** - Implement password hashing (bcrypt/argon2)
3. **Use HTTPS** - Enable SSL/TLS
4. **Update CORS settings** - Restrict origins in production
5. **Use gunicorn** - Production WSGI server included in requirements

### Production Server
```bash
# Using gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check credentials in .env file
- Ensure database "canteen" exists

### Port Already in Use
- Change PORT in .env file
- Or kill the process using port 5000

### Module Not Found
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

## Support

For issues and questions, please check:
1. Database logs: Check PostgreSQL logs
2. Application logs: Check Flask console output
3. Browser console: Check for JavaScript errors

## License

This project is for educational purposes.
