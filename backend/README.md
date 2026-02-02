# Smart Canteen Backend

Flask backend with PostgreSQL database for the Smart Canteen application.

## Quick Start

### 1. Install PostgreSQL and create database

```sql
-- Connect as postgres superuser
psql -U postgres

-- Create database
CREATE DATABASE canteen;

-- Exit
\q
```

### 2. Initialize database tables

```bash
psql -U postgres -d canteen -f init_db.sql
```

### 3. Setup Python environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Copy example file
cp .env.example .env

# Edit .env and set your database password
# Default values:
# DB_NAME=canteen
# DB_USER=postgres
# DB_PASSWORD=your_password_here
# DB_HOST=localhost
# DB_PORT=5432
```

### 5. Run the application

```powershell
python app.py
```

Server will run on `http://localhost:5000`

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
- `GET /api/orders` - Get orders (supports filters: user_id, admin)
- `PATCH /api/orders/<order_id>/status` - Update order status (Admin)

### Statistics
- `GET /api/stats` - Get admin dashboard statistics

## Database Schema

### Tables
- **users** - User accounts (id, username, email, password, role, created_at)
- **menu_items** - Menu items (id, item_name, price, category, description, availability, image_url, created_at, updated_at)
- **orders** - Orders (id, order_id, user_id, items (JSONB), total_amount, status, payment_method, payment_status, transaction_id, created_at, updated_at)

## Default Accounts

Automatically created by `init_db.sql`:
- **Admin**: username=`admin`, password=`admin123`
- **User**: username=`user`, password=`user123`

## Features

- RESTful API architecture
- PostgreSQL database integration
- User authentication
- Complete menu management (CRUD operations)
- Order processing and tracking
- Admin statistics dashboard
- CORS enabled for frontend communication
- Automatic table creation on startup

## Production Deployment

Use gunicorn for production:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Notes

- CORS is enabled for local development
- Password hashing should be implemented for production
- Environment variables should be used for sensitive configuration
- Database tables are created automatically if they don't exist

