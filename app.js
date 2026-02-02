// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Initialize data
function initializeData() {
    // Cart is managed in localStorage for better UX
    if (!localStorage.getItem('smartCanteenCart')) {
        localStorage.setItem('smartCanteenCart', JSON.stringify([]));
    }
}

function initializeDemoAccounts() {
    // Demo accounts are now managed by the database
    // This function is kept for backward compatibility
}

// User Management Functions
async function registerUser(username, email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await response.json();
        if (data.success) {
            localStorage.setItem('smartCanteenCurrentUser', JSON.stringify(data.user));
            return { success: true, message: 'Registration successful' };
        } else {
            return { success: false, message: data.message || 'Registration failed' };
        }
    } catch (error) {
        console.error('Registration error:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
}

async function loginUser(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (data.success) {
            localStorage.setItem('smartCanteenCurrentUser', JSON.stringify(data.user));
            return { success: true, message: 'Login successful', user: data.user };
        } else {
            return { success: false, message: data.message || 'Login failed' };
        }
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
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

// Menu Management Functions
async function getMenu() {
    try {
        const response = await fetch(`${API_BASE_URL}/menu`);
        const data = await response.json();
        if (data.success) {
            return data.menu || [];
        }
        return [];
    } catch (error) {
        console.error('Error fetching menu:', error);
        return [];
    }
}

async function getMenuItemById(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/menu/${id}`);
        const data = await response.json();
        if (data.success) {
            return data.item;
        }
        return null;
    } catch (error) {
        console.error('Error fetching menu item:', error);
        return null;
    }
}

async function addMenuItem(itemData) {
    try {
        const response = await fetch(`${API_BASE_URL}/menu`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(itemData)
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error adding menu item:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
}

async function updateMenuItem(id, itemData) {
    try {
        const response = await fetch(`${API_BASE_URL}/menu/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(itemData)
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error updating menu item:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
}

async function deleteMenuItemById(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/menu/${id}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error deleting menu item:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
}

async function toggleMenuItemAvailability(id) {
    try {
        const menuItem = await getMenuItemById(id);
        if (!menuItem) {
            return { success: false, message: 'Item not found' };
        }
        const response = await fetch(`${API_BASE_URL}/menu/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ availability: !menuItem.availability })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error toggling availability:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
}
// Cart Management Functions (localStorage for better UX)
function getCart() {
    return JSON.parse(localStorage.getItem('smartCanteenCart') || '[]');
}

function saveCart(cart) {
    localStorage.setItem('smartCanteenCart', JSON.stringify(cart));
}

async function addItemToCart(itemId, quantity = 1) {
    const menuItem = await getMenuItemById(itemId);
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

// Order Management Functions
async function getAllOrders() {
    try {
        const response = await fetch(`${API_BASE_URL}/orders?admin=true`);
        const data = await response.json();
        if (data.success && Array.isArray(data.orders)) {
            return data.orders;
        }
        return [];
    } catch (error) {
        console.error('Error fetching orders:', error);
        return [];
    }
}

async function getUserOrders() {
    const currentUser = getCurrentUser();
    if (!currentUser) return [];
    try {
        const response = await fetch(`${API_BASE_URL}/orders?user_id=${currentUser.id}`);
        const data = await response.json();
        if (data.success && Array.isArray(data.orders)) {
            return data.orders;
        }
        return [];
    } catch (error) {
        console.error('Error fetching user orders:', error);
        return [];
    }
}

async function placeOrder(cartItems, paymentMethod = 'UPI') {
    if (!cartItems || cartItems.length === 0) {
        return { success: false, message: 'Cart is empty' };
    }
    const currentUser = getCurrentUser();
    if (!currentUser) {
        return { success: false, message: 'Please login to place order' };
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/checkout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cart: cartItems,
                payment_method: paymentMethod,
                user: currentUser
            })
        });
        const data = await response.json();
        if (data.success) {
            clearCart();
        }
        return data;
    } catch (error) {
        console.error('Error placing order:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
}

async function updateOrderStatusById(orderId, newStatus) {
    try {
        const response = await fetch(`${API_BASE_URL}/orders/${orderId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error updating order status:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
}

// Statistics Functions
async function getStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        if (data.success) {
            return data.stats;
        }
        return null;
    } catch (error) {
        console.error('Error fetching stats:', error);
        return null;
    }
}
// UI Helper Functions
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

// Validation helpers
function validateEmail(email) {
    if (!email || typeof email !== 'string') return false;
    email = email.trim();
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!re.test(email)) return false;
    const localPart = email.split('@')[0] || '';
    if (/^\d+$/.test(localPart)) return false;
    return true;
}

function validatePassword(password) {
    if (!password || typeof password !== 'string') return false;
    return password.length >= 6;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeMobileNav();
    initializeTouchControls();
});

initializeData();
initializeDemoAccounts();

// Expose functions for pages that rely on them
window.validateEmail = validateEmail;
window.validatePassword = validatePassword;


