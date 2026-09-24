import pytest
from app import app
from rag_recommender import get_rag_recommendations

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_rag_tea_recommends_samosa():
    """Verify that adding Tea strongly recommends Samosa with pairing explanation."""
    mock_menu = [
        {'id': 1, 'item_name': 'Tea', 'price': 20.0, 'category': 'Beverages'},
        {'id': 2, 'item_name': 'Samosa', 'price': 25.0, 'category': 'Snacks'},
        {'id': 3, 'item_name': 'Chicken Burger', 'price': 120.0, 'category': 'Main Course'},
        {'id': 4, 'item_name': 'French Fries', 'price': 60.0, 'category': 'Snacks'}
    ]
    recs = get_rag_recommendations([{'id': 1, 'item_name': 'Tea'}], mock_menu)
    assert len(recs) > 0
    top = recs[0]
    assert top['item_name'] == 'Samosa'
    assert top['confidence_score'] >= 90
    assert 'match made in heaven' in top['headline'].lower()
    assert 'tea' in top['explanation'].lower() or 'chai' in top['explanation'].lower()

def test_api_recommendations_endpoint(client):
    """Test the /api/recommendations endpoint via HTTP POST."""
    res = client.post('/api/recommendations', json={'cart': [{'item_name': 'Tea'}]})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['recommendations']) > 0
    top = data['recommendations'][0]
    assert top['item_name'] == 'Samosa'
    assert top['price'] > 0
    assert top['headline'] != ''
    assert top['explanation'] != ''

def test_api_recommendations_empty_cart(client):
    """Test /api/recommendations returns default campus favorites when cart is empty."""
    res = client.post('/api/recommendations', json={'cart': []})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['recommendations']) > 0
