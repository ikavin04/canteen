# Testing Guide - Smart Canteen

## Manual Testing Checklist

### 1. Database Setup Testing

- [ ] PostgreSQL is installed and running
- [ ] Database "canteen" is created
- [ ] Tables are created using init_db.sql
- [ ] Default users (admin/user) are inserted
- [ ] Sample menu items are inserted

```bash
# Verify database setup
psql -U postgres -d canteen -c "\dt"
# Should show: users, menu_items, orders

psql -U postgres -d canteen -c "SELECT * FROM users;"
# Should show admin and user accounts

psql -U postgres -d canteen -c "SELECT COUNT(*) FROM menu_items;"
# Should show 10 menu items
```

### 2. Backend Testing

#### Start Server
```bash
cd backend
python app.py
```

Expected output:
```
Database tables initialized successfully.
 * Running on http://0.0.0.0:5000
```

#### Test API Endpoints

**Health Check**
```bash
curl http://localhost:5000/api/health
# Expected: {"status":"ok"}
```

**Get Menu**
```bash
curl http://localhost:5000/api/menu
# Expected: JSON array of menu items
```

**User Login**
```bash
curl -X POST http://localhost:5000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# Expected: {"success":true,"user":{...}}
```

**Get Statistics**
```bash
curl http://localhost:5000/api/stats
# Expected: JSON with stats
```

### 3. Frontend Testing

#### Registration Flow
1. Navigate to `http://localhost:5000/register.html`
2. Fill in registration form:
   - Username: testuser
   - Email: test@example.com
   - Password: test123
3. Click Register
4. Should redirect to index.html
5. Check localStorage for user data

#### Login Flow
1. Navigate to `http://localhost:5000/login.html`
2. Test with admin credentials:
   - Username: admin
   - Password: admin123
3. Click Login
4. Should redirect to admin.html for admin
5. Should redirect to index.html for regular users

#### User Dashboard Flow
1. Login as regular user (username: user, password: user123)
2. Navigate to `http://localhost:5000/user_dashboard.html`
3. Verify menu items are displayed
4. Add items to cart
5. Update quantities
6. Proceed to checkout
7. Complete payment
8. Verify order in user_orders.html

#### Admin Panel Flow
1. Login as admin (username: admin, password: admin123)
2. Navigate to `http://localhost:5000/admin.html`
3. Test Dashboard tab:
   - Verify statistics are displayed
   - Check recent orders list
4. Test Menu Management tab:
   - Add new menu item
   - Edit existing item
   - Toggle availability
   - Delete item
5. Test Order Management tab:
   - View all orders
   - Update order status
   - Verify status changes

### 4. Integration Testing

#### Complete Order Flow
1. Login as user
2. Add 3 items to cart
3. Navigate to checkout
4. Complete payment with UPI
5. Check order confirmation page
6. Login as admin
7. Verify order appears in admin panel
8. Update order status to "Preparing"
9. Login as user again
10. Verify status update in user_orders.html

#### Menu Management Flow
1. Login as admin
2. Add new item "Test Item" - ₹99
3. Verify item appears in menu list
4. Toggle availability to false
5. Login as user
6. Verify item is not available for ordering
7. Login as admin
8. Delete "Test Item"
9. Verify item is removed from database

### 5. Database Integrity Testing

**Check User Registration**
```sql
SELECT COUNT(*) FROM users;
-- Should increase after each registration
```

**Check Orders**
```sql
SELECT * FROM orders ORDER BY created_at DESC LIMIT 5;
-- Should show recent orders with correct data
```

**Check Menu Items**
```sql
SELECT * FROM menu_items WHERE availability = true;
-- Should show only available items
```

**Check Order Items (JSON)**
```sql
SELECT order_id, items FROM orders;
-- Should show proper JSON structure
```

### 6. Error Handling Testing

#### Test Invalid Login
- Try login with wrong password
- Expected: Error message displayed

#### Test Empty Cart Checkout
- Navigate to payment without items
- Expected: Error message about empty cart

#### Test Duplicate Registration
- Register with existing username
- Expected: Error message about duplicate user

#### Test Invalid Menu Item
- Try to add item with negative price
- Expected: Validation error

#### Test Unauthorized Access
- Try to access admin.html without login
- Expected: Should check authentication

### 7. Browser Console Testing

Open browser developer tools (F12) and check:

1. No JavaScript errors in console
2. Network tab shows successful API calls
3. localStorage contains proper data structure
4. No CORS errors

### 8. Cross-Browser Testing

Test on:
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari
- [ ] Mobile browsers

### 9. Performance Testing

**Database Query Performance**
```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 1;
-- Check if indexes are being used
```

**API Response Time**
- Menu loading: < 500ms
- Order placement: < 1s
- Login: < 500ms

### 10. Security Testing

- [ ] Passwords are not visible in browser
- [ ] API doesn't expose sensitive data
- [ ] SQL injection protection (parameterized queries)
- [ ] XSS protection
- [ ] CSRF protection should be added for production

## Automated Testing (Future)

### Python Unit Tests
Create `backend/tests/test_api.py`:
```python
import pytest
from app import app

def test_health_check():
    client = app.test_client()
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'
```

### Run Tests
```bash
pytest backend/tests/
```

## Common Issues & Solutions

### Database Connection Failed
- Check if PostgreSQL is running
- Verify credentials in .env file
- Check if database exists

### Port 5000 Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9
```

### Menu Items Not Loading
- Check browser console for errors
- Verify API endpoint is accessible
- Check CORS settings

### Orders Not Saving
- Check database connection
- Verify orders table exists
- Check PostgreSQL logs

## Test Data

### Sample Users
```
Admin: admin / admin123
User: user / user123
```

### Sample Menu Items
All items in Main Course, Snacks, Beverages, Desserts categories

### Sample Orders
Place test orders with different:
- Payment methods (UPI, Card, Cash)
- Order statuses (Pending, Preparing, Ready, Completed)
- Multiple items with different quantities

## Success Criteria

✅ All API endpoints return expected responses
✅ User can register and login successfully
✅ User can browse menu and add items to cart
✅ User can place orders and view order history
✅ Admin can manage menu items (CRUD)
✅ Admin can view and update order statuses
✅ Database maintains data integrity
✅ No console errors in browser
✅ Responsive design works on mobile
✅ Application handles errors gracefully
