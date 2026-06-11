// static/js/notifications.js
// Complete Notification System

class NotificationSystem {
    constructor() {
        this.pollingInterval = null;
        this.pollingTime = 30000; // 30 seconds
        this.notificationCount = 0;
        this.lastCheckTime = null;
        
        this.initialize();
    }
    
    initialize() {
        this.setupEventListeners();
        this.startPolling();
        this.requestNotificationPermission();
        this.updateUnreadCount();
    }
    
    setupEventListeners() {
        // Notification bell click
        const bellIcon = document.getElementById('notificationBell');
        if (bellIcon) {
            bellIcon.addEventListener('click', () => this.toggleNotificationPanel());
        }
        
        // Mark all as read button
        const markAllBtn = document.getElementById('markAllRead');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => this.markAllAsRead());
        }
        
        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('notificationPanel');
            const bell = document.getElementById('notificationBell');
            if (panel && bell && !panel.contains(e.target) && !bell.contains(e.target)) {
                panel.classList.remove('show');
            }
        });
    }
    
    startPolling() {
        if (this.pollingInterval) clearInterval(this.pollingInterval);
        
        this.pollingInterval = setInterval(() => {
            this.checkNewNotifications();
        }, this.pollingTime);
        
        // Initial check
        this.checkNewNotifications();
    }
    
    async checkNewNotifications() {
        try {
            const response = await fetch('/notifications/api/unread/');
            const data = await response.json();
            
            if (data.count > this.notificationCount) {
                this.playNotificationSound();
                this.showBrowserNotification(data.count);
                this.updateNotificationBadge(data.count);
                this.renderNotifications(data.notifications);
            }
            
            this.notificationCount = data.count;
            this.lastCheckTime = new Date();
            
        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    }
    
    async updateUnreadCount() {
        try {
            const response = await fetch('/notifications/api/unread/');
            const data = await response.json();
            this.updateNotificationBadge(data.count);
            this.renderNotifications(data.notifications);
        } catch (error) {
            console.error('Error updating unread count:', error);
        }
    }
    
    updateNotificationBadge(count) {
        const badge = document.getElementById('notificationCount');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'inline-block';
                badge.classList.add('animate-pulse');
                setTimeout(() => badge.classList.remove('animate-pulse'), 1000);
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    async renderNotifications(notifications) {
        const container = document.getElementById('notificationList');
        if (!container) return;
        
        if (!notifications || notifications.length === 0) {
            container.innerHTML = `
                <div class="notification-empty text-center p-4">
                    <i class="fas fa-bell-slash fa-2x text-muted mb-2"></i>
                    <p class="text-muted mb-0">No new notifications</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = notifications.map(notif => `
            <div class="notification-item" data-id="${notif.id}" onclick="notificationSystem.markAsRead(${notif.id})">
                <div class="d-flex">
                    <div class="notification-icon flex-shrink-0">
                        <i class="fas ${this.getNotificationIcon(notif.type)}"></i>
                    </div>
                    <div class="flex-grow-1 ms-3">
                        <div class="d-flex justify-content-between align-items-start">
                            <strong class="notification-title">${this.escapeHtml(notif.title)}</strong>
                            <small class="text-muted">${this.timeAgo(notif.created_at)}</small>
                        </div>
                        <p class="notification-message mb-0">${this.escapeHtml(notif.message)}</p>
                        ${notif.link ? `<a href="${notif.link}" class="notification-link small">View Details →</a>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    async markAsRead(id) {
        try {
            const response = await fetch(`/notifications/${id}/mark-read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            if (data.success) {
                // Remove notification from list with animation
                const element = document.querySelector(`.notification-item[data-id="${id}"]`);
                if (element) {
                    element.style.opacity = '0';
                    setTimeout(() => {
                        element.remove();
                        this.updateUnreadCount();
                    }, 300);
                }
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            const response = await fetch('/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.notificationCount = 0;
                this.updateNotificationBadge(0);
                this.renderNotifications([]);
                this.showToast('All notifications marked as read', 'success');
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
        }
    }
    
    toggleNotificationPanel() {
        const panel = document.getElementById('notificationPanel');
        if (panel) {
            panel.classList.toggle('show');
            if (panel.classList.contains('show')) {
                this.loadNotifications();
            }
        }
    }
    
    async loadNotifications() {
        try {
            const response = await fetch('/notifications/api/all/');
            const data = await response.json();
            this.renderAllNotifications(data.notifications);
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }
    
    renderAllNotifications(notifications) {
        const container = document.getElementById('allNotificationsList');
        if (!container) return;
        
        if (notifications.length === 0) {
            container.innerHTML = '<div class="text-center p-4 text-muted">No notifications found</div>';
            return;
        }
        
        container.innerHTML = notifications.map(notif => `
            <tr class="${!notif.is_read ? 'table-active' : ''}">
                <td>
                    <i class="fas ${this.getNotificationIcon(notif.type)} fa-lg"></i>
                </td>
                <td>
                    <strong>${this.escapeHtml(notif.title)}</strong><br>
                    <small class="text-muted">${this.escapeHtml(notif.message)}</small>
                </td>
                <td>${this.timeAgo(notif.created_at)}</td>
                <td>
                    ${!notif.is_read ? 
                        `<button onclick="notificationSystem.markAsRead(${notif.id})" class="btn btn-sm btn-primary">
                            Mark Read
                        </button>` : 
                        '<span class="badge bg-success">Read</span>'
                    }
                </td>
            </tr>
        `).join('');
    }
    
    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    showBrowserNotification(count) {
        if (!('Notification' in window) || Notification.permission !== 'granted') return;
        
        new Notification('New Notifications', {
            body: `You have ${count} new notification${count > 1 ? 's' : ''}`,
            icon: '/static/assets/logo.png',
            badge: '/static/assets/badge.png',
            vibrate: [200, 100, 200]
        });
    }
    
    playNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.2;
            audio.play().catch(e => console.log('Audio not supported'));
        } catch (e) {
            console.log('Audio not supported');
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) {
            const div = document.createElement('div');
            div.id = 'toastContainer';
            div.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(div);
        }
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type} border-0 mb-2`;
        toastEl.setAttribute('role', 'alert');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        document.getElementById('toastContainer').appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }
    
    getNotificationIcon(type) {
        const icons = {
            'TASK_ASSIGNED': 'fa-tasks text-primary',
            'TASK_UPDATED': 'fa-edit text-warning',
            'TASK_COMPLETED': 'fa-check-circle text-success',
            'DEADLINE_REMINDER': 'fa-clock text-danger',
            'PROJECT_UPDATED': 'fa-project-diagram text-info',
            'FILE_UPLOADED': 'fa-file-upload text-secondary',
            'TEAM_MESSAGE': 'fa-comment text-success',
            'COMMENT_ADDED': 'fa-comment-dots text-info'
        };
        return icons[type] || 'fa-bell text-secondary';
    }
    
    timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        const intervals = {
            year: 31536000,
            month: 2592000,
            week: 604800,
            day: 86400,
            hour: 3600,
            minute: 60
        };
        
        for (const [unit, secondsInUnit] of Object.entries(intervals)) {
            const interval = Math.floor(seconds / secondsInUnit);
            if (interval >= 1) {
                return interval === 1 ? `1 ${unit} ago` : `${interval} ${unit}s ago`;
            }
        }
        return 'just now';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize notification system
let notificationSystem;

document.addEventListener('DOMContentLoaded', function() {
    notificationSystem = new NotificationSystem();
    window.notificationSystem = notificationSystem;
});