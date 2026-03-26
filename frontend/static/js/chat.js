// Chat functionality for the legal chatbot

console.log('Chat.js loaded');

// Get CSRF token from cookie
function getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCsrfToken();

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing chat...');
    const chatForm = document.getElementById('chat-form');
    const questionInput = document.getElementById('question-input');
    const chatWindow = document.getElementById('chat-window');
    const emptyState = document.getElementById('chat-empty-state');
    
    console.log('Elements found - chatForm:', !!chatForm, 'questionInput:', !!questionInput, 'chatWindow:', !!chatWindow);
    
    // Toggle empty state visibility
    function updateEmptyState() {
        const hasMessages = chatWindow.querySelectorAll('.chat-message:not(.chat-empty-state)').length > 0;
        if (emptyState) {
            emptyState.style.display = hasMessages ? 'none' : 'flex';
        }
    }
    
    // Load previous chat history on page load
    loadChatHistory();

    if (chatForm) {
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const message = questionInput.value.trim();
            if (!message) return;

            // Add user message to chat
            addMessage(message, 'user');
            questionInput.value = '';

            // Show loading indicator
            const loadingId = addLoadingMessage();

            try {
                const response = await fetch('/chatbot/api/message/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: message }),
                    credentials: 'same-origin'
                });

                const data = await response.json();

                // Remove loading message
                removeMessage(loadingId);

                if (data.success) {
                    // Add bot response to chat
                    addMessage(data.message, 'bot', data.sources);
                    
                    // Save user activity to session storage for dashboard
                    saveUserActivity(message);
                    
                    // Save to chat history
                    saveChatHistory(message, 'user', data.sources);
                    saveChatHistory(data.message, 'bot', data.sources);
                } else {
                    addMessage('Sorry, I encountered an error. Please try again.', 'bot');
                }
            } catch (error) {
                console.error('Error:', error);
                removeMessage(loadingId);
                addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        });
    }

    function addMessage(content, sender, sources = []) {
        console.log('Adding message:', content.substring(0, 50), 'from', sender);
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const avatar = sender === 'bot' ? '⚖️' : '👤';
        
        // Convert markdown-style formatting to HTML
        let formattedContent = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        
        let sourceInfo = '';
        if (sources && sources.length > 0) {
            sourceInfo = `<div class="message-sources">Sources: ${sources.join(', ')}</div>`;
        }

        messageDiv.innerHTML = `
            <div class="avatar">${avatar}</div>
            <div class="message">
                ${formattedContent}
                ${sourceInfo}
            </div>
        `;
        
        // Hide empty state when first message is added
        updateEmptyState();
        
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        console.log('Message added to DOM');
    }

    function addLoadingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message bot loading';
        messageDiv.id = 'loading-' + Date.now();
        messageDiv.innerHTML = `
            <div class="avatar">⚖️</div>
            <div class="message">
                <span class="typing-indicator">Thinking...</span>
            </div>
        `;
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        updateEmptyState();
        return messageDiv.id;
    }

    function removeMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }
    
    // Save user activity for dashboard
    function saveUserActivity(query) {
        let activity = JSON.parse(sessionStorage.getItem('user_activity') || '{"queries": [], "topics": []}');
        
        // Add new query
        activity.queries.push(query);
        
        // Extract topics from query and personalization
        const topics = JSON.parse(sessionStorage.getItem('user_preferences') || '{"topics": []}');
        if (topics.topics) {
            activity.topics = topics.topics;
        }
        
        // Keep only last 20 queries
        if (activity.queries.length > 20) {
            activity.queries = activity.queries.slice(-20);
        }
        
        sessionStorage.setItem('user_activity', JSON.stringify(activity));
    }
    
    // Load chat history from session storage
    function loadChatHistory() {
        console.log('Loading chat history...');
        const history = JSON.parse(sessionStorage.getItem('chat_history') || '[]');
        console.log('History found:', history);
        
        // If no history, initialize with welcome message
        if (history.length === 0) {
            console.log('No history, creating welcome message');
            const welcomeMsg = {
                message: "Hello! I'm your Legal AI Assistant. How can I help you today?",
                sender: 'bot',
                sources: [],
                timestamp: new Date().toISOString()
            };
            sessionStorage.setItem('chat_history', JSON.stringify([welcomeMsg]));
            addMessage(welcomeMsg.message, 'bot', welcomeMsg.sources);
        } else {
            console.log('Loading', history.length, 'messages from history');
            // Load all history messages
            history.forEach(msg => {
                addMessage(msg.message, msg.sender, msg.sources);
            });
        }
    }
    
    // Save chat message to history
    function saveChatHistory(message, sender, sources = []) {
        let history = JSON.parse(sessionStorage.getItem('chat_history') || '[]');
        history.push({
            message: message,
            sender: sender,
            sources: sources,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 50 messages
        if (history.length > 50) {
            history = history.slice(-50);
        }
        
        sessionStorage.setItem('chat_history', JSON.stringify(history));
    }
});

// Start a new chat - clear history
function startNewChat() {
    console.log('Starting new chat...');
    sessionStorage.removeItem('chat_history');
    
    // Clear the chat window
    const chatWindow = document.getElementById('chat-window');
    if (!chatWindow) return;
    
    chatWindow.innerHTML = '';
    
    // Add welcome message
    const welcomeMsg = {
        message: "Hello! I'm your Legal AI Assistant. How can I help you today?",
        sender: 'bot',
        sources: [],
        timestamp: new Date().toISOString()
    };
    sessionStorage.setItem('chat_history', JSON.stringify([welcomeMsg]));
    addMessage(welcomeMsg.message, 'bot', welcomeMsg.sources);
    
    // Show empty state again
    const emptyState = document.getElementById('chat-empty-state');
    if (emptyState) {
        emptyState.style.display = 'flex';
    }
}
