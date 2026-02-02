# Smart Canteen - Quick Reference Card

## 🚀 Quick Commands

### Database Setup
```bash
# Create database
psql -U postgres -c "CREATE DATABASE canteen;"

# Initialize tables
psql -U postgres -d canteen -f backend/init_db.sql

# Check tables
psql -U postgres -d canteen -c "\dt"

# View users
psql -U postgres -d canteen -c "SELECT * FROM users;"
```

### Backend
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py

# Run with gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend
```
Open browser: http://localhost:5000
Login: http://localhost:5000/login.html
Admin: http://localhost:5000/admin.html
```

## 🔑 Default Credentials

**Admin:**
- Username: `admin`
- Password: `admin123`

**User:**
- Username: `user`
- Password: `user123`

## 📋 Common Tasks

### Add Menu Item (via API)
```bash
curl -X POST http://localhost:5000/api/menu \
  -H "Content-Type: application/json" \
  -d '{"item_name":"Pizza","price":100,"category":"Main Course","availability":true}'
```

### Get All Orders
```bash
curl http://localhost:5000/api/orders?admin=true
```

### Update Order Status
```bash
curl -X PATCH http://localhost:5000/api/orders/ORD-ABC123/status \
  -H "Content-Type: application/json" \
  -d '{"status":"Preparing"}'
```

### Test Login
```bash
curl -X POST http://localhost:5000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 🗄️ Database Queries

### View Menu Items
```sql
SELECT * FROM menu_items WHERE availability = true;
```

### View Recent Orders
```sql
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;
```

### Get Order Statistics
```sql
SELECT 
  COUNT(*) as total_orders,
  SUM(total_amount) as total_revenue
FROM orders 
WHERE payment_status = 'Paid';
```

### Find Orders by User
```sql
SELECT o.*, u.username 
FROM orders o 
JOIN users u ON o.user_id = u.id 
WHERE u.username = 'user';
```

## 🔧 Troubleshooting

### Database won't connect
```bash
# Check PostgreSQL status
pg_ctl status

# Start PostgreSQL (Windows)
pg_ctl start -D "C:\Program Files\PostgreSQL\14\data"

# Start PostgreSQL (Mac)
brew services start postgresql

# Start PostgreSQL (Linux)
sudo systemctl start postgresql
```

### Port 5000 in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9

# Or change port in .env
PORT=8000
```

### Clear database and restart
```bash
# Drop and recreate
psql -U postgres -c "DROP DATABASE canteen;"
psql -U postgres -c "CREATE DATABASE canteen;"
psql -U postgres -d canteen -f backend/init_db.sql
```

## 📊 Order Status Flow

```
Pending → Preparing → Ready → Completed
         ↓
    Cancelled (optional)
```

## 🎯 Testing Checklist

- [ ] Backend starts without errors
- [ ] Can access http://localhost:5000
- [ ] Can login with admin/user
- [ ] Menu items display correctly
- [ ] Can add items to cart
- [ ] Can place order
- [ ] Admin can view orders
- [ ] Admin can update order status
- [ ] Admin can manage menu items

## 📝 File Locations

```
Config:           backend/.env
Database Script:  backend/init_db.sql
Main Backend:     backend/app.py
Frontend JS:      app.js
Styles:           styles.css
```

## 🌐 API Base URL

Development: `http://localhost:5000/api`
Production: Update in app.js line 2

## 📦 Dependencies

**Python:**
- Flask 2.2.5
- psycopg2-binary 2.9.7
- Flask-Cors 3.0.10
- python-dotenv 1.0.0
- gunicorn 21.2.0

**Database:**
- PostgreSQL 12+

## 💾 Backup Database

```bash
# Backup
pg_dump -U postgres canteen > backup.sql

# Restore
psql -U postgres -d canteen -f backup.sql
```

## 🔐 Security Notes

**For Production:**
1. Hash passwords (use bcrypt)
2. Use environment variables
3. Enable HTTPS
4. Update CORS settings
5. Add rate limiting
6. Use strong SECRET_KEY
7. Sanitize all inputs
8. Add CSRF protection

## 📚 Documentation Files

- [README.md](README.md) - Main documentation
- [SETUP.md](SETUP.md) - Detailed setup guide
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- [TESTING.md](TESTING.md) - Testing procedures
- [backend/README.md](backend/README.md) - Backend docs

## 🎨 Color Scheme

Primary: `#ff6b35`
Secondary: `#004e89`
Success: `#28a745`
Error: `#dc3545`
Warning: `#ffc107`

---
**Version:** 2.0.0 | **Stack:** Flask + PostgreSQL + Vanilla JS
