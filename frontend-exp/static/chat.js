// static/chat.js

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
    const chatCurrentTargetAvatar = document.getElementById('chatCurrentTargetAvatar');
    const messagesContainer = document.getElementById('chatPageMessagesArea');
    const messageInput = document.getElementById('chatPageMessageInput');
    const sendMessageButton = document.getElementById('chatPageSendButton');
    const chatInputAreaDiv = document.getElementById('chatPageInputArea');

    // --- State ---
    let activeChatContactId = null;
    let activeChatTargetUsername = null;
    let loggedInUsername = null;
    let loggedInUserId = null;
    let contactsMap = new Map();

    // --- Check Core Elements ---
    const essentialElements = {
        chatContactListUL, chatCurrentTargetNameHeader, chatCurrentTargetAvatar,
        messagesContainer, messageInput, sendMessageButton, chatInputAreaDiv
    };
    for (const elName in essentialElements) {
        if (!essentialElements[elName]) {
            console.error(`CRITICAL (Chat Page): UI element ID '${elName}' missing!`);
            document.body.insertAdjacentHTML('afterbegin', `<p style="background:red; color:white; padding:10px; text-align:center;">Chat page error: UI component missing. Please contact support.</p>`);
            return;
        }
    }
    chatInputAreaDiv.style.display = 'none';

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
            console.warn("[CHAT_PAGE] Logged-in user data incomplete. Redirecting to login.");
            window.location.href = '/login.html?error=Session+invalid';
            return false;
        } catch (error) {
            console.error("[CHAT_PAGE] Failed to fetch logged-in user:", error);
            window.location.href = '/login.html?error=Session+error';
            return false;
        }
    }

    // --- Load and Display Chat Contacts in Sidebar ---
    async function loadChatContacts() {
        if (!loggedInUserId) return;
        chatContactListUL.innerHTML = '<p class="loading" style="padding:15px;text-align:center;">Loading contacts...</p>';
        try {
            const contacts = await apiCall('/api/chat/my-contacts');
            chatContactListUL.innerHTML = '';
            contactsMap.clear();

            if (Array.isArray(contacts) && contacts.length > 0) {
                contacts.forEach(contact => {
                    if (!contact || typeof contact.contact_id !== 'number' || !contact.other_user_username) {
                        console.warn("[CHAT_PAGE] Invalid contact data received:", contact);
                        return;
                    }
                    contactsMap.set(contact.contact_id, {
                        other_user_username: contact.other_user_username,
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
                chatContactListUL.innerHTML = '<p class="no-data" style="padding:15px;text-align:center;">No active conversations. <a href="/connection.html">Connect with users</a> to start chatting.</p>';
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
            const newUrl = new URL(window.location);
            newUrl.searchParams.set('user', targetUser); // Could also set contact_id
            history.pushState({ contactId: contactId, targetUser: targetUser }, '', newUrl);
            selectChat(contactId, targetUser);
        }
    });

    function selectChat(contactId, targetUser) {
        // Check if already active and messages are loaded (to prevent redundant loads)
        if (activeChatContactId === contactId && messagesContainer.innerHTML !== '' && !messagesContainer.querySelector('.loading, .no-data, .error-message')) {
             messageInput.focus();
             return;
        }

        activeChatContactId = contactId;
        activeChatTargetUsername = targetUser;

        document.querySelectorAll('#chatContactList .contact-item.active-chat').forEach(el => el.classList.remove('active-chat'));
        const activeContactEl = chatContactListUL.querySelector(`.contact-item[data-contact-id="${contactId}"]`);
        if (activeContactEl) activeContactEl.classList.add('active-chat');

        chatCurrentTargetNameHeader.textContent = escapeHtml(targetUser);
        chatCurrentTargetAvatar.textContent = targetUser ? targetUser.substring(0,2).toUpperCase() : '??';
        chatCurrentTargetAvatar.style.display = 'flex';
        messagesContainer.innerHTML = '';
        chatInputAreaDiv.style.display = 'flex';
        messageInput.disabled = false;
        sendMessageButton.disabled = false;
        messageInput.focus();

        loadMessages(activeChatContactId);
    }


    // --- Load Messages for selected chat ---
    async function loadMessages(chatContactIdToLoad) {
        if (!chatContactIdToLoad || typeof chatContactIdToLoad !== 'number') {
            console.error("[CHAT_PAGE] Invalid chatContactIdToLoad for loading messages:", chatContactIdToLoad);
            messagesContainer.innerHTML = `<p class="error-message">Error: Invalid chat session ID.</p>`;
            return;
        }
        messagesContainer.innerHTML = '<p class="loading" style="padding:15px;text-align:center;">Loading messages...</p>';
        try {
            const messages = await apiCall(`/api/chat/${chatContactIdToLoad}`);
            console.log(`[CHAT_PAGE] Raw messages received for contact ID ${chatContactIdToLoad}:`, JSON.parse(JSON.stringify(messages))); // Log raw API response
            messagesContainer.innerHTML = '';
            if (Array.isArray(messages) && messages.length > 0) {
                messages.forEach(msg => displayMessage(msg));
            } else {
                messagesContainer.innerHTML = '<p class="no-data" style="padding:15px;text-align:center;">No messages in this chat yet. Send one!</p>';
            }
            scrollToBottom();
        } catch (error) {
            console.error("[CHAT_PAGE] Error loading messages:", error);
            messagesContainer.innerHTML = `<p class="error-message" style="padding:15px;text-align:center;">Could not load messages: ${escapeHtml(error.message)}</p>`;
        }
    }

    // --- Display Message ---
    // MODIFIED HERE TO USE message.sender
    function displayMessage(message) {
        // The console log shows the backend is sending 'sender' field
        const senderName = message.sender; // USE 'sender' FIELD

        if (!message || typeof message.text !== 'string' || !senderName) {
            console.warn("[CHAT_PAGE] Invalid message object received for display (missing text or sender):", message);
            return;
        }

        const noDataOrLoading = messagesContainer.querySelector('.no-data, .loading');
        if (noDataOrLoading) noDataOrLoading.remove();

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');
        // const senderSpan = document.createElement('span'); // Optional sender name display
        // senderSpan.classList.add('sender-name');

        if (senderName === loggedInUsername) { // Compare with the global loggedInUsername
            messageDiv.classList.add('sent');
            // senderSpan.textContent = 'You';
        } else {
            messageDiv.classList.add('received');
            // senderSpan.textContent = escapeHtml(senderName);
        }
        // if (senderSpan.textContent) messageDiv.appendChild(senderSpan); // Optional

        const textNode = document.createElement('span');
        textNode.textContent = escapeHtml(message.text);
        messageDiv.appendChild(textNode);

        if (message.timestamp) {
            const timeSpan = document.createElement('span');
            timeSpan.style.fontSize = '0.7em';
            timeSpan.style.color = '#888';
            timeSpan.style.marginLeft = '10px';
            timeSpan.style.display = 'block';
            timeSpan.style.textAlign = (senderName === loggedInUsername) ? 'right' : 'left';
            try {
                timeSpan.textContent = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            } catch (e) {
                console.warn("Invalid timestamp format for message:", message.timestamp);
                timeSpan.textContent = "Invalid time";
            }
            messageDiv.appendChild(timeSpan);
        }

        messagesContainer.appendChild(messageDiv);
        scrollToBottom();
    }
    // END OF MODIFICATION

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
            const newMessageData = await apiCall('/api/send-message', 'POST', {
                contact_id: activeChatContactId,
                text: text
            });
            // The backend response from /api/send-message should be a complete ChatMessageOut object
            // which should include the `sender` (or `sender_username`) field correctly.
            console.log("[CHAT_PAGE] Message sent, API response:", newMessageData);
            displayMessage(newMessageData); // Display using the response from API
            messageInput.value = '';

            const contactItemInSidebar = chatContactListUL.querySelector(`.contact-item[data-contact-id="${activeChatContactId}"] .last-message-preview`);
            if (contactItemInSidebar) {
                contactItemInSidebar.textContent = escapeHtml(text.substring(0, 30) + (text.length > 30 ? '...' : ''));
            }

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
            if (messagesContainer) messagesContainer.innerHTML = '<p class="error-message">Please <a href="/login.html">log in</a> to use chat.</p>';
            if (chatInputAreaDiv) chatInputAreaDiv.style.display = 'none';
            if (chatContactListUL) chatContactListUL.innerHTML = '<p class="no-data" style="padding:15px;text-align:center;">Please log in.</p>';
            return;
        }

        await loadChatContacts();

        const urlParams = new URLSearchParams(window.location.search);
        const chatWithUserFromQuery = urlParams.get('user');

        if (chatWithUserFromQuery) {
            if (chatWithUserFromQuery === loggedInUsername) {
                chatCurrentTargetNameHeader.textContent = "Error";
                messagesContainer.innerHTML = '<p class="error-message">You cannot start a chat with yourself.</p>';
                chatInputAreaDiv.style.display = 'none';
                return;
            }
            console.log(`[CHAT_PAGE] Pre-selecting chat with: ${chatWithUserFromQuery} from URL param.`);
            try {
                // This API call should return { chat_id: number }
                const sessionData = await apiCall(`/api/chat/session/with/${encodeURIComponent(chatWithUserFromQuery)}`);
                if (sessionData && typeof sessionData.chat_id === 'number') {
                    selectChat(sessionData.chat_id, chatWithUserFromQuery);
                } else {
                     throw new Error("Failed to get or create chat session. API response did not contain a valid chat_id.");
                }
            } catch (error) {
                 console.error("Error pre-selecting chat from URL:", error);
                 messagesContainer.innerHTML = `<p class="error-message">Could not initiate chat with ${escapeHtml(chatWithUserFromQuery)}: ${escapeHtml(error.message)}</p>`;
                 chatInputAreaDiv.style.display = 'none';
            }
        } else {
            messagesContainer.innerHTML = `
                <div class="chat-placeholder">
                    <i class="fas fa-comments"></i>
                    <p>Select a conversation from the left sidebar.</p>
                    <p>Or, go to <a href="/connection.html" style="color: var(--primary-color); text-decoration: underline;">My Network</a> to start a new chat with one of your connections.</p>
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

    window.addEventListener('popstate', (event) => {
        if (event.state && typeof event.state.contactId === 'number' && event.state.targetUser) {
            console.log("[CHAT_PAGE] Popstate event, selecting chat:", event.state);
            selectChat(event.state.contactId, event.state.targetUser);
        } else {
            activeChatContactId = null;
            activeChatTargetUsername = null;
            document.querySelectorAll('#chatContactList .contact-item.active-chat').forEach(el => el.classList.remove('active-chat'));
            chatCurrentTargetNameHeader.textContent = "Select a chat to start messaging";
            chatCurrentTargetAvatar.style.display = 'none';
            messagesContainer.innerHTML = `
                <div class="chat-placeholder">
                    <i class="fas fa-comments"></i>
                    <p>Select a conversation from the left sidebar.</p>
                     <p>Or, go to <a href="/connection.html" style="color: var(--primary-color); text-decoration: underline;">My Network</a> to start a new chat with one of your connections.</p>
                </div>`;
            chatInputAreaDiv.style.display = 'none';
            console.log("[CHAT_PAGE] Popstate to no active chat.");
        }
    });

    // --- START CHAT PAGE INITIALIZATION ---
    initializeChatPage();
});