import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import werkzeug
if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '3.0.0'

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client


def test_normal_order(client):
    """Test 1: Placing a valid order succeeds."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    
    # 1. Check item exists in menu_items -> returns id=1
    # 2. Check user_type for user_id=1 -> returns ('Student',)
    # 3. Check order_id uniqueness -> returns (0,)
    # 4. Insert order -> returns ('ORD-STU123456',)
    mock_cur.fetchall.return_value = [(1,)]
    mock_cur.fetchone.side_effect = [('Student',), (0,), ('ORD-STU123456',)]
    
    with patch('app.get_db_connection', return_value=mock_conn):
        response = client.post('/api/checkout', json={
            'user_id': 1,
            'payment_method': 'UPI',
            'cart': [
                {'id': 1, 'name': 'Coffee', 'price': 30.00, 'quantity': 2}
            ]
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'orderId' in data
        assert data['amount'] == 60.00


def test_invalid_input(client):
    """Test 2: Empty cart or invalid quantity is rejected with clear error."""
    # Empty cart
    response_empty = client.post('/api/checkout', json={
        'user_id': 1,
        'cart': []
    })
    assert response_empty.status_code == 400
    assert response_empty.get_json()['success'] is False
    assert 'Cart is empty' in response_empty.get_json()['message']

    # Non-numeric quantity
    response_invalid_qty = client.post('/api/checkout', json={
        'user_id': 1,
        'cart': [
            {'id': 1, 'name': 'Tea', 'price': 25.00, 'quantity': 'invalid'}
        ]
    })
    assert response_invalid_qty.status_code == 400
    assert response_invalid_qty.get_json()['success'] is False
    assert 'Invalid price or quantity' in response_invalid_qty.get_json()['message']

    # Missing user_id
    response_no_user = client.post('/api/checkout', json={
        'cart': [
            {'id': 1, 'name': 'Tea', 'price': 25.00, 'quantity': 1}
        ]
    })
    assert response_no_user.status_code == 400
    assert response_no_user.get_json()['success'] is False
    assert 'User ID is required' in response_no_user.get_json()['message']


def test_unauthorized_admin_access(client):
    """Test 3: Hitting admin routes without logging in returns 401/403."""
    # 1. Admin stats endpoint
    res_stats = client.get('/api/stats')
    assert res_stats.status_code == 401
    assert res_stats.get_json()['success'] is False
    assert 'Authentication required' in res_stats.get_json()['message']

    # 2. Admin users endpoint
    res_users = client.get('/api/users')
    assert res_users.status_code == 401
    assert res_users.get_json()['success'] is False

    # 3. Admin menu creation
    res_menu = client.post('/api/menu', json={
        'item_name': 'Burger',
        'price': 100,
        'category': 'Main Course'
    })
    assert res_menu.status_code == 401
    assert res_menu.get_json()['success'] is False

    # 4. Admin order listing via ?admin=true
    res_orders = client.get('/api/orders?admin=true')
    assert res_orders.status_code == 401
    assert res_orders.get_json()['success'] is False

    # 5. Non-admin user attempting admin access returns 403
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['role'] = 'user'
    
    res_forbidden = client.get('/api/stats')
    assert res_forbidden.status_code == 403
    assert res_forbidden.get_json()['success'] is False
    assert 'Admin access required' in res_forbidden.get_json()['message']


def test_out_of_range(client):
    """Test 4: Negative quantity or nonexistent item ID is rejected cleanly."""
    # Negative quantity
    res_neg_qty = client.post('/api/checkout', json={
        'user_id': 1,
        'cart': [
            {'id': 1, 'name': 'Tea', 'price': 25.00, 'quantity': -3}
        ]
    })
    assert res_neg_qty.status_code == 400
    assert res_neg_qty.get_json()['success'] is False
    assert 'Item quantity must be greater than 0' in res_neg_qty.get_json()['message']

    # Zero quantity
    res_zero_qty = client.post('/api/checkout', json={
        'user_id': 1,
        'cart': [
            {'id': 1, 'name': 'Tea', 'price': 25.00, 'quantity': 0}
        ]
    })
    assert res_zero_qty.status_code == 400
    assert res_zero_qty.get_json()['success'] is False
    assert 'Item quantity must be greater than 0' in res_zero_qty.get_json()['message']

    # Non-existent item ID in DB
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    # Item 999999 does not exist (empty query result)
    mock_cur.fetchall.return_value = []
    
    with patch('app.get_db_connection', return_value=mock_conn):
        res_nonexistent = client.post('/api/checkout', json={
            'user_id': 1,
            'cart': [
                {'id': 999999, 'name': 'Ghost Item', 'price': 50.00, 'quantity': 1}
            ]
        })
        assert res_nonexistent.status_code == 400
        assert res_nonexistent.get_json()['success'] is False
        assert 'Item ID 999999 does not exist' in res_nonexistent.get_json()['message']
