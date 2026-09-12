// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const voiceBtn = document.getElementById('voice-btn');
    const chatMessages = document.getElementById('chat-messages');
    const commandHistory = document.getElementById('command-history');
    
    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    voiceBtn.addEventListener('click', startVoiceInput);
    
    // Quick command buttons
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const command = this.getAttribute('data-command');
            executeQuickCommand(command);
        });
    });
    
    // Update system stats every 2 seconds
    setInterval(updateSystemStats, 2000);
    
    // Initialize
    updateSystemStats();
});

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const voiceEnabled = document.getElementById('voice-enabled').checked;
    const message = userInput.value.trim();
    
    if (message) {
        addUserMessage(message);
        userInput.value = '';
        
        // Send to Python backend with voice enabled flag
        eel.process_message(message, voiceEnabled)(function(response) {
            addSerenaMessage(response);
            updateCommandHistory(message);
        });
    }
}

function addUserMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addSerenaMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message serena';
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function startVoiceInput() {
    const voiceBtn = document.getElementById('voice-btn');
    voiceBtn.disabled = true;
    voiceBtn.textContent = '🎙️';
    
    eel.voice_input()(function(result) {
        voiceBtn.disabled = false;
        voiceBtn.textContent = '🎤';
        
        if (result) {
            addUserMessage(result);
            eel.process_message(result)(function(response) {
                addSerenaMessage(response);
                updateCommandHistory(result);
            });
        }
    });
}

function executeQuickCommand(command) {
    addUserMessage(command);
    eel.process_message(command)(function(response) {
        addSerenaMessage(response);
        updateCommandHistory(command);
    });
}

function updateSystemStats() {
    eel.get_system_stats()(function(stats) {
        if (stats) {
            document.getElementById('cpu-usage').textContent = stats.cpu + '%';
            document.getElementById('memory-usage').textContent = stats.memory + '%';
            document.getElementById('battery-status').textContent = stats.battery + '%';
        }
    });
}

function updateCommandHistory(command) {
    const commandHistory = document.getElementById('command-history');
    const noCommands = commandHistory.querySelector('.no-commands');
    
    if (noCommands) {
        noCommands.remove();
    }
    
    const commandDiv = document.createElement('p');
    commandDiv.textContent = command;
    commandHistory.insertBefore(commandDiv, commandHistory.firstChild);
    
    // Keep only last 10 commands
    while (commandHistory.children.length > 10) {
        commandHistory.removeChild(commandHistory.lastChild);
    }
}

function updateMode(mode) {
    document.getElementById('mode-display').textContent = mode;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Listen for updates from Python
eel.expose(updateMode);
eel.expose(addSerenaMessage);