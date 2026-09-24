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
    user_type TEXT DEFAULT 'Student',
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

-- Create unique index on item_name for safe idempotent seeding
CREATE UNIQUE INDEX IF NOT EXISTS idx_menu_items_name_unique ON menu_items (item_name);

-- Insert 30 freshly curated canteen menu items
INSERT INTO menu_items (item_name, price, category, description, availability, image_url) VALUES
('Tea', 20.00, 'Beverages', 'Aromatic hot Indian masala chai infused with ginger, cardamom, and clove.', true, 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=500'),
('Filter Coffee', 30.00, 'Beverages', 'Traditional South Indian filter coffee brewed with fresh chicory blend and frothy milk.', true, 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500'),
('Cold Coffee', 55.00, 'Beverages', 'Rich blended iced coffee topped with chocolate syrup and creamy foam.', true, 'https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?w=500'),
('Fresh Lime Soda', 35.00, 'Beverages', 'Zesty, fizzy sparkling soda with fresh squeezed lemon juice and mint.', true, 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500'),
('Mango Lassi', 45.00, 'Beverages', 'Thick and chilled yogurt smoothie blended with sweet Alphonso mango pulp.', true, 'https://images.unsplash.com/photo-1553787499-6f9133860278?w=500'),
('Badam Milk', 40.00, 'Beverages', 'Warm aromatic milk simmered with crushed almonds, saffron strands, and cardamom.', true, 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500'),
('Samosa', 25.00, 'Snacks', 'Crisp, golden-fried triangular pastries stuffed with spiced potatoes and green peas.', true, 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500'),
('Paneer Puff', 35.00, 'Snacks', 'Flaky, layered puff pastry filled with mildly spiced marinated paneer cubes.', true, 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500'),
('French Fries', 60.00, 'Snacks', 'Crispy golden potato fingers tossed in sea salt, served with herb ketchup.', true, 'https://images.unsplash.com/photo-1576107232684-1279f3908594?w=500'),
('Veg Cutlet', 30.00, 'Snacks', 'Hearty pan-fried vegetable patties coated in crispy breadcrumbs with mint dip.', true, 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=500'),
('Onion Pakoda', 35.00, 'Snacks', 'Crunchy gram flour fritters studded with sliced onions, green chilies, and curry leaves.', true, 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=500'),
('Mirchi Bajji', 30.00, 'Snacks', 'Plump green banana peppers dipped in spiced chickpea batter and fried golden crisp.', true, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500'),
('Vegetable Sandwich', 70.00, 'Snacks', 'Fresh multigrain bread layered with cucumber, tomato, beetroot, and mint chutney.', true, 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500'),
('Masala Dosa', 70.00, 'Breakfast', 'Crisp golden fermented rice crepe smeared with red chutney and spiced potato mash.', true, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500'),
('Idli Vada Combo', 55.00, 'Breakfast', 'Two feather-light steamed rice cakes paired with a crisp medu vada and hot sambar.', true, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500'),
('Poori Masala', 65.00, 'Breakfast', 'Three puffy deep-fried golden pooris served with flavorful potato sagu.', true, 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=500'),
('Ven Pongal', 50.00, 'Breakfast', 'Comforting rice and yellow moong dal cooked with pure ghee, black pepper, and cashews.', true, 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500'),
('Medu Vada', 40.00, 'Breakfast', 'Two crunchy savory lentil donuts infused with peppercorns, curry leaves, and ginger.', true, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500'),
('Aloo Paratha', 60.00, 'Breakfast', 'Golden griddle-toasted whole wheat flatbread filled with seasoned mashed potatoes.', true, 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=500'),
('Chicken Burger', 120.00, 'Main Course', 'Grilled juicy chicken patty with cheddar cheese slice, fresh lettuce, and garlic mayo.', true, 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500'),
('Veg Burger', 85.00, 'Main Course', 'Crispy spiced vegetable patty topped with melted cheese, tomato, and tangy secret sauce.', true, 'https://images.unsplash.com/photo-1550547660-d9450f859349?w=500'),
('Chicken Biryani', 160.00, 'Main Course', 'Fragrant long-grain basmati rice slow-cooked with spiced marinated chicken and onion raita.', true, 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500'),
('Veg Dum Biryani', 110.00, 'Main Course', 'Aromatic basmati rice layered with garden veggies, saffron, fried onions, and salan.', true, 'https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=500'),
('Paneer Butter Masala with Roti', 130.00, 'Main Course', 'Velvety butter-tomato gravy with soft paneer cubes, served with 3 warm phulkas.', true, 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500'),
('Dal Tadka with Jeera Rice', 95.00, 'Main Course', 'Yellow toor dal tempered with garlic and cumin, paired with aromatic ghee jeera rice.', true, 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500'),
('Pasta', 130.00, 'Main Course', 'Italian penne pasta tossed in creamy parmesan Alfredo sauce with herbs and olives.', true, 'https://images.unsplash.com/photo-1621996346565-e3d5d6281699?w=500'),
('Pizza Slice', 90.00, 'Main Course', 'Generous slice of stone-baked pizza loaded with molten mozzarella and bell peppers.', true, 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500'),
('Gulab Jamun', 40.00, 'Desserts', 'Warm melt-in-mouth milk solid spheres immersed in fragrant cardamom rose sugar syrup.', true, 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500'),
('Ice Cream', 45.00, 'Desserts', 'Creamy double-vanilla ice cream cup topped with crunchy waffle cone crisps.', true, 'https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=500'),
('Chocolate Brownie', 75.00, 'Desserts', 'Warm dense Belgian chocolate fudge brownie with dark chocolate drizzle.', true, 'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500')
ON CONFLICT (item_name) DO UPDATE SET
    price = EXCLUDED.price,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    image_url = EXCLUDED.image_url;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_menu_items_availability ON menu_items(availability);

-- Grant privileges (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_db_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_db_user;
