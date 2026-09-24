// Smart Canteen - Frontend API & State Client
// Configuration: dynamically adapt to same-origin or localhost:5000
const API_BASE_URL = (typeof window !== 'undefined' && window.BACKEND_URL)
    ? window.BACKEND_URL.replace(/\/+$/, '') + '/api'
    : (typeof window !== 'undefined' && (window.location.port === '5000' || !window.location.port && window.location.protocol.startsWith('http')))
        ? '/api'
        : (typeof window !== 'undefined' && window.location.hostname)
            ? `${window.location.protocol}//${window.location.hostname}:5000/api`
            : 'http://localhost:5000/api';

// Authentication & Request Helper
function getAuthHeaders() {
    const user = getCurrentUser();
    const headers = { 'Content-Type': 'application/json' };
    if (user && user.id) {
        headers['X-User-Id'] = String(user.id);
    }
    if (user && user.role) {
        headers['X-User-Role'] = String(user.role);
    }
    return headers;
}

async function apiFetch(endpoint, options = {}) {
    let url = endpoint;
    if (!url.startsWith('http')) {
        // Strip leading /api if endpoint starts with /api/
        let ep = endpoint;
        if (ep.startsWith('/api/')) {
            ep = ep.substring(4);
        }
        const cleanEndpoint = ep.startsWith('/') ? ep : '/' + ep;
        url = `${API_BASE_URL}${cleanEndpoint}`;
    }
    const config = {
        credentials: 'include',
        ...options,
        headers: {
            ...getAuthHeaders(),
            ...(options.headers || {})
        }
    };
    return fetch(url, config);
}

// Initialize data in localStorage
function initializeData() {
    if (!localStorage.getItem('smartCanteenCart')) {
        localStorage.setItem('smartCanteenCart', JSON.stringify([]));
    }
}

function initializeDemoAccounts() {
    // Demo accounts are maintained on PostgreSQL backend
}

