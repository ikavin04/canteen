# Smart Canteen - Complete System Logic Documentation

## System Overview
Smart Canteen is a comprehensive digital canteen management system for KGiSL Institute with complete order flow from registration to food collection.

---

## 1. User Registration & Authentication Flow

### Registration Process
1. **New User Access** → `welcome.html` (Splash Screen)
   - Shows animated welcome screen with:
     - "👋 Welcome! New User?"
     - "🎉 Welcome Back! Old User?"
   - Auto-redirects to `index.html` after 3.5 seconds

2. **Landing Page** → `index.html`
   - Features:
     - Hero section with "Get Started" and "Login" buttons
     - Feature cards (Browse Menu, Easy Ordering, Quick Payment)
     - Navigation to register or login

3. **Registration Form** → `register.html`
   - Fields:
     - Username (min 3 characters)
     - Email (valid format)
     - **User Type** (Student/Staff/Guest) ✨ NEW
     - Password (min 8 chars, 1 uppercase, 1 special)
     - Confirm Password
   - Validation:
     - Client-side validation with error messages
     - Real-time feedback for each field
   - API Call: `POST /api/users/register`
     ```json
     {
       "username": "john_doe",
       "email": "john@example.com",
       "password": "Pass@123",
       "user_type": "Student"
     }
     ```
   - Success → Redirect to `login.html` after 2 seconds

4. **Login** → `login.html`
   - Fields: Username, Password
   - API Call: `POST /api/users/login`
   - Response includes: `{id, username, email, role, user_type}`
   - Role-based routing:
     - `role === 'admin'` → `admin.html`
     - `role === 'user'` → `user_dashboard.html`

---

## 2. User Journey - Order Flow

### Step 1: Browse Menu
**Page:** `user_dashboard.html`

- **Menu Loading:**
  - API: `GET /api/menu?available=1`
  - Categories: Main Course, Snacks, Beverages, Breakfast, Desserts
  - Each item shows: Name, Price, Category, Add to Cart button

- **Cart Management:**
  - Sidebar cart (toggle with cart icon)
  - Add items with quantity
  - Live cart total calculation
  - Cart stored in `localStorage`

### Step 2: Add Items to Cart
- Click "Add to Cart" → Opens quantity modal
- Select quantity (1-10)
- Confirm → Item added to cart
- Cart shows:
  - Item name
  - Quantity controls (+/-)
  - Item total (price × quantity)
  - Remove item option

### Step 3: Checkout
**Page:** `payment.html`

- **Order Summary:**
  - List all cart items with quantities
  - Individual item totals
  - Grand total at bottom

- **Payment Method Selection:**
  - UPI (default)
  - Credit/Debit Card
  - Cash on Pickup

- **Order Placement:**
  - API: `POST /api/checkout`
    ```json
    {
      "cart": [
        {"id": 1, "name": "Tea", "price": 15, "quantity": 2},
        {"id": 2, "name": "Samosa", "price": 20, "quantity": 3}
      ],
      "payment_method": "UPI",
      "user_id": 5
    }
    ```
  - Backend generates:
    - `order_id`: ORD-XXXXXXX (unique)
    - `transaction_id`: TXN-XXXXXXXXX
    - Initial status: "Uncompleted" (Preparing)

### Step 4: Order Confirmation
**Page:** `order_confirmation.html`

Shows professional bill/receipt with:

**Order Summary Section:**
- Order ID
- Transaction ID
- Payment Method
- Status Badge
- Order Time

**Items Ordered:**
- Each item card shows:
  - Item name
  - Quantity and unit price: "Qty: 2 @ ₹15.00"
  - Item total: ₹30.00

**Bill Summary:**
- Subtotal: Sum of all items
- Total Amount: In large gradient text (Coral to Golden)

Example:
```
╔══════════════════════════════════════╗
║        ORDER SUMMARY                  ║
╠══════════════════════════════════════╣
║ Order ID:        ORD-DA312B9A26      ║
║ Transaction ID:  TXN3532095514       ║
║ Payment Method:  UPI                 ║
║ Status:          🟡 Preparing        ║
║ Order Time:      2/2/2026, 4:18 PM  ║
╠══════════════════════════════════════╣
║        ITEMS ORDERED                  ║
║                                       ║
║ Fresh Juice                           ║
║ Qty: 1 @ ₹60.00              ₹60.00 ║
║                                       ║
║ Tea                                   ║
║ Qty: 1 @ ₹15.00              ₹15.00 ║
╠══════════════════════════════════════╣
║ BILL SUMMARY                          ║
║ Subtotal:                     ₹75.00 ║
║ Total Amount:                 ₹75.00 ║
╚══════════════════════════════════════╝
```

### Step 5: Track Order
**Page:** `user_orders.html`

- **Order List:**
  - Filter by: All, Preparing, Ready, Completed
  - Each order card shows:
    - Order ID
    - Status badge with color coding
    - Items count
    - Total amount
    - Order time
    - Action buttons

