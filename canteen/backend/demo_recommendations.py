"""
Demo script to test the recommendation engine locally.

This script demonstrates how the recommendation engine works
without needing to start the Flask server or database.

Run: python demo_recommendations.py
"""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from recommendation_engine import get_engine


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_basic_recommendation():
    """Demo basic recommendation with single cart item."""
    print_section("Demo 1: Basic Recommendation - Single Item")
    
    # Sample menu items
    menu_items = [
        {'id': 1, 'item_name': 'Tea', 'price': 10, 'category': 'Beverages', 
         'description': 'Hot tea', 'availability': True},
        {'id': 2, 'item_name': 'Biscuits', 'price': 10, 'category': 'Snacks',
         'description': 'Crispy biscuits', 'availability': True},
        {'id': 3, 'item_name': 'Samosa', 'price': 20, 'category': 'Snacks',
         'description': 'Vegetable samosa', 'availability': True},
        {'id': 4, 'item_name': 'Coffee', 'price': 15, 'category': 'Beverages',
         'description': 'Hot coffee', 'availability': True},
        {'id': 5, 'item_name': 'Rusks', 'price': 15, 'category': 'Snacks',
         'description': 'Toast rusks', 'availability': False},  # Unavailable
    ]
    
    engine = get_engine()
    cart_items = ['Tea']
    
    print(f"Cart Items: {cart_items}")
    print("\nGetting recommendations...")
    
    recommendations = engine.get_recommendations(
        cart_items=cart_items,
        available_items=menu_items,
        max_recommendations=5
    )
    
    print(f"\nFound {len(recommendations)} recommendation(s):")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['item_name']} (₹{rec['price']})")
        print(f"   Category: {rec['category']}")
        print(f"   Score: {rec['recommendation_score']}")
        print(f"   Reason: {rec['reason']}")
    
    print("\n✅ Notice: Rusks is NOT recommended (unavailable)")


def demo_multiple_items():
    """Demo recommendations with multiple cart items."""
    print_section("Demo 2: Multiple Cart Items")
    
    menu_items = [
        {'id': 1, 'item_name': 'Tea', 'price': 10, 'category': 'Beverages',
         'description': 'Hot tea', 'availability': True},
        {'id': 2, 'item_name': 'Coffee', 'price': 15, 'category': 'Beverages',
         'description': 'Hot coffee', 'availability': True},
        {'id': 3, 'item_name': 'Biscuits', 'price': 10, 'category': 'Snacks',
         'description': 'Crispy biscuits', 'availability': True},
        {'id': 4, 'item_name': 'Samosa', 'price': 20, 'category': 'Snacks',
         'description': 'Vegetable samosa', 'availability': True},
        {'id': 5, 'item_name': 'Donuts', 'price': 25, 'category': 'Snacks',
         'description': 'Sweet donuts', 'availability': True},
    ]
    
    engine = get_engine()
    cart_items = ['Tea', 'Coffee']
    
    print(f"Cart Items: {cart_items}")
    print("\nGetting recommendations...")
    
    recommendations = engine.get_recommendations(
        cart_items=cart_items,
        available_items=menu_items,
        max_recommendations=5
    )
    
    print(f"\nFound {len(recommendations)} recommendation(s):")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['item_name']} (₹{rec['price']})")
        print(f"   Score: {rec['recommendation_score']}")
        print(f"   Reason: {rec['reason']}")
    
    print("\n✅ Notice: Recommendations from both Tea and Coffee are combined")


