// static/js/chat.js
// Complete Real-time Chat System

class ChatSystem {
    constructor(teamId, username) {
        this.teamId = teamId;
        this.username = username;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.typingTimeout = null;
        this.isTyping = false;
        
        this.initialize();
    }
    
    initialize() {
        this.connect();
        this.setupEventListeners();
        this.loadMessageHistory();
        this.markMessagesAsRead();
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${protocol}${window.location.host}/ws/chat/${this.teamId}/`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.showConnectionStatus('connected', 'Connected');
            this.sendPresence('online');
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleIncomingMessage(data);
        };
        
        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.showConnectionStatus('disconnected', 'Reconnecting...');
            this.reconnect();
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showConnectionStatus('error', 'Connection error');
        };
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting attempt ${this.reconnectAttempts} of ${this.maxReconnectAttempts}`);
            setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.showConnectionStatus('error', 'Unable to connect. Please refresh the page.');
        }
    }
    
    setupEventListeners() {
        // Send message on button click or Enter key
        const sendBtn = document.getElementById('send-btn');
        const messageInput = document.getElementById('message-input');
        
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            messageInput.addEventListener('input', () => this.handleTyping());
        }
        
        // Auto-scroll to bottom
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            this.scrollToBottom();
            
            // Mark messages as read when user scrolls to bottom
            chatContainer.addEventListener('scroll', () => {
                if (this.isScrolledToBottom()) {
                    this.markMessagesAsRead();
                }
            });
        }
    }
    
    sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        const messageData = {
            type: 'chat_message',
            message: message,
            username: this.username,
            timestamp: new Date().toISOString()
        };
        
        this.socket.send(JSON.stringify(messageData));
        
        // Clear input and reset typing indicator
        messageInput.value = '';
        this.resetTypingIndicator();
        
        // Add message to UI immediately (optimistic rendering)
        this.addMessageToUI(messageData, true);
    }
    
    handleIncomingMessage(data) {
        // Don't duplicate if message is from current user
        if (data.username === this.username) return;
        
        this.addMessageToUI(data, false);
        this.playNotificationSound();
        this.showDesktopNotification(data);
        
        // Auto-scroll if already at bottom
        if (this.isScrolledToBottom()) {
            this.scrollToBottom();
        }
    }
    
    addMessageToUI(data, isOwnMessage) {
        const messagesDiv = document.getElementById('chat-messages');
        if (!messagesDiv) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isOwnMessage ? 'message-right' : 'message-left'} mb-3`;
        
        const time = new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-header">
                    <strong>${this.escapeHtml(data.username)}</strong>
                    <small class="text-muted ms-2">${time}</small>
                </div>
                <p class="mb-1">${this.escapeHtml(data.message)}</p>
                ${!isOwnMessage && !data.is_read ? '<span class="message-status">● New</span>' : ''}
            </div>
        `;
        
        messagesDiv.appendChild(messageDiv);
        
        // Scroll to bottom only for new messages
        if (this.isScrolledToBottom() || isOwnMessage) {
            this.scrollToBottom();
        }
    }
    
    loadMessageHistory() {
        fetch(`/chat/api/history/${this.teamId}/`)
            .then(response => response.json())
            .then(messages => {
                const messagesDiv = document.getElementById('chat-messages');
                if (messagesDiv) {
                    messagesDiv.innerHTML = '';
                    messages.forEach(message => {
                        this.addMessageToUI(message, message.username === this.username);
                    });
                    this.scrollToBottom();
                }
            })
            .catch(error => console.error('Error loading message history:', error));
    }
    
    handleTyping() {
        if (!this.isTyping) {
            this.isTyping = true;
            this.sendPresence('typing');
        }
        
        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.resetTypingIndicator();
        }, 1000);
    }
    
    resetTypingIndicator() {
        if (this.isTyping) {
            this.isTyping = false;
            this.sendPresence('stopped_typing');
        }
    }
    
    sendPresence(status) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'presence',
                status: status,
                username: this.username
            }));
        }
    }
    
    showConnectionStatus(status, message) {
        const statusDiv = document.getElementById('connection-status');
        if (statusDiv) {
            statusDiv.textContent = message;
            statusDiv.className = `connection-status ${status}`;
            setTimeout(() => {
                if (status === 'connected') {
                    statusDiv.style.opacity = '0';
                }
            }, 3000);
        }
    }
    
    showDesktopNotification(data) {
        if (!('Notification' in window)) return;
        
        if (Notification.permission === 'granted') {
            new Notification(`${data.username} sent a message`, {
                body: data.message.length > 100 ? data.message.substring(0, 100) + '...' : data.message,
                icon: '/static/assets/logo.png'
            });
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission();
        }
    }
    
    playNotificationSound() {
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.3;
        audio.play().catch(e => console.log('Audio play failed:', e));
    }
    
    markMessagesAsRead() {
        fetch(`/chat/api/mark-read/${this.teamId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
    }
    
    isScrolledToBottom() {
        const messagesDiv = document.getElementById('chat-messages');
        if (!messagesDiv) return true;
        
        const threshold = 100;
        return messagesDiv.scrollHeight - messagesDiv.scrollTop - messagesDiv.clientHeight < threshold;
    }
    
    scrollToBottom() {
        const messagesDiv = document.getElementById('chat-messages');
        if (messagesDiv) {
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chat when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-messages');
    if (chatContainer) {
        const teamId = chatContainer.dataset.teamId;
        const username = chatContainer.dataset.username;
        
        if (teamId && username) {
            window.chatSystem = new ChatSystem(teamId, username);
        }
    }
});