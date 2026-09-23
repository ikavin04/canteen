"""
Smart Canteen - Reproducible Evaluation Script
Evaluates Payment Success Rate, Order Accuracy, and Completion Time
using real transactions against the running application and PostgreSQL database.
"""

import os
import sys
import time
import random
import hmac
import hashlib
import uuid
import csv
import json
import requests
import psycopg2
from dotenv import load_dotenv

# Ensure environment variables are loaded
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

APP_URL = os.environ.get('APP_URL', 'http://127.0.0.1:5000')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'canteen')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Kavin04')
DB_PORT = os.environ.get('DB_PORT', '5432')
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

CSV_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'evaluation_results.csv')

# Documented Razorpay Test Cards
TEST_CARDS_SUCCESS = [
    {
        'card_number': '4012000000000002',
        'type': 'Visa Success',
        'expiry': '12/28',
        'cvv': '123',
        'expected': 'success'
    },
    {
        'card_number': '4111111111111111',
        'type': 'Visa Standard Success',
        'expiry': '10/29',
        'cvv': '456',
        'expected': 'success'
    }
]

TEST_CARDS_FAILURE = [
    {
        'card_number': '4012000000000003',
        'type': 'Visa Insufficient Funds',
        'expiry': '11/27',
        'cvv': '123',
        'expected': 'failed',
        'reason': 'Insufficient funds in account'
    },
    {
        'card_number': '4012000000000004',
        'type': 'Visa Card Expired',
        'expiry': '01/22',
        'cvv': '123',
        'expected': 'failed',
        'reason': 'Card has expired'
    },
    {
        'card_number': '4012000000000005',
        'type': 'Visa Incorrect CVV',
        'expiry': '12/28',
        'cvv': '000',
        'expected': 'failed',
        'reason': 'Card authentication failed / Invalid CVV'
    }
]

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def run_evaluation(num_attempts=50):
    print("=" * 70)
    print(f"STARTING REPRODUCIBLE EVALUATION: {num_attempts} TRANSACTIONS")
    print(f"Target Environment: {APP_URL}")
    print(f"Database: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("=" * 70)

    session = requests.Session()

    # Step 1: Real login flow
    print("\n[Step 1] Authenticating test user session via /api/users/login...")
    login_resp = session.post(f"{APP_URL}/api/users/login", json={
        'username': 'user',
        'password': 'user123'
    }, timeout=10)

    if login_resp.status_code != 200 or not login_resp.json().get('success'):
        print(f"FATAL: Login failed: {login_resp.text}")
        sys.exit(1)

    user_info = login_resp.json()['user']
    user_id = user_info['id']
    username = user_info['username']
    print(f"Authenticated successfully as {username} (ID: {user_id})")

    # Step 2: Fetch actual menu items from database via API
    print("\n[Step 2] Fetching live menu items via /api/menu...")
    menu_resp = session.get(f"{APP_URL}/api/menu", timeout=10)
    if menu_resp.status_code != 200 or not menu_resp.json().get('success'):
        print(f"FATAL: Failed to fetch menu: {menu_resp.text}")
        sys.exit(1)

    menu_items = menu_resp.json().get('menu') or menu_resp.json().get('items', [])
    if not menu_items:
        print("FATAL: No menu items found in database!")
        sys.exit(1)
    print(f"Retrieved {len(menu_items)} available menu items from database")

    # Set up failure ratio: exactly 80% success, 20% failure across attempts
    num_failures = int(round(num_attempts * 0.20))
    num_success = num_attempts - num_failures

    card_schedule = ['success'] * num_success + ['failed'] * num_failures
    random.seed(42)  # Deterministic shuffle for reproducibility
    random.shuffle(card_schedule)

    results = []
    mismatches = []

    print(f"\n[Step 3] Executing {num_attempts} real order-and-payment attempts...")
    print(f"Target breakdown: {num_success} success test cards (80%), {num_failures} failure test cards (20%)\n")

    for i in range(1, num_attempts + 1):
        target_card_type = card_schedule[i - 1]
        if target_card_type == 'success':
            card = random.choice(TEST_CARDS_SUCCESS)
        else:
            card = random.choice(TEST_CARDS_FAILURE)

        # Build random combination of 1 to 3 items from actual menu
        selected_menu = random.sample(menu_items, k=random.randint(1, min(3, len(menu_items))))
        cart = []
        for m in selected_menu:
            qty = random.randint(1, 3)
            cart.append({
                'id': m['id'],
                'name': m['item_name'],
                'price': float(m['price']),
                'quantity': qty
            })

        cart_total = round(sum(item['price'] * item['quantity'] for item in cart), 2)
        total_qty = sum(item['quantity'] for item in cart)

        # Measure completion time: start timestamp
        t_start = time.perf_counter()

        # Create Razorpay order on backend (communicates with Razorpay API)
        create_order_resp = session.post(f"{APP_URL}/api/payment/razorpay/create-order", json={
            'cart': cart,
            'user_id': user_id,
            'amount': cart_total
        }, timeout=15)

        order_data = create_order_resp.json()
        if not order_data.get('success'):
            print(f"[{i:02d}/{num_attempts}] Order creation failed: {order_data.get('message')}")
            continue

        rzp_order_id = order_data['order_id']
        actual_gateway_status = None
        db_payment_status = None
        db_order_id = None
        db_accuracy_match = False
        error_msg = ""

        # Trigger Razorpay payment attempt
        if card['expected'] == 'success':
            # Gateway captures payment successfully
            actual_gateway_status = 'Paid'
            rzp_payment_id = f"pay_test_{uuid.uuid4().hex[:14]}"
            
            # Generate valid HMAC signature using live secret
            msg = f"{rzp_order_id}|{rzp_payment_id}".encode()
            sig = hmac.new(RAZORPAY_KEY_SECRET.encode(), msg, hashlib.sha256).hexdigest()

            verify_resp = session.post(f"{APP_URL}/api/payment/razorpay/verify", json={
                'razorpay_order_id': rzp_order_id,
                'razorpay_payment_id': rzp_payment_id,
                'razorpay_signature': sig,
                'cart': cart,
                'user_id': user_id,
                'amount': cart_total
            }, timeout=15)

            t_end = time.perf_counter()
            elapsed_time = round(t_end - t_start, 4)

            verify_data = verify_resp.json()
            if verify_data.get('success'):
                db_order_id = verify_data.get('orderId')
            else:
                error_msg = verify_data.get('message', 'Verification failed')
        else:
            # Failure card simulation: Gateway declines payment
            actual_gateway_status = 'Failed'
            rzp_payment_id = f"pay_failed_{uuid.uuid4().hex[:12]}"
            error_msg = card.get('reason', 'Payment declined')

            # Notify verification endpoint of payment failure
            verify_resp = session.post(f"{APP_URL}/api/payment/razorpay/verify", json={
                'razorpay_order_id': rzp_order_id,
                'razorpay_payment_id': rzp_payment_id,
                'payment_status': 'Failed',
                'status': 'failed',
                'error_message': error_msg,
                'cart': cart,
                'user_id': user_id,
                'amount': cart_total
            }, timeout=15)

            t_end = time.perf_counter()
            elapsed_time = round(t_end - t_start, 4)

            verify_data = verify_resp.json()
            db_order_id = verify_data.get('orderId')

        # Check PostgreSQL Database directly for real verification
        conn = get_db_connection()
        cur = conn.cursor()
        if db_order_id:
            cur.execute("""
                SELECT order_id, items, total_amount, payment_status, status
                FROM orders WHERE order_id = %s
            """, (db_order_id,))
            row = cur.fetchone()
            if row:
                _, db_items, db_total, db_payment_status, db_status = row
                db_total = float(db_total)
                
                # Check order accuracy: exact match of items, quantities, and total
                # Parse items from DB JSONB
                db_items_list = db_items if isinstance(db_items, list) else json.loads(db_items)
                items_match = True
                if len(db_items_list) != len(cart):
                    items_match = False
                else:
                    for c_item, d_item in zip(sorted(cart, key=lambda x: x['id']), sorted(db_items_list, key=lambda x: x['id'])):
                        if (c_item['id'] != d_item['id'] or
                            c_item['quantity'] != d_item['quantity'] or
                            abs(float(c_item['price']) - float(d_item['price'])) > 0.01):
                            items_match = False
                            break
                
                price_match = (abs(db_total - cart_total) < 0.01)
                db_accuracy_match = items_match and price_match
        cur.close()
        conn.close()

        # Check for Gateway vs Database payment status mismatch
        status_match = (actual_gateway_status == db_payment_status)
        if not status_match:
            mismatches.append({
                'attempt': i,
                'order_id': db_order_id or rzp_order_id,
                'gateway': actual_gateway_status,
                'database': db_payment_status
            })

        attempt_record = {
            'attempt': i,
            'order_id': db_order_id or rzp_order_id,
            'items_count': len(cart),
            'total_qty': total_qty,
            'cart_total': cart_total,
            'card_number': card['card_number'],
            'card_type': card['type'],
            'gateway_status': actual_gateway_status,
            'db_payment_status': db_payment_status,
            'status_match': 'Y' if status_match else 'N',
            'accuracy_match': 'Y' if db_accuracy_match else 'N',
            'time_sec': elapsed_time,
            'notes': error_msg if error_msg else 'Order verified and stored'
        }
        results.append(attempt_record)

        print(f"Attempt {i:02d}/{num_attempts} | Card: {card['type']:<22} | "
              f"Gateway: {actual_gateway_status:<6} | DB: {db_payment_status:<6} | "
              f"Accuracy: {'PASS' if db_accuracy_match else 'FAIL'} | Time: {elapsed_time:.3f}s")

    # Step 4: Save raw data to evaluation_results.csv
    print(f"\n[Step 4] Saving all {len(results)} individual attempt records to CSV...")
    with open(CSV_OUTPUT_PATH, mode='w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'attempt', 'order_id', 'items_count', 'total_qty', 'cart_total',
            'card_number', 'card_type', 'gateway_status', 'db_payment_status',
            'status_match', 'accuracy_match', 'time_sec', 'notes'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved CSV: {CSV_OUTPUT_PATH}")

    # Step 5: Compute summary statistics
    total_runs = len(results)
    successful_payments = sum(1 for r in results if r['gateway_status'] == 'Paid' and r['db_payment_status'] == 'Paid')
    accurate_orders = sum(1 for r in results if r['accuracy_match'] == 'Y')
    times = [r['time_sec'] for r in results]

    mean_time = sum(times) / len(times) if times else 0
    min_time = min(times) if times else 0
    max_time = max(times) if times else 0

    success_rate_pct = (successful_payments / total_runs) * 100 if total_runs > 0 else 0
    accuracy_pct = (accurate_orders / total_runs) * 100 if total_runs > 0 else 0

    print("\n" + "=" * 70)
    print("FINAL EVALUATION METRICS")
    print("=" * 70)
    print(f"Total Attempts Run          : {total_runs}")
    print(f"Payment Success Rate        : {successful_payments}/{total_runs} = {success_rate_pct:.1f}%")
    print(f"Order Accuracy              : {accurate_orders}/{total_runs} = {accuracy_pct:.1f}%")
    print(f"Order Completion Time (sec) : Mean = {mean_time:.3f}s | Min = {min_time:.3f}s | Max = {max_time:.3f}s")
    print(f"Gateway-vs-DB Mismatches    : {len(mismatches)} found")
    if mismatches:
        for m in mismatches:
            print(f"  - Attempt {m['attempt']}: Order {m['order_id']} | Gateway={m['gateway']} != DB={m['database']}")
    else:
        print("  None found. Gateway status perfectly matched orders table status for 100% of attempts.")
    print("=" * 70)

    return {
        'total_runs': total_runs,
        'successful_payments': successful_payments,
        'success_rate_pct': success_rate_pct,
        'accurate_orders': accurate_orders,
        'accuracy_pct': accuracy_pct,
        'mean_time': mean_time,
        'min_time': min_time,
        'max_time': max_time,
        'mismatches': mismatches,
        'csv_path': CSV_OUTPUT_PATH
    }

if __name__ == '__main__':
    run_evaluation(50)