// User Management Functions
async function registerUser(username, email, password, userType = 'Student') {
    try {
        const response = await apiFetch('/users/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password, user_type: userType })
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
        const response = await apiFetch('/users/login', {
            method: 'POST',
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

async function getAllUsers() {
    try {
        const response = await apiFetch('/users');
        if (response.status === 401 || response.status === 403) {
            if (window.location.pathname.includes('admin.html')) {
                localStorage.removeItem('smartCanteenCurrentUser');
                window.location.href = 'login.html';
            }
            return [];
        }
        const data = await response.json();
        if (data.success && Array.isArray(data.users)) {
            return data.users;
        }
        return [];
    } catch (error) {
        console.error('Error fetching users:', error);
        return [];
    }
}

function logout() {
    apiFetch('/users/logout', { method: 'POST' }).catch(() => {});
    localStorage.removeItem('smartCanteenCurrentUser');
    localStorage.removeItem('smartCanteenCart');
    window.location.href = 'login.html';
}

function getCurrentUser() {
    try {
        const currentUser = localStorage.getItem('smartCanteenCurrentUser');
        return currentUser ? JSON.parse(currentUser) : null;
    } catch (e) {
        return null;
    }
}

// Menu Management Functions
async function getMenu() {
    try {
        const response = await apiFetch('/menu');
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
        const response = await apiFetch(`/menu/${id}`);
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
        const response = await apiFetch('/menu', {
            method: 'POST',
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
        const response = await apiFetch(`/menu/${id}`, {
            method: 'PUT',
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
        const response = await apiFetch(`/menu/${id}`, {
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
        const response = await apiFetch(`/menu/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ availability: !menuItem.availability })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error toggling availability:', error);
        return { success: false, message: 'Network error. Please try again.' };
    }
}

// Cart Management Functions (localStorage for instant UX)
function getCart() {
    try {
        return JSON.parse(localStorage.getItem('smartCanteenCart') || '[]');
    } catch (e) {
        return [];
    }
}

function saveCart(cart) {
    localStorage.setItem('smartCanteenCart', JSON.stringify(cart));
    updateAllCartBadges();
}

function addToCart(item, quantity = 1) {
    if (!item) return { success: false, message: 'Invalid item' };
    const cart = getCart();
    const itemId = item.id;
    const existingItem = cart.find(i => i.id === itemId);
    const name = item.item_name || item.name || 'Item';
    const price = parseFloat(item.price) || 0;
    const imageUrl = item.image_url || '';

    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            id: itemId,
            name: name,
            price: price,
            quantity: quantity,
            image_url: imageUrl
        });
    }
    saveCart(cart);
    return { success: true, message: 'Item added to cart' };
}

async function addItemToCart(itemId, quantity = 1) {
    const menuItem = await getMenuItemById(itemId);
    if (!menuItem) {
        return { success: false, message: 'Item not found' };
    }
    if (!menuItem.availability) {
        return { success: false, message: 'Item is not available' };
    }
    return addToCart(menuItem, quantity);
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

// Chef AI RAG Recommendation Engine Client
async function getRagRecommendations(cartOrItem = null) {
    try {
        let body = {};
        if (Array.isArray(cartOrItem)) {
            body.cart = cartOrItem;
        } else if (cartOrItem && typeof cartOrItem === 'object') {
            body.item = cartOrItem;
            body.cart = getCart();
        } else {
            body.cart = getCart();
        }

        const response = await apiFetch('/recommendations', {
            method: 'POST',
            body: JSON.stringify(body)
        });
        const data = await response.json();
        if (data.success && Array.isArray(data.recommendations)) {
            return data.recommendations;
        }
        return [];
    } catch (error) {
        console.warn('RAG recommendations fetch error:', error);
        return [];
    }
}

// Order Management Functions
async function getAllOrders() {
    try {
        const response = await apiFetch('/orders?admin=true');
        if (response.status === 401 || response.status === 403) {
            if (window.location.pathname.includes('admin.html')) {
                localStorage.removeItem('smartCanteenCurrentUser');
                window.location.href = 'login.html';
            }
            return [];
        }
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
        const response = await apiFetch(`/orders?user_id=${currentUser.id}`);
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
        const response = await apiFetch('/checkout', {
            method: 'POST',
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
        const response = await apiFetch(`/orders/${orderId}/status`, {
            method: 'PATCH',
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
        const response = await apiFetch('/stats');
        if (response.status === 401 || response.status === 403) {
            if (window.location.pathname.includes('admin.html')) {
                localStorage.removeItem('smartCanteenCurrentUser');
                window.location.href = 'login.html';
            }
            return null;
        }
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

// UI Notification Helpers
function showTemporaryMessage(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    
    let iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
    if (type === 'success') {
        iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
    } else if (type === 'error') {
        iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
    } else if (type === 'warning') {
        iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
    }

    toast.innerHTML = `<span style="display: flex; align-items: center; flex-shrink: 0;">${iconSvg}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function showMessage(message, type = 'info') {
    const msgEl = document.getElementById('message');
    if (msgEl) {
        msgEl.className = `message ${type}`;
        msgEl.textContent = message;
        msgEl.classList.remove('hidden');
        setTimeout(() => {
            msgEl.classList.add('hidden');
        }, 4000);
    }
    showTemporaryMessage(message, type);
}

function updateAllCartBadges() {
    try {
        const cart = (typeof getCart === 'function') ? getCart() : [];
        const totalQty = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
        const badgeElements = document.querySelectorAll('#cartCount, #mobileCartCount, #drawerCartCount, .cart-badge');
        badgeElements.forEach(el => {
            el.textContent = totalQty;
        });
    } catch (e) {
        console.error('Error updating cart badges:', e);
    }
}

function initializeMobileNav() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    if (!hamburger || !navLinks) return;

    // Ensure backdrop element exists
    let backdrop = document.querySelector('.nav-backdrop');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.className = 'nav-backdrop';
        backdrop.id = 'navBackdrop';
        document.body.appendChild(backdrop);
    }

    function openMobileNav() {
        hamburger.classList.add('active');
        hamburger.setAttribute('aria-expanded', 'true');
        navLinks.classList.add('active');
        backdrop.classList.add('active');
        document.body.classList.add('nav-open');
    }

    function closeMobileNav() {
        hamburger.classList.remove('active');
        hamburger.setAttribute('aria-expanded', 'false');
        navLinks.classList.remove('active');
        backdrop.classList.remove('active');
        document.body.classList.remove('nav-open');
    }

    function toggleMobileNav(e) {
        if (e) e.stopPropagation();
        if (navLinks.classList.contains('active')) {
            closeMobileNav();
        } else {
            openMobileNav();
        }
    }

    // Remove existing event listener duplicates if re-initialized
    hamburger.onclick = toggleMobileNav;
    backdrop.onclick = closeMobileNav;

    // Close button inside drawer
    const closeBtn = navLinks.querySelector('.drawer-close-btn, .nav-close-btn');
    if (closeBtn) {
        closeBtn.onclick = closeMobileNav;
    }

    // Close drawer when clicking any link
    navLinks.querySelectorAll('a').forEach(link => {
        link.onclick = () => {
            closeMobileNav();
        };
    });

    // Close on Escape key press
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && navLinks.classList.contains('active')) {
            closeMobileNav();
        }
    });

    // Wire up user details in drawer if present
    const currentUser = (typeof getCurrentUser === 'function') ? getCurrentUser() : null;
    if (currentUser) {
        const drawerName = navLinks.querySelector('#drawerUserName');
        if (drawerName) drawerName.textContent = currentUser.username || 'User';
        const drawerRole = navLinks.querySelector('#drawerUserRole');
        if (drawerRole) drawerRole.textContent = currentUser.role || 'Student';
        const drawerAvatar = navLinks.querySelector('#drawerUserAvatar');
        if (drawerAvatar && currentUser.username) {
            drawerAvatar.textContent = currentUser.username.charAt(0).toUpperCase();
        }
    }

    updateAllCartBadges();
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
    updateAllCartBadges();
});

initializeData();
initializeDemoAccounts();

// Global exports
window.API_BASE_URL = API_BASE_URL;
window.apiFetch = apiFetch;
window.getAuthHeaders = getAuthHeaders;
window.addToCart = addToCart;
window.addItemToCart = addItemToCart;
window.getCart = getCart;
window.saveCart = saveCart;
window.clearCart = clearCart;
window.updateItemQuantity = updateItemQuantity;
window.removeItemFromCart = removeItemFromCart;
window.getCurrentUser = getCurrentUser;
window.logout = logout;
window.registerUser = registerUser;
window.loginUser = loginUser;
window.getAllUsers = getAllUsers;
window.getMenu = getMenu;
window.getMenuItemById = getMenuItemById;
window.addMenuItem = addMenuItem;
window.updateMenuItem = updateMenuItem;
window.deleteMenuItemById = deleteMenuItemById;
window.toggleMenuItemAvailability = toggleMenuItemAvailability;
window.getAllOrders = getAllOrders;
window.getUserOrders = getUserOrders;
window.placeOrder = placeOrder;
window.updateOrderStatus = updateOrderStatusById;
window.updateOrderStatusById = updateOrderStatusById;
window.getStats = getStats;
window.validateEmail = validateEmail;
window.validatePassword = validatePassword;
window.showMessage = showMessage;
window.showTemporaryMessage = showTemporaryMessage;
window.initializeMobileNav = initializeMobileNav;
window.updateAllCartBadges = updateAllCartBadges;
