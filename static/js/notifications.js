// Enhanced notification system for Smart Canteen
class NotificationManager {
    constructor() {
        this.init();
    }

    init() {
        // Request notification permission on page load
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        // Create notification container if it doesn't exist
        this.createNotificationContainer();
        
        // Start order status polling for users
        if (window.location.pathname.includes('/user/orders') || 
            window.location.pathname.includes('/user/dashboard')) {
            this.startOrderStatusPolling();
        }
    }

    createNotificationContainer() {
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
    }

    // Show in-app notification
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
        `;
        
        const container = document.getElementById('notification-container');
        container.appendChild(notification);
        
        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
        
        // Add slide-in animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
    }

    // Show browser notification (requires permission)
    showBrowserNotification(title, message, icon = null) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: icon || '/static/favicon.ico',
                badge: '/static/favicon.ico'
            });
        }
    }

    // Poll for order status updates
    startOrderStatusPolling() {
        // Get current user's recent orders and poll for status changes
        const userId = this.getCurrentUserId();
        if (!userId) return;

        this.pollInterval = setInterval(() => {
            this.checkOrderStatusUpdates(userId);
        }, 15000); // Check every 15 seconds
    }

    getCurrentUserId() {
        // Extract user ID from page or session (you might need to adjust this)
        const userElement = document.querySelector('[data-user-id]');
        return userElement ? userElement.dataset.userId : null;
    }

    async checkOrderStatusUpdates(userId) {
        try {
            const response = await fetch(`/api/user/${userId}/recent_orders`);
            const orders = await response.json();
            
            // Check if any orders have updated status
            orders.forEach(order => {
                const lastKnownStatus = localStorage.getItem(`order_${order.id}_status`);
                if (lastKnownStatus && lastKnownStatus !== order.status) {
                    this.notifyOrderStatusChange(order);
                }
                localStorage.setItem(`order_${order.id}_status`, order.status);
            });
        } catch (error) {
            console.error('Failed to check order status:', error);
        }
    }

    notifyOrderStatusChange(order) {
        const statusMessages = {
            'Preparing': `Your order #${order.id} is now being prepared!`,
            'Ready': `Your order #${order.id} is ready for pickup!`,
            'Completed': `Your order #${order.id} has been completed.`,
            'Cancelled': `Your order #${order.id} has been cancelled.`
        };

        const message = statusMessages[order.status];
        if (message) {
            this.showNotification(message, 'success');
            this.showBrowserNotification('Smart Canteen - Order Update', message);
            
            // Play notification sound
            this.playNotificationSound();
        }
    }

    playNotificationSound() {
        // Create a simple notification sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    }

    // Clean up when leaving page
    destroy() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
    }
}

// Initialize notification manager
const notificationManager = new NotificationManager();

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    notificationManager.destroy();
});

// Enhanced cart notifications
function addToCartWithNotification(item) {
    addToCart(item);
    notificationManager.showNotification(`${item.name} added to cart!`, 'success', 3000);
}

// Enhanced order placement
function proceedToCheckoutWithNotifications() {
    const cart = getCart();
    if (!cart.length) {
        notificationManager.showNotification('Your cart is empty', 'warning');
        return;
    }

    // Show loading notification
    notificationManager.showNotification('Placing your order...', 'info');

    fetch('/user/place_order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart_items: cart })
    }).then(r => r.json()).then(data => {
        if (data.success) {
            localStorage.removeItem('sc_cart');
            updateCartCount();
            
            // Show success notification
            notificationManager.showNotification(
                `Order placed successfully! Transaction ID: ${data.transaction_id}`, 
                'success', 
                7000
            );
            
            // Show browser notification
            notificationManager.showBrowserNotification(
                'Smart Canteen - Order Confirmed',
                `Your order has been placed successfully. Transaction ID: ${data.transaction_id}`
            );
            
            setTimeout(() => {
                window.location.href = '/user/orders';
            }, 2000);
        } else {
            notificationManager.showNotification(
                `Failed to place order: ${data.message || 'Unknown error'}`, 
                'error'
            );
        }
    }).catch(err => {
        console.error(err);
        notificationManager.showNotification('Network error while placing order', 'error');
    });
}