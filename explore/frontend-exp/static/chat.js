document.addEventListener('DOMContentLoaded', () => {
    const contactList = document.getElementById('contact-list');
    const messageArea = document.getElementById('message-area');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatName = document.getElementById('chat-name');
    const chatAvatar = document.getElementById('chat-avatar');
    const initialMessage = document.getElementById('initial-message');
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUploadInput = document.getElementById('file-upload-input');

    let currentContactId = null;

    async function loadContacts() {
        try {
            const response = await fetch('/api/contacts');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const contacts = await response.json();
            contacts.forEach(contact => {
                const contactDiv = document.createElement('div');
                contactDiv.classList.add('contact');
                contactDiv.dataset.contactId = contact.id;
                const initials = contact.name.substring(0, 2).toUpperCase();
                contactDiv.innerHTML = `
                    <div class="avatar">${initials}</div>
                    <span>${contact.name}</span>
                `;
                contactDiv.addEventListener('click', () => {
                    currentContactId = contact.id;
                    chatName.textContent = contact.name;
                    chatAvatar.textContent = initials;
                    messageArea.innerHTML = '';
                    initialMessage.style.display = 'none';
                    loadChatHistory(contact.id);
                });
                contactList.appendChild(contactDiv);
            });
        } catch (error) {
            console.error('Error loading contacts:', error);
        }
    }

    async function loadChatHistory(contactId) {
        try {
            const response = await fetch(`/api/chat/${contactId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const messages = await response.json();
            messages.forEach(message => {
                appendMessage(message.text, message.sender === 'me' ? 'sent' : 'received', message.timestamp, message.file_path);
            });
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    sendButton.addEventListener('click', async () => {
        const messageText = messageInput.value.trim();
        if (messageText && currentContactId) {
            try {
                const response = await fetch('/api/send-message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        contact_id: currentContactId,
                        text: messageText,
                    }),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const newMessage = await response.json(); // Get the message from the server

                appendMessage(newMessage.text, 'sent', newMessage.timestamp, null); // Use the message data
                messageInput.value = '';
            } catch (error) {
                console.error('Error sending message:', error);
            }
        }
    });

    function appendMessage(text, type, timestamp, filePath) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        if (filePath) {
            const fileLink = document.createElement('a');
            fileLink.href = `/uploads/${filePath}`;
            fileLink.textContent = filePath.split('/').pop();
            contentDiv.appendChild(fileLink);
        } else {
            contentDiv.textContent = text;
        }

        const timeDiv = document.createElement('div');
        timeDiv.classList.add('message-time');
        timeDiv.textContent = timestamp;

        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);

        messageArea.appendChild(messageDiv);
        messageArea.scrollTop = messageArea.scrollHeight;
    }

    fileUploadButton.addEventListener('click', () => {
        fileUploadInput.click();
    });

    // ... (other JavaScript code) ...

    fileUploadInput.addEventListener('change', async () => {
    const file = fileUploadInput.files[0];
    if (file && currentContactId) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('contact_id', currentContactId);
        try {
            const response = await fetch('/api/upload-file', {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            appendMessage(null, 'sent', new Date().toLocaleTimeString(), result.file_path);
        } catch (error) {
            console.error('Error uploading file:', error);
        } finally {
            fileUploadInput.value = '';
        }
    }
    });

// ... (other JavaScript code) ...

    loadContacts();
});