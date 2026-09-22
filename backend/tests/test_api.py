import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import werkzeug
if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '3.0.0'

import app as app_module
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


def test_razorpay_create_order_simulator(client):
    """Test 5: Creating Razorpay order without live keys falls back to simulator."""
    res = client.post('/api/payment/razorpay/create-order', json={
        'user_id': 1,
        'cart': [{'id': 1, 'name': 'Dosa', 'price': 40.0, 'quantity': 2}],
        'amount': 80.0
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['mode'] == 'demo'
    assert data['amount'] == 8000  # 80 INR in paise
    assert data['order_id'].startswith('order_rzp_')


def test_razorpay_create_order_live(client):
    """Test 6: Creating Razorpay order with live keys invokes razorpay client."""
    mock_rzp_client = MagicMock()
    mock_rzp_client.order.create.return_value = {'id': 'order_live_123456'}
    mock_rzp = MagicMock()
    mock_rzp.Client.return_value = mock_rzp_client

    with patch.object(app_module, 'RAZORPAY_AVAILABLE', True), \
         patch.object(app_module, 'RAZORPAY_KEY_ID', 'rzp_live_testkey12345'), \
         patch.object(app_module, 'RAZORPAY_KEY_SECRET', 'testsecretkey12345'), \
         patch.object(app_module, 'razorpay', mock_rzp):
        res = client.post('/api/payment/razorpay/create-order', json={
            'user_id': 1,
            'cart': [{'id': 1, 'name': 'Dosa', 'price': 40.0, 'quantity': 1}],
            'amount': 40.0
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True
        assert data['mode'] == 'live'
        assert data['order_id'] == 'order_live_123456'


def test_razorpay_create_order_validation(client):
    """Test 7: Razorpay create-order validates cart and user."""
    # Empty cart
    res_empty = client.post('/api/payment/razorpay/create-order', json={
        'user_id': 1,
        'cart': []
    })
    assert res_empty.status_code == 400
    assert 'Cart is empty' in res_empty.get_json()['message']

    # Missing user
    res_no_user = client.post('/api/payment/razorpay/create-order', json={
        'cart': [{'id': 1, 'name': 'Tea', 'price': 20.0, 'quantity': 1}]
    })
    assert res_no_user.status_code == 400
    assert 'User ID is required' in res_no_user.get_json()['message']


def test_razorpay_verify_payment_simulator(client):
    """Test 8: Verifying simulated payment completes order and stores in DB."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.side_effect = [('Student',), (0,), ('ORD-STU998877',)]

    with patch('app.get_db_connection', return_value=mock_conn):
        res = client.post('/api/payment/razorpay/verify', json={
            'user_id': 1,
            'razorpay_order_id': 'order_rzp_test123',
            'razorpay_payment_id': 'pay_sim_998877',
            'razorpay_signature': 'simulated_signature_valid',
            'cart': [{'id': 1, 'name': 'Meals', 'price': 80.0, 'quantity': 1}],
            'amount': 80.0
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True
        assert data['orderId'] == 'ORD-STU998877'
        assert data['amount'] == 80.0


def test_razorpay_verify_payment_live_invalid_sig(client):
    """Test 9: Live payment with tampered signature is rejected."""
    with patch('app.RAZORPAY_KEY_ID', 'rzp_live_testkey12345'), \
         patch('app.RAZORPAY_KEY_SECRET', 'testsecretkey12345'):
        res = client.post('/api/payment/razorpay/verify', json={
            'user_id': 1,
            'razorpay_order_id': 'order_live_123',
            'razorpay_payment_id': 'pay_live_456',
            'razorpay_signature': 'bad_tampered_signature',
            'cart': [{'id': 1, 'name': 'Meals', 'price': 80.0, 'quantity': 1}],
            'amount': 80.0
        })
        assert res.status_code == 400
        data = res.get_json()
        assert data['success'] is False
        assert 'Invalid payment signature' in data['message']


def test_custom_404_api(client):
    """Test 10: API routes that do not exist return structured JSON 404."""
    res = client.get('/api/unknown/endpoint')
    assert res.status_code == 404
    data = res.get_json()
    assert data['success'] is False
    assert 'not found' in data['message'].lower()


def test_custom_404_frontend(client):
    """Test 11: Non-existent static routes return 404 and serve 404.html."""
    res = client.get('/nonexistent-page-xyz.html')
    assert res.status_code == 404
    # Ensure it served the custom 404.html content
    assert b'404' in res.data
    assert b'Dish Not Found' in res.data


def test_get_orders_by_order_id(client):
    """Test 12: Querying orders by order_id returns the matching order."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = [{'order_id': 'ORD-STU123456', 'total_amount': 120.0}]

    with patch('app.get_db_connection', return_value=mock_conn):
        res = client.get('/api/orders?order_id=ORD-STU123456')
        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True
        assert len(data['orders']) == 1
        assert data['orders'][0]['order_id'] == 'ORD-STU123456'


def test_header_fallback_auth_admin(client):
    """Test 13: Admin endpoint accepts X-User-Id and X-User-Role headers."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = {'count': 5, 'revenue': 1000.0}

    with patch('app.get_db_connection', return_value=mock_conn):
        res = client.get('/api/stats', headers={
            'X-User-Id': '1',
            'X-User-Role': 'admin'
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True
