-- Smart Canteen Database Initialization Script
-- Run this script to create the database and tables

-- Create database (run this as postgres superuser)
-- CREATE DATABASE canteen;

-- Connect to the canteen database before running the rest

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create menu_items table
CREATE TABLE IF NOT EXISTS menu_items (
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

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
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
);

-- Insert sample admin user (password: admin123)
INSERT INTO users (username, email, password, role) 
VALUES ('admin', 'admin@canteen.com', 'admin123', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insert sample regular user (password: user123)
INSERT INTO users (username, email, password, role) 
VALUES ('user', 'user@canteen.com', 'user123', 'user')
ON CONFLICT (username) DO NOTHING;

-- Insert sample menu items
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
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_menu_items_availability ON menu_items(availability);

-- Grant privileges (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_db_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_db_user;
