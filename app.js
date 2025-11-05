function initializeData() {
    if (!localStorage.getItem('smartCanteenMenu')) {
        const sampleMenu = [
            {
                id: 1,
                item_name: 'Chicken Burger',
                description: 'Grilled chicken patty with lettuce and tomato',
                price: 120.00,
                category: 'Main Course',
                availability: true
            },
            {
                id: 2,
                item_name: 'Vegetable Sandwich',
                description: 'Fresh vegetables with mayo',
                price: 80.00,
                category: 'Snacks',
                availability: true
            },
            {
                id: 3,
                item_name: 'Coffee',
                description: 'Hot brewed coffee',
                price: 30.00,
                category: 'Beverages',
                availability: true
            },
            {
                id: 4,
                item_name: 'Tea',
                description: 'Indian masala tea',
                price: 20.00,
                category: 'Beverages',
                availability: true
            },
            {
                id: 5,
                item_name: 'Pasta',
                description: 'Italian style pasta with tomato sauce',
                price: 150.00,
                category: 'Main Course',
                availability: true
            },
            {
                id: 6,
                item_name: 'French Fries',
                description: 'Crispy golden fries',
                price: 60.00,
                category: 'Snacks',
                availability: true
            },
            {
                id: 7,
                item_name: 'Fruit Juice',
                description: 'Fresh mixed fruit juice',
                price: 40.00,
                category: 'Beverages',
                availability: true
            },
            {
                id: 8,
                item_name: 'Biryani',
                description: 'Aromatic basmati rice with spices',
                price: 180.00,
                category: 'Main Course',
                availability: true
            }
        ];
        localStorage.setItem('smartCanteenMenu', JSON.stringify(sampleMenu));
    }
    if (!localStorage.getItem('smartCanteenCart')) {
        localStorage.setItem('smartCanteenCart', JSON.stringify([]));
    }
    if (!localStorage.getItem('smartCanteenOrders')) {
        localStorage.setItem('smartCanteenOrders', JSON.stringify([]));
    }
}
function initializeDemoAccounts() {
    if (!localStorage.getItem('smartCanteenUsers')) {
        const demoUsers = [
            {
                id: 1,
                username: 'admin',
                email: 'admin@canteen.com',
                password: 'admin123',
                role: 'admin',
                created_at: new Date().toISOString()
            },
            {
                id: 2,
                username: 'student1',
                email: 'student1@college.edu',
                password: 'password123',
                role: 'user',
                created_at: new Date().toISOString()
            }
        ];
        localStorage.setItem('smartCanteenUsers', JSON.stringify(demoUsers));
    }
}
function registerUser(username, email, password) {
    const users = getAllUsers();
    if (users.find(user => user.username === username)) {
        return { success: false, message: 'Username already exists' };
    }
    if (users.find(user => user.email === email)) {
        return { success: false, message: 'Email already registered' };
    }
    const newUser = {
        id: Math.max(...users.map(u => u.id), 0) + 1,
        username,
        email,
        password,
        role: 'user',
        created_at: new Date().toISOString()
    };
    users.push(newUser);
    localStorage.setItem('smartCanteenUsers', JSON.stringify(users));
    return { success: true, message: 'Registration successful' };
}
function loginUser(username, password) {
    const users = getAllUsers();
    const user = users.find(u => u.username === username && u.password === password);
    if (!user) {
        return { success: false, message: 'Invalid username or password' };
    }
    localStorage.setItem('smartCanteenCurrentUser', JSON.stringify(user));
    return { success: true, message: 'Login successful', user };
}
function logout() {
    localStorage.removeItem('smartCanteenCurrentUser');
    localStorage.removeItem('smartCanteenCart');
    window.location.href = 'login.html';
}
function getCurrentUser() {
    const currentUser = localStorage.getItem('smartCanteenCurrentUser');
    return currentUser ? JSON.parse(currentUser) : null;
}
function getAllUsers() {
    return JSON.parse(localStorage.getItem('smartCanteenUsers') || '[]');
}
function getUserById(userId) {
    const users = getAllUsers();
    return users.find(user => user.id === userId);
}
function getMenu() {
    return JSON.parse(localStorage.getItem('smartCanteenMenu') || '[]');
}
function saveMenu(menu) {
    localStorage.setItem('smartCanteenMenu', JSON.stringify(menu));
}
function getMenuItemById(id) {
    const menu = getMenu();
    return menu.find(item => item.id === id);
}
function addMenuItem(itemData) {
    const menu = getMenu();
    const newId = Math.max(...menu.map(item => item.id), 0) + 1;
    const newItem = {
        id: newId,
        item_name: itemData.item_name,
        description: itemData.description || '',
        price: parseFloat(itemData.price),
        category: itemData.category,
        availability: itemData.availability !== false
    };
    menu.push(newItem);
    saveMenu(menu);
    return { success: true, message: 'Menu item added successfully' };
}
function updateMenuItem(id, itemData) {
    const menu = getMenu();
    const itemIndex = menu.findIndex(item => item.id === id);
    if (itemIndex === -1) {
        return { success: false, message: 'Item not found' };
    }
    menu[itemIndex] = {
        ...menu[itemIndex],
        item_name: itemData.item_name,
        description: itemData.description || '',
        price: parseFloat(itemData.price),
        category: itemData.category,
        availability: itemData.availability !== false
    };
    saveMenu(menu);
    return { success: true, message: 'Menu item updated successfully' };
}
function deleteMenuItemById(id) {
    const menu = getMenu();
    const updatedMenu = menu.filter(item => item.id !== id);
    if (menu.length === updatedMenu.length) {
        return { success: false, message: 'Item not found' };
    }
    saveMenu(updatedMenu);
    return { success: true, message: 'Menu item deleted successfully' };
}
function toggleMenuItemAvailability(id) {
    const menu = getMenu();
    const item = menu.find(item => item.id === id);
    if (!item) {
        return { success: false, message: 'Item not found' };
    }
    item.availability = !item.availability;
    saveMenu(menu);
    return { success: true, message: 'Availability updated successfully' };
}
function getCart() {
    return JSON.parse(localStorage.getItem('smartCanteenCart') || '[]');
}
function saveCart(cart) {
    localStorage.setItem('smartCanteenCart', JSON.stringify(cart));
}
function addItemToCart(itemId, quantity = 1) {
    const menuItem = getMenuItemById(itemId);
    if (!menuItem) {
        return { success: false, message: 'Item not found' };
    }
    if (!menuItem.availability) {
        return { success: false, message: 'Item is not available' };
    }
    const cart = getCart();
    const existingItem = cart.find(item => item.id === itemId);
    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            id: menuItem.id,
            name: menuItem.item_name,
            price: menuItem.price,
            quantity: quantity
        });
    }
    saveCart(cart);
    return { success: true, message: 'Item added to cart' };
}
function updateItemQuantity(itemId, change) {
    const cart = getCart();
    const item = cart.find(item => item.id === itemId);
    if (!item) {
        return { success: false, message: 'Item not found in cart' };
    }
    item.quantity += change;
    if (item.quantity <= 0) {
        return removeItemFromCart(itemId);
    }
    saveCart(cart);
    return { success: true, message: 'Quantity updated' };
}
function removeItemFromCart(itemId) {
    const cart = getCart();
    const updatedCart = cart.filter(item => item.id !== itemId);
    saveCart(updatedCart);
    return { success: true, message: 'Item removed from cart' };
}
function clearCart() {
    localStorage.setItem('smartCanteenCart', JSON.stringify([]));
}
function getAllOrders() {
    return JSON.parse(localStorage.getItem('smartCanteenOrders') || '[]');
}
function getUserOrders() {
    const currentUser = getCurrentUser();
    if (!currentUser) return [];
    const orders = getAllOrders();
    return orders.filter(order => order.user_id === currentUser.id);
}
function saveOrders(orders) {
    localStorage.setItem('smartCanteenOrders', JSON.stringify(orders));
}
function generateOrderId() {
    return 'ORD-' + Math.random().toString(36).substr(2, 6).toUpperCase();
}
function generateTransactionId() {
    return 'TXN' + Math.random().toString(36).substr(2, 8).toUpperCase();
}
function placeOrder(cartItems, paymentMethod = 'UPI') {
    if (!cartItems || cartItems.length === 0) {
        return { success: false, message: 'Cart is empty' };
    }
    const currentUser = getCurrentUser();
    if (!currentUser) {
        return { success: false, message: 'Please login to place order' };
    }
    const orders = getAllOrders();
    const orderId = generateOrderId();
    const transactionId = generateTransactionId();
    const totalAmount = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const newOrder = {
        id: orders.length + 1,
        order_id: orderId,
        user_id: currentUser.id,
        items: cartItems.map(item => ({
            id: item.id,
            name: item.name,
            price: item.price,
            quantity: item.quantity
        })),
        total_amount: totalAmount,
        status: 'Uncompleted',
        payment_method: paymentMethod,
        payment_status: 'Paid',
        transaction_id: transactionId,
        timestamp: new Date().toISOString()
    };
    orders.push(newOrder);
    saveOrders(orders);
    return { 
        success: true, 
        message: 'Order placed successfully',
        orderId: orderId,
        transactionId: transactionId,
        totalAmount: totalAmount
    };
}
function updateOrderStatusById(orderId, newStatus) {
    const orders = getAllOrders();
    const order = orders.find(order => order.order_id === orderId);
    if (!order) {
        return { success: false, message: 'Order not found' };
    }
    order.status = newStatus;
    if (newStatus === 'Ready') {
        order.ready_at = new Date().toISOString();
    } else if (newStatus === 'Completed') {
        order.completed_at = new Date().toISOString();
    }
    saveOrders(orders);
    return { success: true, message: 'Order status updated successfully' };
}
function showTemporaryMessage(message, type) {
    const messageEl = document.createElement('div');
    messageEl.className = `temp-message ${type}`;
    messageEl.textContent = message;
    messageEl.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 6px;
        color: white;
        z-index: 10000;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease-out;
    `;
    if (type === 'success') {
        messageEl.style.backgroundColor = '#28a745';
    } else if (type === 'error') {
        messageEl.style.backgroundColor = '#dc3545';
    } else if (type === 'warning') {
        messageEl.style.backgroundColor = '#ffc107';
        messageEl.style.color = '#000';
    } else {
        messageEl.style.backgroundColor = '#17a2b8';
    }
    document.body.appendChild(messageEl);
    setTimeout(() => {
        messageEl.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => messageEl.remove(), 300);
    }, 3000);
}
function initializeMobileNav() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navLinks.classList.toggle('active');
        });
        document.addEventListener('click', (e) => {
            if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
                hamburger.classList.remove('active');
                navLinks.classList.remove('active');
            }
        });
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navLinks.classList.remove('active');
            });
        });
    }
}
function initializeTouchControls() {
    document.addEventListener('touchstart', (e) => {
        if (e.target.classList.contains('quantity-btn')) {
            e.target.style.transform = 'scale(0.95)';
        }
    });
    document.addEventListener('touchend', (e) => {
        if (e.target.classList.contains('quantity-btn')) {
            e.target.style.transform = 'scale(1)';
        }
    });
}
document.addEventListener('DOMContentLoaded', () => {
    initializeMobileNav();
    initializeTouchControls();
});
initializeData();
initializeDemoAccounts();
