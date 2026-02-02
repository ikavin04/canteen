# Smart Canteen API Reference

Base URL: `http://localhost:5000/api`

## Authentication

All endpoints accept JSON requests and return JSON responses.

### Register User
```http
POST /api/users/register
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string"
}

Response:
{
  "success": true,
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "role": "user"
  }
}
```

### Login User
```http
POST /api/users/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}

Response:
{
  "success": true,
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "role": "user"
  }
}
```

## Menu Management

### Get All Menu Items
```http
GET /api/menu
GET /api/menu?available=true  # Filter by availability

Response:
{
  "success": true,
  "menu": [
    {
      "id": 1,
      "item_name": "Chicken Burger",
      "price": 120.00,
      "category": "Main Course",
      "description": "Juicy chicken burger",
      "availability": true,
      "image_url": "",
      "created_at": "2026-02-02T10:00:00",
      "updated_at": "2026-02-02T10:00:00"
    }
  ]
}
```

### Get Single Menu Item
```http
GET /api/menu/{id}

Response:
{
  "success": true,
  "item": {
    "id": 1,
    "item_name": "Chicken Burger",
    "price": 120.00,
    "category": "Main Course",
    "description": "Juicy chicken burger",
    "availability": true,
    "image_url": ""
  }
}
```

### Add Menu Item (Admin)
```http
POST /api/menu
Content-Type: application/json

{
  "item_name": "Pizza Slice",
  "price": 100.00,
  "category": "Main Course",
  "description": "Cheesy pizza slice",
  "availability": true,
  "image_url": ""
}

Response:
{
  "success": true,
  "item": { ... }
}
```

### Update Menu Item (Admin)
```http
PUT /api/menu/{id}
Content-Type: application/json

{
  "item_name": "Updated Name",
  "price": 150.00,
  "availability": false
}

Response:
{
  "success": true,
  "item": { ... }
}
```

### Delete Menu Item (Admin)
```http
DELETE /api/menu/{id}

Response:
{
  "success": true,
  "message": "Item deleted successfully"
}
```

## Order Management

### Place Order
```http
POST /api/checkout
Content-Type: application/json

{
  "cart": [
    {
      "id": 1,
      "name": "Chicken Burger",
      "price": 120.00,
      "quantity": 2
    }
  ],
  "payment_method": "UPI",
  "user": {
    "id": 1,
    "username": "user"
  }
}

Response:
{
  "success": true,
  "message": "Payment processed",
  "orderId": "ORD-ABC123DEF4",
  "amount": 240.00
}
```

### Get Orders
```http
# Get all orders (Admin)
GET /api/orders?admin=true

# Get user's orders
GET /api/orders?user_id=1

# Get orders by username
GET /api/orders?username=user

Response:
{
  "success": true,
  "orders": [
    {
      "id": 1,
      "order_id": "ORD-ABC123DEF4",
      "user_id": 1,
      "items": [...],
      "total_amount": 240.00,
      "status": "Pending",
      "payment_method": "UPI",
      "payment_status": "Paid",
      "transaction_id": "TXN123456",
      "created_at": "2026-02-02T10:00:00",
      "updated_at": "2026-02-02T10:00:00"
    }
  ]
}
```

### Update Order Status (Admin)
```http
PATCH /api/orders/{order_id}/status
Content-Type: application/json

{
  "status": "Preparing"
}

Response:
{
  "success": true,
  "orderId": "ORD-ABC123DEF4"
}
```

## Statistics (Admin)

### Get Dashboard Stats
```http
GET /api/stats

Response:
{
  "success": true,
  "stats": {
    "totalUsers": 10,
    "totalOrders": 25,
    "totalRevenue": 5000.00,
    "pendingOrders": 5,
    "availableItems": 15,
    "unavailableItems": 2,
    "ordersToday": 8,
    "revenueToday": 1200.00
  }
}
```

## Error Responses

All endpoints may return error responses:

```json
{
  "success": false,
  "message": "Error description"
}
```

Common HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

## Order Status Values

- `Pending` - Order placed, waiting for preparation
- `Preparing` - Order is being prepared
- `Ready` - Order is ready for pickup
- `Completed` - Order has been completed
- `Cancelled` - Order was cancelled

## Payment Methods

- `UPI`
- `Card`
- `Cash`
- `Wallet`

## Categories

- `Main Course`
- `Snacks`
- `Beverages`
- `Desserts`
