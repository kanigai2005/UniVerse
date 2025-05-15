// static/chat.js (NEW version for sidebar layout)

// --- Utility: Simple HTML Escaping ---
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') { return unsafe === null || unsafe === undefined ? '' : String(unsafe); }
    return unsafe
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
}

document.addEventListener('DOMContentLoaded', async () => {
    console.log("Chat Page (Sidebar Layout) DOM Loaded.");

    // --- Element References ---
    const chatContactListUL = document.getElementById('chatContactList');
    const chatCurrentTargetNameHeader = document.getElementById('chatCurrentTargetName');
    const chatCurrentTargetAvatar = document.getElementById('chatCurrentTargetAvatar'); // New
    const messagesContainer = document.getElementById('chatPageMessagesArea');
    const messageInput = document.getElementById('chatPageMessageInput');
    const sendMessageButton = document.getElementById('chatPageSendButton');
    const chatInputAreaDiv = document.getElementById('chatPageInputArea');
    const backToNetworkButton = document.getElementById('backToNetworkBtn'); // In top-nav

    // --- State ---
    let activeChatContactId = null; // The ChatContact.id of the currently open chat
    let activeChatTargetUsername = null;
    let loggedInUsername = null;
    let loggedInUserId = null;
    let contactsMap = new Map(); // To store contact_id -> {other_user_username, etc.}

    // --- Check Core Elements ---
    const essentialElements = {
        chatContactListUL, chatCurrentTargetNameHeader, chatCurrentTargetAvatar,
        messagesContainer, messageInput, sendMessageButton, chatInputAreaDiv, backToNetworkButton
    };
    for (const elName in essentialElements) {
        if (!essentialElements[elName]) {
            console.error(`CRITICAL (Chat Page): UI element ID '${elName}' missing!`);
            return; // Stop if critical elements are missing
        }
    }
    chatInputAreaDiv.style.display = 'none'; // Hide input until a chat is active

    // --- API Call Helper ---
    async function apiCall(url, method = 'GET', body = null) {
        const options = { method, headers: {}, credentials: 'include' };
        if (body && (method === 'POST' || method === 'PUT' || method === 'DELETE')) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
        try {
            const response = await fetch(url, options);
            let responseData = {};
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                responseData = await response.json();
            } else if (!response.ok) {
                const textError = await response.text();
                throw new Error(textError || `Request failed: ${response.status} ${response.statusText}`);
            }
            if (!response.ok) {
                const errorMessage = responseData.detail || `Request to ${url} failed: ${response.status} ${response.statusText}`;
                throw new Error(errorMessage);
            }
            return responseData;
        } catch (error) {
            console.error(`Error during API call to ${url} (method: ${method}):`, error);
            throw error;
        }
    }

    // --- Fetch Current Logged-In User ---
    async function fetchLoggedInUser() {
        try {
            const userData = await apiCall('/api/users/me');
            if (userData && userData.username && typeof userData.id === 'number') {
                loggedInUsername = userData.username;
                loggedInUserId = userData.id;
                console.log("[CHAT_PAGE] Logged in user:", loggedInUsername, "ID:", loggedInUserId);
                return true;
            }
            console.warn("[CHAT_PAGE] Logged-in user data incomplete.");
            window.location.href = '/?error=Session+invalid'; return false;
        } catch (error) {
            console.error("[CHAT_PAGE] Failed to fetch logged-in user:", error);
            window.location.href = '/?error=Session+error'; return false;
        }
    }

    // --- Load and Display Chat Contacts in Sidebar ---
    async function loadChatContacts() {
        if (!loggedInUserId) return;
        chatContactListUL.innerHTML = '<p class="loading" style="padding:15px;text-align:center;">Loading contacts...</p>';
        try {
            // YOU NEED TO CREATE THIS API ENDPOINT: /api/chat/my-contacts
            const contacts = await apiCall('/api/chat/my-contacts');
            chatContactListUL.innerHTML = ''; // Clear loading
            contactsMap.clear();

            if (Array.isArray(contacts) && contacts.length > 0) {
                contacts.forEach(contact => {
                    // Store contact info for later use
                    contactsMap.set(contact.contact_id, {
                        other_user_username: contact.other_user_username,
                        // other_user_id: contact.other_user_id, // if needed
                        // avatar_initials: contact.other_user_username.substring(0,2).toUpperCase()
                    });

                    const listItem = document.createElement('li');
                    listItem.classList.add('contact-item');
                    listItem.dataset.contactId = contact.contact_id;
                    listItem.dataset.targetUsername = contact.other_user_username;

                    const avatar = document.createElement('div');
                    avatar.classList.add('avatar-placeholder');
                    avatar.textContent = contact.other_user_username ? contact.other_user_username.substring(0,2).toUpperCase() : '??';

                    const infoDiv = document.createElement('div');
                    infoDiv.classList.add('contact-info');
                    const nameSpan = document.createElement('div');
                    nameSpan.classList.add('contact-name');
                    nameSpan.textContent = escapeHtml(contact.other_user_username);
                    const previewSpan = document.createElement('div');
                    previewSpan.classList.add('last-message-preview');
                    previewSpan.textContent = escapeHtml(contact.last_message_preview || 'No messages yet');

                    infoDiv.appendChild(nameSpan);
                    infoDiv.appendChild(previewSpan);
                    listItem.appendChild(avatar);
                    listItem.appendChild(infoDiv);
                    chatContactListUL.appendChild(listItem);
                });
            } else {
                chatContactListUL.innerHTML = '<p class="no-data" style="padding:15px;text-align:center;">No active conversations.</p>';
            }
        } catch (error) {
            console.error("[CHAT_PAGE] Error loading chat contacts:", error);
            chatContactListUL.innerHTML = `<p class="error-message" style="padding:15px;text-align:center;">Could not load contacts: ${escapeHtml(error.message)}</p>`;
        }
    }

    // --- Handle Contact Selection in Sidebar ---
    chatContactListUL.addEventListener('click', (event) => {
        const clickedItem = event.target.closest('.contact-item');
        if (!clickedItem) return;

        const contactId = parseInt(clickedItem.dataset.contactId, 10);
        const targetUser = clickedItem.dataset.targetUsername;

        if (contactId && targetUser) {
            selectChat(contactId, targetUser);
        }
    });

    function selectChat(contactId, targetUser) {
        if (activeChatContactId === contactId) return; // Already selected

        activeChatContactId = contactId;
        activeChatTargetUsername = targetUser;

        // Highlight active contact in sidebar
        document.querySelectorAll('#chatContactList .contact-item.active-chat').forEach(el => el.classList.remove('active-chat'));
        const activeContactEl = chatContactListUL.querySelector(`.contact-item[data-contact-id="${contactId}"]`);
        if (activeContactEl) activeContactEl.classList.add('active-chat');

        chatCurrentTargetNameHeader.textContent = escapeHtml(targetUser);
        chatCurrentTargetAvatar.textContent = targetUser ? targetUser.substring(0,2).toUpperCase() : '';
        chatCurrentTargetAvatar.style.display = 'flex';
        messagesContainer.innerHTML = ''; // Clear previous messages
        chatInputAreaDiv.style.display = 'flex'; // Show input area
        messageInput.disabled = false;
        sendMessageButton.disabled = false;
        messageInput.focus();

        loadMessages(activeChatContactId);
    }


    // --- Load Messages for selected chat ---
    async function loadMessages(chatId) {
        if (!chatId || typeof chatId !== 'number') {
            console.error("[CHAT_PAGE] Invalid chatId for loading messages:", chatId);
            messagesContainer.innerHTML = `<p class="error-message">Error: Invalid chat session.</p>`;
            return;
        }
        messagesContainer.innerHTML = '<p class="loading" style="padding:15px;text-align:center;">Loading messages...</p>';
        try {
            const messages = await apiCall(`/api/chat/${chatId}`);
            messagesContainer.innerHTML = '';
            if (Array.isArray(messages) && messages.length > 0) {
                messages.forEach(msg => displayMessage(msg));
            } else {
                messagesContainer.innerHTML = '<p class="no-data" style="padding:15px;text-align:center;">No messages in this chat yet.</p>';
            }
            scrollToBottom();
        } catch (error) {
            console.error("[CHAT_PAGE] Error loading messages:", error);
            messagesContainer.innerHTML = `<p class="error-message" style="padding:15px;text-align:center;">Could not load messages: ${escapeHtml(error.message)}</p>`;
        }
    }

    // --- Display Message ---
    function displayMessage(message) {
        if (!message || typeof message.text !== 'string') return;
        const noDataOrLoading = messagesContainer.querySelector('.no-data, .loading');
        if (noDataOrLoading) noDataOrLoading.remove();

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');
        const senderSpan = document.createElement('span');
        senderSpan.classList.add('sender-name');

        if (message.sender === loggedInUsername) {
            messageDiv.classList.add('sent');
            senderSpan.textContent = 'You';
        } else {
            messageDiv.classList.add('received');
            senderSpan.textContent = escapeHtml(message.sender || 'Unknown');
        }
        messageDiv.appendChild(senderSpan);
        messageDiv.appendChild(document.createTextNode(message.text));
        messagesContainer.appendChild(messageDiv);
        scrollToBottom();
    }

    // --- Send Message ---
    async function handleSendMessage() {
        const text = messageInput.value.trim();
        if (!text || !activeChatContactId || typeof activeChatContactId !== 'number') {
            if (typeof activeChatContactId !== 'number') alert("Error: No active chat selected or chat session is invalid.");
            return;
        }

        sendMessageButton.disabled = true;
        const originalSendBtnHTML = sendMessageButton.innerHTML;
        sendMessageButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const newMessage = await apiCall('/api/send-message', 'POST', { contact_id: activeChatContactId, text: text });
            displayMessage(newMessage);
            messageInput.value = '';
            // Potentially update last message preview in sidebar (more advanced)
        } catch (error) {
            console.error("[CHAT_PAGE] Error sending message:", error);
            alert(`Could not send message: ${escapeHtml(error.message)}`);
        } finally {
            sendMessageButton.disabled = false;
            sendMessageButton.innerHTML = originalSendBtnHTML;
            messageInput.focus();
        }
    }

    function scrollToBottom() {
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    // --- Page Initialization ---
    async function initializeChatPage() {
        const userLoggedIn = await fetchLoggedInUser();
        if (!userLoggedIn) {
            chatCurrentTargetNameHeader.textContent = "Authentication Required";
            messagesContainer.innerHTML = '<p class="error-message">Please <a href="/">log in</a> to use chat.</p>';
            chatInputAreaDiv.style.display = 'none';
            return;
        }

        await loadChatContacts(); // Load the sidebar

        // Check for URL parameter to pre-select a chat
        const urlParams = new URLSearchParams(window.location.search);
        const chatWithUserFromQuery = urlParams.get('user');

        if (chatWithUserFromQuery) {
            if (chatWithUserFromQuery === loggedInUsername) {
                chatCurrentTargetNameHeader.textContent = "Error";
                messagesContainer.innerHTML = '<p class="error-message">You cannot start a chat with yourself.</p>';
                chatInputAreaDiv.style.display = 'none';
                return;
            }
            // Need to get/create session then select it
            console.log(`[CHAT_PAGE] Pre-selecting chat with: ${chatWithUserFromQuery} from URL param.`);
            try {
                const sessionData = await apiCall(`/api/chat/session/with/${encodeURIComponent(chatWithUserFromQuery)}`);
                if (sessionData && typeof sessionData.chat_id === 'number') {
                    // Check if this contact is already in the sidebar, if not, loadChatContacts might need a refresh
                    // or we add it dynamically if it's a brand new chat not yet in "my-contacts"
                    // For simplicity now, we assume loadChatContacts would eventually show it.
                    // The best UX would be to ensure it's in the sidebar and selected.
                    // For now, just directly select it.
                    selectChat(sessionData.chat_id, chatWithUserFromQuery);
                } else {
                     throw new Error("Failed to get chat session for user from URL.");
                }
            } catch (error) {
                 console.error("Error pre-selecting chat from URL:", error);
                 messagesContainer.innerHTML = `<p class="error-message">Could not initiate chat with ${escapeHtml(chatWithUserFromQuery)}: ${escapeHtml(error.message)}</p>`;
                 chatInputAreaDiv.style.display = 'none';
            }
        } else {
            // No specific user in URL, show placeholder in main chat area
            messagesContainer.innerHTML = `
                <div class="chat-placeholder">
                    <i class="fas fa-comments"></i>
                    <p>Select a conversation from the left sidebar.</p>
                </div>`;
            chatInputAreaDiv.style.display = 'none';
        }
    }

    // --- Event Listeners ---
    sendMessageButton.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSendMessage();
        }
    });
    if (backToNetworkButton) {
        backToNetworkButton.addEventListener('click', () => {
            window.location.href = '/connection.html';
        });
    }

    // --- START CHAT PAGE INITIALIZATION ---
    initializeChatPage();
});