- **Order Status Timeline:**
  ```
  ✅ Order Placed → ⏳ Preparing → ⏳ Ready → ⏳ Completed
  ```
  - **Uncompleted** (Preparing): Yellow badge, "Being prepared"
  - **Ready**: Blue badge, "Ready for pickup!" notification
  - **Completed**: Green badge, "Order picked up"

- **Real-time Updates:**
  - Auto-polling every 30 seconds
  - Checks for status changes
  - Shows notification when order is ready

### Step 6: Food Collection
**User Side:**
- User sees order status change to "Ready"
- Gets notification: "Your order is ready for pickup!"
- Goes to canteen with Order ID

**Admin Side:**
- See Admin Flow below

---

## 3. Admin Dashboard Flow

**Page:** `admin.html`

### Dashboard Stats (Top Section)
- Available Items
- Unavailable Items
- Orders Today
- Revenue Today

### **Order Verification Section** ✨ NEW
Located at top of dashboard for quick access:

**Purpose:** Verify orders when users come to collect food

**Process:**
1. User arrives at canteen counter
2. User shows Order ID (e.g., "ORD-DA312B9A26")
3. Admin enters Order ID in verification box
4. Click "Verify Order"

**Verification Results:**

✅ **Order Ready for Pickup:**
```
✅ Order ORD-DA312B9A26
Status: Ready for pickup

Customer: john_doe
Items: Fresh Juice (x1), Tea (x1)
Total: ₹75.00
Payment: UPI
Time: 2/2/2026, 4:18:45 PM

[Mark as Collected] Button
```

⏳ **Order Still Preparing:**
```
⏳ Order ORD-DA312B9A26
Status: Still being prepared

Customer: john_doe
Items: Pizza Slice (x2), Fresh Juice (x1)
Total: ₹240.00
Payment: UPI
Time: 2/2/2026, 4:25:30 PM
```

✅ **Already Collected:**
```
✅ Order ORD-DA312B9A26
Status: Already picked up

Customer: john_doe
Items: Tea (x1)
Total: ₹15.00
Payment: Cash
Time: 2/2/2026, 3:10:15 PM
```

❌ **Invalid Order ID:**
```
❌ Order not found
```

**Actions:**
- Click "Mark as Collected" → Updates status to "Completed"
- Order disappears from "Ready" list
- User can see "Completed" status in their order history

### Order Management Tab
- **Order Table:**
  - Order ID
  - Customer name
  - Items count
  - Total amount
  - Status dropdown (change status directly)
  - Time
  - View button

- **Status Management:**
  - Dropdown with 3 options:
    1. **Preparing** (Uncompleted) - Yellow
    2. **Ready** - Blue
    3. **Completed** - Green
  - Change status → Auto-updates user's view
  - Status changes are instant

- **Workflow:**
  1. New order arrives → Status: "Preparing"
  2. Food ready → Admin changes to "Ready"
  3. User notified → Comes to collect
  4. Admin verifies Order ID → Marks as "Collected"
  5. Status → "Completed"

### Menu Management Tab
- Add/Edit/Delete menu items
- Toggle availability
- Set price and category
- Real-time menu updates

---

## 4. Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    user_type TEXT DEFAULT 'Student',  -- NEW: Student/Staff/Guest
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Menu Items Table
```sql
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
);
```

### Orders Table
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_id TEXT UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    items JSONB NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    status TEXT DEFAULT 'Uncompleted',
    payment_method TEXT,
    payment_status TEXT DEFAULT 'Pending',
    transaction_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. API Endpoints

### Authentication
- `POST /api/users/register` - Create new user
- `POST /api/users/login` - Login user
- `GET /api/users` - Get all users (admin)

### Menu
- `GET /api/menu` - Get all menu items
- `GET /api/menu?available=1` - Get available items only
- `POST /api/menu` - Add new item (admin)
- `PUT /api/menu/:id` - Update item (admin)
- `DELETE /api/menu/:id` - Delete item (admin)

### Orders
- `POST /api/checkout` - Create new order
- `GET /api/orders` - Get all orders
- `GET /api/orders?user_id=5` - Get user's orders
- `PATCH /api/orders/:order_id/status` - Update order status

---

## 6. Order Status Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PLACED    │────▶│  PREPARING  │────▶│    READY    │────▶│  COMPLETED  │
│ (Checkout)  │     │(Uncompleted)│     │ (For Pickup)│     │ (Collected) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           ▲                    │                    │
                           │                    │                    │
                      Admin Changes        User Notified      Admin Verifies
                         Status               Auto-Poll           & Marks
