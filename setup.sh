#!/bin/bash
# Smart Canteen - Quick Setup Script for Mac/Linux

echo "================================"
echo "Smart Canteen Setup Script"
echo "================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

echo
echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo
echo "[3/5] Installing Python dependencies..."
pip install -r requirements.txt

echo
echo "[4/5] Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ".env file created. Please edit it with your database password."
    echo
    echo "IMPORTANT: Edit backend/.env and set your PostgreSQL password!"
else
    echo ".env file already exists."
fi

echo
echo "[5/5] Setup complete!"
echo
echo "================================"
echo "Next Steps:"
echo "================================"
echo "1. Install PostgreSQL if not installed"
echo "2. Create database: psql -U postgres -c 'CREATE DATABASE canteen;'"
echo "3. Initialize database: psql -U postgres -d canteen -f backend/init_db.sql"
echo "4. Edit backend/.env with your database password"
echo "5. Run: cd backend && python app.py"
echo
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo
echo "Default user credentials:"
echo "  Username: user"
echo "  Password: user123"
echo
