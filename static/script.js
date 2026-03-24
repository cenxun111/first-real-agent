// Generate or retrieve session ID
function getSessionId() {
    let sessionId = localStorage.getItem('agentSessionId');
    if (!sessionId) {
        sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('agentSessionId', sessionId);
    }
    return sessionId;
}

const SESSION_ID = getSessionId();

// DOM Elements
const chatFeed = document.getElementById('chatFeed');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');

// Configure marked.js to use highlighted code blocks if hljs was present (skipped for simplicity, clean styling applied via CSS)
// Optionally we open links in new tabs safely
if(typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true,
        gfm: true
    });
}

function createMessageElement(content, sender, isMarkdown = false) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender === 'user' ? 'user-message' : 'agent-message');
    
    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble');
    
    if (isMarkdown && sender !== 'user' && typeof marked !== 'undefined') {
        bubble.innerHTML = marked.parse(content);
    } else {
        bubble.textContent = content;
    }
    
    msgDiv.appendChild(bubble);
    return msgDiv;
}

function showTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.classList.add('typing-indicator');
    indicatorDiv.id = 'typingIndicator';
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.classList.add('typing-dot');
        indicatorDiv.appendChild(dot);
    }
    
    chatFeed.appendChild(indicatorDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function scrollToBottom() {
    chatFeed.scrollTop = chatFeed.scrollHeight;
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;
    
    // Clear input & reset height
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Append user message
    const userMsg = createMessageElement(text, 'user');
    chatFeed.appendChild(userMsg);
    scrollToBottom();
    
    // Show typing animation
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: SESSION_ID,
                message: text
            })
        });
        
        const data = await response.json();
        removeTypingIndicator();
        
        if (data.status === 'success') {
            const agentMsg = createMessageElement(data.response, 'agent', true);
            chatFeed.appendChild(agentMsg);
        } else {
            const errorMsg = createMessageElement("Sorry, an error occurred processing your request.", 'system');
            chatFeed.appendChild(errorMsg);
            console.error(data);
        }
    } catch (error) {
        removeTypingIndicator();
        const errorMsg = createMessageElement("Network error. Could not reach the server.", 'system');
        chatFeed.appendChild(errorMsg);
        console.error("Error calling chat API:", error);
    }
    
    scrollToBottom();
}

// Event Listeners
sendBtn.addEventListener('click', sendMessage);

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Press enter to send, Shift+Enter for new line
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
