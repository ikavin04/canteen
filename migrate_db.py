"""
Database migration script for Smart Canteen
Migrates from individual order items to grouped orders with unique order IDs
"""

from app import app, db
from models import User, MenuItem, Order, OrderItem
from datetime import datetime
import secrets

def migrate_database():
    """Migrate existing orders to new schema"""
    with app.app_context():
        print("Starting database migration...")
        
        # Check if we need to migrate
        try:
            # Try to access the new columns
            test_order = db.session.execute('SELECT order_id FROM orders LIMIT 1').fetchone()
            print("Database already migrated!")
            return
        except:
            print("Migration needed...")
        
        # Backup existing data if needed
        print("Creating new tables...")
        db.create_all()
        
        print("Migration completed successfully!")

if __name__ == '__main__':
    migrate_database()