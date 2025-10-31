// Chat History Management
let chatHistory = [];
let currentChatId = null;
let uploadedFilesList = [];
let uploadedFiles = null;

// Load chat history from backend
function loadChatHistory() {
    fetch('/history')
        .then(response => response.json())
        .then(data => {
            chatHistory = data.sessions || [];
            renderChatHistory();
        })
        .catch(error => {
            console.error('Error loading chat history:', error);
        });
}

function renderChatHistory() {
    const chatHistoryContainer = document.getElementById('chatHistory');
    
    if (chatHistory.length === 0) {
        chatHistoryContainer.innerHTML = '<div class="chat-history-empty">No previous chats</div>';
        return;
    }
    
    chatHistoryContainer.innerHTML = chatHistory.map(chat => `
        <div class="chat-history-item ${chat.id === currentChatId ? 'active' : ''}" data-chat-id="${chat.id}">
            <span class="chat-history-item-text">${chat.title}</span>
            <button class="chat-history-item-delete" onclick="deleteChatSession('${chat.id}', event)">×</button>
        </div>
    `).join('');
    
    // Add click listeners
    document.querySelectorAll('.chat-history-item').forEach(item => {
        item.addEventListener('click', function(e) {
            if (!e.target.classList.contains('chat-history-item-delete')) {
                loadChat(this.dataset.chatId);
            }
        });
    });
}

function createNewChat() {
    currentChatId = Date.now().toString();
    
    // Update URL
    window.history.pushState({}, '', `/${currentChatId}`);
    
    // Create session in backend
    fetch('/session/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentChatId,
            title: 'New Chat'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Session created:', currentChatId);
            loadChatHistory(); // Reload history
        }
    })
    .catch(error => {
        console.error('Error creating session:', error);
    });
    
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h2>👋 I'm DocuSensei—how can I help?</h2>
            <div class="suggestion-cards">
                <div class="suggestion-card">
                    <span class="icon">📄</span>
                    <span>Summarize this document for me</span>
                </div>
                <div class="suggestion-card">
                    <span class="icon">🔍</span>
                    <span>Find specific information in my files</span>
                </div>
                <div class="suggestion-card">
                    <span class="icon">💡</span>
                    <span>Extract key insights from documents</span>
                </div>
                <div class="suggestion-card">
                    <span class="icon">❓</span>
                    <span>Answer questions about my documents</span>
                </div>
            </div>
        </div>
    `;
    
    // Clear uploaded files
    uploadedFilesList = [];
    document.getElementById('uploadedFiles').innerHTML = '';
    
    // Re-attach suggestion card listeners
    attachSuggestionListeners();
}

// Load a specific chat
function loadChat(chatId) {
    currentChatId = chatId;
    
    // Update URL
    window.history.pushState({}, '', `/${chatId}`);
    
    // Fetch chat messages from backend
    fetch(`/session/${chatId}`)
        .then(response => response.json())
        .then(data => {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '';
            
            // Load messages
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${msg.role}`;
                    const formattedContent = msg.role === 'assistant' ? formatResponse(msg.content) : msg.content;
                    messageDiv.innerHTML = `<div class="message-content">${formattedContent}</div>`;
                    chatMessages.appendChild(messageDiv);
                });
            } else {
                // Show welcome message if no messages
                chatMessages.innerHTML = `
                    <div class="welcome-message">
                        <h2>👋 I'm DocuSensei—how can I help?</h2>
                        <div class="suggestion-cards">
                            <div class="suggestion-card">
                                <span class="icon">📄</span>
                                <span>Summarize this document for me</span>
                            </div>
                            <div class="suggestion-card">
                                <span class="icon">🔍</span>
                                <span>Find specific information in my files</span>
                            </div>
                            <div class="suggestion-card">
                                <span class="icon">💡</span>
                                <span>Extract key insights from documents</span>
                            </div>
                            <div class="suggestion-card">
                                <span class="icon">❓</span>
                                <span>Answer questions about my documents</span>
                            </div>
                        </div>
                    </div>
                `;
                attachSuggestionListeners();
            }
            
            // Load uploaded files
            uploadedFilesList = data.files || [];
            renderUploadedFiles();
            
            // Update chat history UI
            renderChatHistory();
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            console.error('Error loading chat:', error);
        });
}

