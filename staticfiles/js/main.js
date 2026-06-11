// static/js/main.js
// Complete Project Management System JavaScript

// ============================================
// 1. DOM Ready Handler
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadNotifications();
    setupFormValidation();
    setupSearchFilters();
    setupDarkMode();
    setupSidebar();
    setupTooltips();
});

// ============================================
// 2. Application Initialization
// ============================================
function initializeApp() {
    // Set current year in footer
    const yearElement = document.getElementById('currentYear');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
    
    // Initialize CSRF token for all AJAX requests
    setupCSRFToken();
    
    // Start auto-refresh for notifications
    startNotificationPolling();
    
    // Initialize dashboard charts if on dashboard page
    if (document.getElementById('dashboardCharts')) {
        initializeDashboardCharts();
    }
    
    // Initialize date pickers
    initializeDatePickers();
}

// ============================================
// 3. CSRF Token Setup for AJAX
// ============================================
function setupCSRFToken() {
    const csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
}

function getCookie(name) {
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

// ============================================
// 4. Notification System
// ============================================
let notificationInterval;

function startNotificationPolling() {
    if (notificationInterval) clearInterval(notificationInterval);
    notificationInterval = setInterval(loadNotifications, 30000); // every 30 seconds
}

function loadNotifications() {
    fetch('/notifications/api/unread/')
        .then(response => response.json())
        .then(data => {
            updateNotificationBadge(data.count);
            if (data.count > 0 && document.getElementById('notificationDropdown')) {
                renderNotifications(data.notifications);
            }
        })
        .catch(error => console.error('Error loading notifications:', error));
}

function updateNotificationBadge(count) {
    const badge = document.getElementById('notificationCount');
    if (badge) {
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}

function renderNotifications(notifications) {
    const container = document.getElementById('notificationList');
    if (!container) return;
    
    if (notifications.length === 0) {
        container.innerHTML = '<div class="dropdown-item text-muted">No new notifications</div>';
        return;
    }
    
    container.innerHTML = notifications.map(notif => `
        <div class="notification-item dropdown-item" data-id="${notif.id}" onclick="markNotificationRead(${notif.id})">
            <div class="d-flex align-items-start">
                <div class="notification-icon me-2">
                    <i class="fas ${getNotificationIcon(notif.type)}"></i>
                </div>
                <div class="flex-grow-1">
                    <strong>${escapeHtml(notif.title)}</strong>
                    <p class="small mb-0">${escapeHtml(notif.message)}</p>
                    <small class="text-muted">${timeAgo(notif.created_at)}</small>
                </div>
            </div>
        </div>
    `).join('');
}

function getNotificationIcon(type) {
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

function markNotificationRead(id) {
    fetch(`/notifications/${id}/mark-read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadNotifications();
        }
    })
    .catch(error => console.error('Error marking notification:', error));
}

// ============================================
// 5. Form Validation
// ============================================
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation for inputs
    document.querySelectorAll('input, select, textarea').forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }
}

// ============================================
// 6. Search and Filters
// ============================================
function setupSearchFilters() {
    // Auto-submit search on input with delay
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                submitSearchForm();
            }, 500);
        });
    }
    
    // Filter change listeners
    document.querySelectorAll('.filter-select').forEach(select => {
        select.addEventListener('change', function() {
            submitSearchForm();
        });
    });
}

function submitSearchForm() {
    const form = document.getElementById('filterForm');
    if (form) {
        form.submit();
    }
}

// ============================================
// 7. Dark Mode Toggle
// ============================================
function setupDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (!darkModeToggle) return;
    
    // Check for saved preference
    const isDarkMode = localStorage.getItem('darkMode') === 'enabled';
    if (isDarkMode) {
        enableDarkMode();
        darkModeToggle.checked = true;
    }
    
    darkModeToggle.addEventListener('change', function() {
        if (this.checked) {
            enableDarkMode();
            localStorage.setItem('darkMode', 'enabled');
        } else {
            disableDarkMode();
            localStorage.setItem('darkMode', 'disabled');
        }
    });
}

function enableDarkMode() {
    document.body.classList.add('dark-mode');
    document.documentElement.setAttribute('data-theme', 'dark');
}

function disableDarkMode() {
    document.body.classList.remove('dark-mode');
    document.documentElement.removeAttribute('data-theme');
}

// ============================================
// 8. Sidebar Collapse
// ============================================
function setupSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.body.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebarCollapsed', 
                document.body.classList.contains('sidebar-collapsed'));
        });
        
        // Restore saved state
        const savedState = localStorage.getItem('sidebarCollapsed') === 'true';
        if (savedState) {
            document.body.classList.add('sidebar-collapsed');
        }
    }
}

// ============================================
// 9. Tooltips and Popovers
// ============================================
function setupTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// ============================================
// 10. Dashboard Charts
// ============================================
function initializeDashboardCharts() {
    // Project Progress Chart
    const ctx1 = document.getElementById('projectProgressChart')?.getContext('2d');
    if (ctx1) {
        fetch('/api/dashboard/stats/')
            .then(response => response.json())
            .then(data => {
                new Chart(ctx1, {
                    type: 'bar',
                    data: {
                        labels: data.project_names,
                        datasets: [{
                            label: 'Progress (%)',
                            data: data.project_progress,
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                title: {
                                    display: true,
                                    text: 'Completion (%)'
                                }
                            }
                        }
                    }
                });
            });
    }
    
    // Task Distribution Chart
    const ctx2 = document.getElementById('taskDistributionChart')?.getContext('2d');
    if (ctx2) {
        fetch('/api/dashboard/task-stats/')
            .then(response => response.json())
            .then(data => {
                new Chart(ctx2, {
                    type: 'doughnut',
                    data: {
                        labels: ['Pending', 'In Progress', 'Testing', 'Completed'],
                        datasets: [{
                            data: data.task_counts,
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.8)',
                                'rgba(54, 162, 235, 0.8)',
                                'rgba(255, 206, 86, 0.8)',
                                'rgba(75, 192, 192, 0.8)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            });
    }
}

// ============================================
// 11. Date Pickers Initialization
// ============================================
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            if (input.id === 'start_date') {
                input.value = today;
            } else if (input.id === 'end_date') {
                const nextMonth = new Date();
                nextMonth.setMonth(nextMonth.getMonth() + 1);
                input.value = nextMonth.toISOString().split('T')[0];
            }
        }
    });
}

// ============================================
// 12. Utility Functions
// ============================================
function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60,
        second: 1
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return interval === 1 ? `1 ${unit} ago` : `${interval} ${unit}s ago`;
        }
    }
    return 'just now';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0 mb-2`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// ============================================
// 13. AJAX Form Submission
// ============================================
function submitFormAjax(formId, url, successCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(form);
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message || 'Operation successful!');
                if (successCallback) successCallback(data);
            } else {
                showToast(data.error || 'An error occurred', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Network error occurred', 'danger');
        });
    });
}

// ============================================
// 14. Export Functions for Global Access
// ============================================
window.showToast = showToast;
window.markNotificationRead = markNotificationRead;
window.submitFormAjax = submitFormAjax;
window.escapeHtml = escapeHtml;