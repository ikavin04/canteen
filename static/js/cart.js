// Simple cart implementation using localStorage
// Cart structure: [{id, name, price, quantity}]

function getCart() {
    let c = localStorage.getItem('sc_cart');
    return c ? JSON.parse(c) : [];
}

function saveCart(cart) {
    localStorage.setItem('sc_cart', JSON.stringify(cart));
    updateCartCount();
}

function updateCartCount() {
    const cart = getCart();
    const count = cart.reduce((s, it) => s + it.quantity, 0);
    const el = document.getElementById('cart-count');
    if (el) el.textContent = count;
}

// Add to cart buttons
document.addEventListener('click', function(e) {
    const target = e.target;
    if (target.classList && target.classList.contains('add-to-cart')) {
        const id = parseInt(target.dataset.id);
        const name = target.dataset.name;
        const price = parseFloat(target.dataset.price);
        addToCart({id, name, price, quantity: 1});
        
        // Show notification if notification manager is available
        if (window.notificationManager) {
            notificationManager.showNotification(`${name} added to cart!`, 'success', 3000);
        }
        
        // show cart panel
        toggleCart(true);
    }
});

function addToCart(item) {
    const cart = getCart();
    const idx = cart.findIndex(c => c.id === item.id);
    if (idx > -1) {
        cart[idx].quantity += item.quantity;
    } else {
        cart.push(item);
    }
    saveCart(cart);
    renderCartItems();
}

function renderCartItems() {
    const container = document.getElementById('cartItems');
    if (!container) return;
    const cart = getCart();
    container.innerHTML = '';
    if (!cart.length) {
        container.innerHTML = '<p class="empty-cart">Your cart is empty</p>';
        document.getElementById('cartTotal').textContent = '₹0.00';
        return;
    }

    let total = 0;
    cart.forEach(item => {
        total += item.price * item.quantity;
        const row = document.createElement('div');
        row.className = 'cart-row';
        row.innerHTML = `
            <div class="cart-item-name">${item.name}</div>
            <div class="cart-item-qty">
                <button class="qty-btn" onclick="changeQty(${item.id}, -1)">-</button>
                <span>${item.quantity}</span>
                <button class="qty-btn" onclick="changeQty(${item.id}, 1)">+</button>
            </div>
            <div class="cart-item-price">₹${(item.price * item.quantity).toFixed(2)}</div>
            <button class="remove-item" onclick="removeItem(${item.id})">Remove</button>
        `;
        container.appendChild(row);
    });

    document.getElementById('cartTotal').textContent = `₹${total.toFixed(2)}`;
}

function changeQty(id, delta) {
    const cart = getCart();
    const idx = cart.findIndex(c => c.id === id);
    if (idx === -1) return;
    cart[idx].quantity = Math.max(1, cart[idx].quantity + delta);
    saveCart(cart);
    renderCartItems();
}

function removeItem(id) {
    let cart = getCart();
    cart = cart.filter(c => c.id !== id);
    saveCart(cart);
    renderCartItems();
}

function toggleCart(show) {
    const panel = document.getElementById('cartPanel');
    if (!panel) return;
    if (show === true) panel.classList.add('open');
    else panel.classList.toggle('open');
    renderCartItems();
}

function proceedToCheckout() {
    const cart = getCart();
    if (!cart.length) {
        if (window.notificationManager) {
            notificationManager.showNotification('Your cart is empty', 'warning');
        } else {
            alert('Your cart is empty');
        }
        return;
    }

    // Show loading notification
    if (window.notificationManager) {
        notificationManager.showNotification('Placing your order...', 'info');
    }

    // Send order to server (mock payment already considered paid)
    fetch('/user/place_order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart_items: cart })
    }).then(r => r.json()).then(data => {
        if (data.success) {
            // Clear cart and redirect to orders page
            localStorage.removeItem('sc_cart');
            updateCartCount();
            
            if (window.notificationManager) {
                // Show success notification
                notificationManager.showNotification(
                    `Order ${data.order_id} placed successfully! Total: ₹${data.total_amount.toFixed(2)}`, 
                    'success', 
                    7000
                );
                
                // Show browser notification
                notificationManager.showBrowserNotification(
                    'Smart Canteen - Order Confirmed',
                    `Order ${data.order_id} placed successfully. Transaction ID: ${data.transaction_id}`
                );
                
                setTimeout(() => {
                    window.location.href = '/user/orders';
                }, 2000);
            } else {
                alert(`Order ${data.order_id} placed successfully. Transaction ID: ${data.transaction_id}`);
                window.location.href = '/user/orders';
            }
        } else {
            if (window.notificationManager) {
                notificationManager.showNotification(
                    `Failed to place order: ${data.message || 'Unknown error'}`, 
                    'error'
                );
            } else {
                alert('Failed to place order: ' + (data.message || 'Unknown'));
            }
        }
    }).catch(err => {
        console.error(err);
        if (window.notificationManager) {
            notificationManager.showNotification('Network error while placing order', 'error');
        } else {
            alert('Network error while placing order');
        }
    });
}

// Init
updateCartCount();
renderCartItems();