// Delete a chat session
function deleteChatSession(chatId, event) {
    event.stopPropagation();
    
    if (!confirm('Delete this chat?')) return;
    
    fetch(`/session/${chatId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // If deleting current chat, create new one
            if (chatId === currentChatId) {
                createNewChat();
            }
            loadChatHistory();
        }
    })
    .catch(error => {
        console.error('Error deleting chat:', error);
    });
}

// Render uploaded files
function renderUploadedFiles() {
    const uploadedFilesContainer = document.getElementById('uploadedFiles');
    if (uploadedFilesList.length === 0) {
        uploadedFilesContainer.innerHTML = '';
        return;
    }
    
    uploadedFilesContainer.innerHTML = uploadedFilesList.map(file => `
        <div class="uploaded-file-tag">
            <span>📄 ${file.filename || file}</span>
        </div>
    `).join('');
}

// Initialize - create first session
console.log('Initializing app...');
createNewChat();
console.log('App initialized');

// Reasoning Level Selection
document.querySelectorAll('.reasoning-option').forEach(option => {
    option.addEventListener('click', function() {
        document.querySelectorAll('.reasoning-option').forEach(o => o.classList.remove('active'));
        this.classList.add('active');
        this.querySelector('input[type="radio"]').checked = true;
    });
});

// Initialize uploadedFiles reference
uploadedFiles = document.getElementById('uploadedFiles');

function handleFileUpload(file) {
    console.log('handleFileUpload called with file:', file);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', currentChatId);  // Add session ID
    
    console.log('Showing loader...');
    // Show loader
    const loader = document.getElementById('uploadLoader');
    if (loader) {
        loader.classList.add('active');
    } else {
        console.error('Upload loader not found!');
    }
    
    console.log('Sending upload request...');
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Upload response received:', response);
        return response.json();
    })
    .then(data => {
        console.log('Upload data:', data);
        // Hide loader
        const loader = document.getElementById('uploadLoader');
        if (loader) {
            loader.classList.remove('active');
        }
        
        if (data.success) {
            try {
                addFileToList(data.filename);
                showNotification(data.message, 'success');
            } catch (listError) {
                console.error('Error adding file to list:', listError);
                // Still show success since upload worked
                showNotification(data.message, 'success');
            }
        } else {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        // Hide loader
        const loader = document.getElementById('uploadLoader');
        if (loader) {
            loader.classList.remove('active');
        }
        showNotification('Upload failed: ' + error.message, 'error');
    });
}

function addFileToList(filename) {
    try {
        if (typeof uploadedFilesList === 'undefined') {
            console.error('uploadedFilesList is undefined!');
            return;
        }
        
        uploadedFilesList.push(filename);
        
        const uploadedFilesContainer = document.getElementById('uploadedFiles');
        if (!uploadedFilesContainer) {
            console.error('uploadedFiles container not found!');
            return;
        }
        
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span class="file-item-name">📎 ${filename}</span>
            <button onclick="removeFile('${filename}', this)">×</button>
        `;
        
        uploadedFilesContainer.appendChild(fileItem);
    } catch (error) {
        console.error('Error in addFileToList:', error);
    }
}

function removeFile(filename, button) {
    uploadedFilesList = uploadedFilesList.filter(f => f !== filename);
    button.parentElement.remove();
    showNotification(`Removed ${filename}`, 'info');
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background-color: ${type === 'success' ? 'rgba(46, 213, 115, 0.9)' : type === 'error' ? 'rgba(255, 107, 107, 0.9)' : 'rgba(102, 126, 234, 0.9)'};
        color: white;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Attach suggestion card listeners
function attachSuggestionListeners() {
    document.querySelectorAll('.suggestion-card').forEach(card => {
        card.addEventListener('click', function() {
            const text = this.querySelector('span:last-child').textContent;
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.value = text;
                sendMessage();
            }
        });
    });
}

// Convert markdown-style text to clean HTML
function formatResponse(text) {
    if (!text) return '';
    
    // Replace **bold** with <strong>
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Replace *italic* with <em>
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Replace line breaks with <br>
    text = text.replace(/\n/g, '<br>');
    
    // Remove markdown table syntax
    text = text.replace(/\|/g, '');
    text = text.replace(/[-]{3,}/g, '');
    
    return text;
}