```

### Status Details:
1. **Placed (Initial)**
   - Created at checkout
   - Payment method recorded
   - Transaction ID generated

2. **Preparing (Uncompleted)**
   - Food being prepared
   - Yellow badge in UI
   - User can view in "My Orders"

3. **Ready**
   - Food ready for pickup
   - Blue badge
   - User gets notification
   - Shows "Ready for pickup!" message

4. **Completed**
   - Food collected by user
   - Green badge
   - Verified by admin
   - Final state

---

## 7. Key Features

### For Users:
✅ Browse menu by category
✅ Add items to cart with quantity
✅ Multiple payment methods
✅ Professional bill/receipt
✅ Real-time order tracking
✅ Status notifications
✅ Order history
✅ Download bill option

### For Admin:
✅ Dashboard with quick stats
✅ **Order ID verification system** (NEW)
✅ **Quick "Mark as Collected" button** (NEW)
✅ Order status management
✅ Menu management (CRUD)
✅ User management
✅ Revenue tracking
✅ Real-time order updates

---

## 8. Color Theme

```css
Primary Colors:
- Coral: #FF724C
- Golden: #FDBF50
- Navy: #2A2C41
- Light BG: #F4F4F8
- White: #FFFFFF

Typography:
- Font Family: 'EB Garamond', Georgia
- Headings: 800 weight
- Buttons: 600 weight
- Prices: 800 weight
```

---

## 9. Demo Accounts

Auto-created on backend startup:

**Admin:**
- Username: `admin`
- Password: `admin123`
- Access: Full admin dashboard

**User:**
- Username: `user`
- Password: `user123`
- Access: User dashboard

---

## 10. Complete User Flow Example

### Scenario: Student Orders Tea and Samosa

1. **Welcome Screen** (3.5s)
   - Animated splash with welcome messages

2. **Register** (if new user)
   - Username: "john_doe"
   - Email: "john@kgisl.edu"
   - User Type: "Student" ✨
   - Password: "Pass@123"

3. **Login**
   - Enter credentials → Redirect to user_dashboard.html

4. **Browse & Order**
   - View menu → Select "Tea" (₹15) and "Samosa" (₹20)
   - Add to cart → Cart shows ₹35 total
   - Click "Proceed to Checkout"

5. **Payment**
   - Review order: Tea (1), Samosa (1)
   - Select payment: UPI
   - Click "Place Order"

6. **Confirmation**
   - Order ID: ORD-DA312B9A26
   - Transaction ID: TXN3532095514
   - Status: Preparing
   - View professional bill with all details

7. **Track Order**
   - Go to "My Orders"
   - See order with yellow "Preparing" badge
   - Timeline shows: Placed ✅ → Preparing ⏳

8. **Order Ready Notification**
   - Admin changes status to "Ready"
   - User sees blue "Ready" badge
   - Notification: "Your order is ready for pickup!"
   - Timeline: Placed ✅ → Preparing ✅ → Ready ✅

9. **Collection**
   - User goes to canteen
   - Shows Order ID to admin
   - Admin enters "ORD-DA312B9A26"
   - Verification shows:
     - ✅ Order Ready
     - Customer: john_doe
     - Items: Tea (x1), Samosa (x1)
     - Total: ₹35.00
   - Admin clicks "Mark as Collected"

10. **Completed**
    - Status changes to "Completed"
    - Green badge in user's order history
    - Timeline: All steps ✅
    - Order archived

---

## 11. Testing Checklist

### Frontend Testing:
- [ ] Splash screen displays and redirects
- [ ] Registration with all user types works
- [ ] Login redirects correctly (admin vs user)
- [ ] Menu loads with all categories
- [ ] Cart add/remove/update works
- [ ] Checkout creates order
- [ ] Bill displays correctly
- [ ] Order status updates in real-time
- [ ] Admin verification finds orders
- [ ] Mark as collected works

### Backend Testing:
- [ ] Database tables created
- [ ] Demo users inserted
- [ ] Registration stores user_type
- [ ] Login returns user_type
- [ ] Menu items CRUD works
- [ ] Orders created with unique IDs
- [ ] Status updates persist
- [ ] Order retrieval by ID works

### End-to-End:
- [ ] Complete user journey from register to collection
- [ ] Admin can manage all orders
- [ ] Real-time status sync between user and admin
- [ ] Payment methods recorded correctly
- [ ] Bill calculations accurate

---

## 12. Running the Application

### Backend (Terminal 1):
```bash
cd backend
.\.venv\Scripts\Activate.ps1
python app.py
```
- Runs on: http://localhost:5000
- Auto-creates database tables and demo data

### Frontend (Terminal 2):
```bash
python -m http.server 3000
```
- Runs on: http://localhost:3000
- Access: http://localhost:3000/welcome.html

---

## Summary

The Smart Canteen system provides a **complete end-to-end solution** for digital canteen management:

✅ **User Type Selection** during registration (Student/Staff/Guest)
✅ **Welcome Splash Screen** for better UX
✅ **Professional Bill/Receipt** with proper alignment and pricing
✅ **Order Verification System** for admins to verify pickup
✅ **Real-time Order Tracking** with status updates
✅ **Complete Order Lifecycle** from placement to collection

All logic flows smoothly from registration → ordering → payment → tracking → collection, with proper synchronization between user and admin views!