def demo_edge_cases():
    """Demo edge cases."""
    print_section("Demo 3: Edge Cases")
    
    menu_items = [
        {'id': 1, 'item_name': 'Tea', 'price': 10, 'category': 'Beverages',
         'description': 'Hot tea', 'availability': True},
        {'id': 2, 'item_name': 'Biscuits', 'price': 10, 'category': 'Snacks',
         'description': 'Crispy biscuits', 'availability': True},
    ]
    
    engine = get_engine()
    
    # Test 1: Empty cart
    print("Test 1: Empty Cart")
    recommendations = engine.get_recommendations([], menu_items, 5)
    print(f"Result: {len(recommendations)} recommendations (expected: 0)")
    
    # Test 2: Unknown item
    print("\nTest 2: Unknown Item in Cart")
    recommendations = engine.get_recommendations(['UnknownItem123'], menu_items, 5)
    print(f"Result: {len(recommendations)} recommendations")
    print("(No error, gracefully handled)")
    
    # Test 3: Item already in cart
    print("\nTest 3: Recommended Item Already in Cart")
    cart = ['Tea', 'Biscuits']  # Biscuits normally recommended with Tea
    recommendations = engine.get_recommendations(cart, menu_items, 5)
    print(f"Cart: {cart}")
    print(f"Recommendations: {[r['item_name'] for r in recommendations]}")
    print("✅ Notice: Biscuits not recommended (already in cart)")


def demo_association_info():
    """Demo getting association information."""
    print_section("Demo 4: Association Information (Debug)")
    
    engine = get_engine()
    
    items_to_check = ['Tea', 'Coffee', 'Biriyani', 'Pizza']
    
    for item_name in items_to_check:
        info = engine.get_association_info(item_name)
        
        if info:
            print(f"\n{item_name}:")
            print(f"  Category: {info.get('category')}")
            print(f"  Pairs with: {', '.join(info.get('pairs_with', []))}")
            print(f"  Reason: {info.get('reason', 'N/A')}")
        else:
            print(f"\n{item_name}: No association data found")


def demo_performance():
    """Demo performance characteristics."""
    print_section("Demo 5: Performance Test")
    
    import time
    
    menu_items = [
        {'id': i, 'item_name': f'Item{i}', 'price': 10, 'category': 'Test',
         'description': 'Test item', 'availability': True}
        for i in range(100)  # 100 items
    ]
    
    engine = get_engine()
    cart_items = ['Tea', 'Coffee']
    
    # Warm up
    engine.get_recommendations(cart_items, menu_items, 5)
    
    # Time 100 requests
    iterations = 100
    start_time = time.time()
    
    for _ in range(iterations):
        recommendations = engine.get_recommendations(cart_items, menu_items, 5)
    
    end_time = time.time()
    elapsed_ms = (end_time - start_time) * 1000
    avg_ms = elapsed_ms / iterations
    
    print(f"Iterations: {iterations}")
    print(f"Total time: {elapsed_ms:.2f}ms")
    print(f"Average per request: {avg_ms:.2f}ms")
    print(f"Throughput: {iterations / (elapsed_ms / 1000):.0f} req/s")
    
    if avg_ms < 10:
        print("\n✅ Performance: EXCELLENT (< 10ms)")
    elif avg_ms < 50:
        print("\n✅ Performance: GOOD (< 50ms)")
    else:
        print("\n⚠️  Performance: May need optimization")


def main():
    """Run all demos."""
    print("\n" + "█" * 70)
    print(" " * 15 + "RECOMMENDATION ENGINE DEMO")
    print("█" * 70)
    
    try:
        demo_basic_recommendation()
        input("\nPress Enter to continue to next demo...")
        
        demo_multiple_items()
        input("\nPress Enter to continue to next demo...")
        
        demo_edge_cases()
        input("\nPress Enter to continue to next demo...")
        
        demo_association_info()
        input("\nPress Enter to continue to next demo...")
        
        demo_performance()
        
        print("\n" + "=" * 70)
        print("  🎉 All demos completed successfully!")
        print("=" * 70 + "\n")
        
        print("Next steps:")
        print("1. Start Flask server: python app.py")
        print("2. Test API: curl 'http://localhost:5000/api/recommendations?cart_items=Tea'")
        print("3. Integrate in frontend")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