// GLOBAL sendMessage function - called from inline onclick
function sendMessage() {
    console.log('=== sendMessage called ===');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    
    if (!chatInput) {
        console.error('chatInput not found!');
        return;
    }
    
    const message = chatInput.value.trim();
    console.log('Message:', message);
    console.log('Session ID:', currentChatId);
    
    if (message === '') {
        console.log('Empty message');
        return;
    }
    
    // Hide welcome message
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    // Add user message
    const userMsg = document.createElement('div');
    userMsg.className = 'message user';
    userMsg.innerHTML = `<div class="message-content">${message}</div>`;
    chatMessages.appendChild(userMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Clear input
    chatInput.value = '';
    
    // Add typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = '<div class="message-content"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    console.log('Sending to /chat endpoint...');
    
    // Send to backend
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            session_id: currentChatId
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        
        // Remove typing indicator
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
        
        // Format and add bot response
        const botMsg = document.createElement('div');
        botMsg.className = 'message bot';
        const formattedResponse = formatResponse(data.response || data.error || 'No response');
        botMsg.innerHTML = `<div class="message-content">${formattedResponse}</div>`;
        chatMessages.appendChild(botMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(error => {
        console.error('Error:', error);
        
        // Remove typing indicator
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
        
        // Show error
        const botMsg = document.createElement('div');
        botMsg.className = 'message bot';
        botMsg.innerHTML = `<div class="message-content">Error: ${error.message}</div>`;
        chatMessages.appendChild(botMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    // Chat Functionality
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');

    console.log('Chat elements:', { chatInput, sendButton, chatMessages });
    
    if (!chatInput || !sendButton || !chatMessages) {
        console.error('Required chat elements not found!');
        return;
    }

    // Load chat history from backend
    loadChatHistory();
    
    // Check URL for session ID
    const path = window.location.pathname;
    if (path && path !== '/' && path.length > 1) {
        const sessionId = path.substring(1); // Remove leading slash
        console.log('Loading session from URL:', sessionId);
        loadChat(sessionId);
    } else {
        // Create new chat if no session in URL
        createNewChat();
    }
    
    // Handle browser back/forward
    window.addEventListener('popstate', function() {
        const path = window.location.pathname;
        if (path && path !== '/' && path.length > 1) {
            const sessionId = path.substring(1);
            loadChat(sessionId);
        } else {
            createNewChat();
        }
    });
    
    // New Chat Button
    document.getElementById('newChatBtn').addEventListener('click', createNewChat);

    attachSuggestionListeners();

    sendButton.addEventListener('click', function() {
        console.log('Send button clicked!');
        sendMessage();
    });
    console.log('Send button listener attached');

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            console.log('Enter key pressed');
            sendMessage();
        }
    });

    function sendMessage() {
        console.log('sendMessage called');
        const message = chatInput.value.trim();
        console.log('Message:', message);
        
        if (message === '') {
            console.log('Empty message, returning');
            return;
        }
        
        console.log('Current session ID:', currentChatId);
        
        // Hide welcome message
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
        
        // Save to chat history
        saveCurrentChat(message);
        
        // Add user message
        addMessage(message, 'user');
        
        // Clear input
        chatInput.value = '';
        
        // Show typing indicator
        const typingId = addTypingIndicator();
        
        console.log('Sending to backend...');
        // Send to backend with session_id
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: currentChatId
            })
        })
        .then(response => {
            console.log('Response received:', response);
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            removeTypingIndicator(typingId);
            if (data.success) {
                addMessage(data.response, 'bot');
            } else {
                addMessage('Sorry, there was an error: ' + (data.error || 'Unknown error'), 'bot');
            }
        })
        .catch(error => {
            console.error('Chat error:', error);
            removeTypingIndicator(typingId);
            addMessage('Sorry, there was an error processing your request.', 'bot');
        });
    }

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? 'U' : 'AI';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;
    
    content.appendChild(messageText);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const typingId = 'typing-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.id = typingId;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = '<div class="message-text">Thinking...</div>';
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatMessages.appendChild(messageDiv);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return typingId;
}

function removeTypingIndicator(typingId) {
    const typing = document.getElementById(typingId);
    if (typing) {
        typing.remove();
    }
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize file upload after everything is loaded
    // File upload initialization
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadBtn && fileInput) {
        console.log('File upload elements found');
        
        uploadBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Attach file button clicked!');
            fileInput.click();
            return false;
        };
        
        fileInput.onchange = function(e) {
            console.log('File input changed:', e.target.files);
            if (e.target.files && e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
                e.target.value = ''; // Reset
            }
        };
    } else {
        console.error('Upload elements not found!');
    }
    
    console.log('All event listeners initialized');
}); // End of DOMContentLoaded
