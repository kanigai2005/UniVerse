// static/connection.js (CORRECTED FOR REDIRECTION)

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
    console.log("Connections Page DOM Loaded - Version: REDIRECTION_ONLY");

    // --- Element References ---
    const connectionsListContainer = document.getElementById('connections-list');
    const suggestionsListContainer = document.getElementById('suggestions-list');
    const pendingRequestsListContainer = document.getElementById('pending-requests-list');
    const userSearchInput = document.getElementById('user-search-input');
    const userSearchButton = document.getElementById('user-search-button');
    const searchResultsListContainer = document.getElementById('search-results-list');
    const togglePendingRequestsBtn = document.getElementById('toggle-pending-requests-btn');
    const pendingRequestsSection = document.getElementById('pending-requests-section');
    let pendingRequestsCountSpan = document.getElementById('pending-requests-count');
    const showMoreConnectionsBtn = document.getElementById('show-more-connections-btn');

    // --- State ---
    let currentUsername = null;
    let currentUserData = null;
    let allFetchedConnections = [];
    let displayedConnectionsCount = 0;
    const CONNECTIONS_PER_PAGE = 9;

    // --- Check Core Elements (No chat pop-up elements here) ---
    const essentialElements = {
        connectionsListContainer, suggestionsListContainer, pendingRequestsListContainer,
        userSearchInput, userSearchButton, searchResultsListContainer,
        togglePendingRequestsBtn, pendingRequestsSection, pendingRequestsCountSpan, showMoreConnectionsBtn
    };
    for (const elName in essentialElements) {
        if (!essentialElements[elName]) {
            console.error(`CRITICAL: UI element '${elName}' is missing! Page may not function correctly.`);
            // You might want to display a more user-friendly error on the page itself
            return;
        }
    }

    // --- Helper to fetch current user ---
    async function fetchCurrentUser() {
        console.log("Attempting to fetch current user...");
        try {
            const response = await fetch('/api/users/me');
            if (!response.ok) {
                if (response.status === 401 || response.status === 307) {
                    console.warn("User not authenticated, redirecting to login.");
                    window.location.href = '/?error=Session+expired';
                } else {
                    console.error("fetchCurrentUser failed with status:", response.status, await response.text());
                }
                return null;
            }
            const userData = await response.json();
            if (userData && userData.username && typeof userData.id === 'number') {
                currentUserData = userData;
                currentUsername = userData.username;
                console.log("Current user fetched:", currentUsername, "ID:", currentUserData.id);
                return currentUserData;
            }
            console.warn("User data fetched but username or ID missing or ID not a number.", userData);
            return null;
        } catch (error) {
            console.error('Error in fetchCurrentUser:', error);
            return null;
        }
    }

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

    // --- UI Update Helpers ---
    function updateListContainer(container, items, itemCreatorFunc, noDataMessage, itemType, isOwnPage = false) {
        if (!container) { console.error("updateListContainer: container is null for itemType", itemType); return; }
        container.innerHTML = '';
        if (!Array.isArray(items) || items.length === 0) {
            container.innerHTML = `<p class="no-data">${escapeHtml(noDataMessage)}</p>`;
            if (container === connectionsListContainer && showMoreConnectionsBtn) showMoreConnectionsBtn.classList.add('hidden');
            return;
        }
        items.forEach(item => container.appendChild(itemCreatorFunc(item, itemType, isOwnPage)));
    }

    // --- Fetch Connections ---
    async function fetchConnections(usernameToFetchFor = currentUsername) {
        if (!usernameToFetchFor) { console.warn("fetchConnections: usernameToFetchFor is missing"); return; }
        connectionsListContainer.innerHTML = '<p class="loading">Loading connections...</p>';
        if (showMoreConnectionsBtn) showMoreConnectionsBtn.classList.add('hidden');
        try {
            const connections = await apiCall(`/api/users/${encodeURIComponent(usernameToFetchFor)}/connections`);
            allFetchedConnections = Array.isArray(connections) ? connections : [];
            displayedConnectionsCount = 0;
            connectionsListContainer.innerHTML = '';
            displayMoreConnections(usernameToFetchFor);
        } catch (error) {
            connectionsListContainer.innerHTML = `<p class="error-message">Could not load connections: ${escapeHtml(error.message)}</p>`;
        }
    }

    function displayMoreConnections(displayedUsername) {
        const isOwn = (currentUsername === displayedUsername);
        const newConnections = allFetchedConnections.slice(displayedConnectionsCount, displayedConnectionsCount + CONNECTIONS_PER_PAGE);
        if (newConnections.length === 0 && displayedConnectionsCount === 0) {
            updateListContainer(connectionsListContainer, [], createUserListItem, "No connections yet. Find new people!", 'connection', isOwn);
            return;
        }
        newConnections.forEach(user => {
            connectionsListContainer.appendChild(createUserListItem(user, 'connection', isOwn));
        });
        displayedConnectionsCount += newConnections.length;
        if (showMoreConnectionsBtn) {
            showMoreConnectionsBtn.classList.toggle('hidden', displayedConnectionsCount >= allFetchedConnections.length);
        }
    }

    // --- Fetch and Display Suggestions ---
    async function fetchSuggestions() {
        if (!currentUsername) { console.warn("fetchSuggestions: currentUsername is missing"); return; }
        suggestionsListContainer.innerHTML = '<p class="loading">Loading suggestions...</p>';
        try {
            const suggestions = await apiCall(`/api/users/${encodeURIComponent(currentUsername)}/suggestions`);
            updateListContainer(suggestionsListContainer, suggestions.slice(0, 9), createUserListItem, "No new suggestions right now.", 'suggestion');
        } catch (error) {
            suggestionsListContainer.innerHTML = `<p class="error-message">Could not load suggestions: ${escapeHtml(error.message)}</p>`;
        }
    }

    // --- Fetch and Display Pending Requests ---
    async function fetchPendingRequests() {
        if (!currentUserData) { console.warn("fetchPendingRequests: currentUserData is missing"); return; }
        if (!pendingRequestsSection.classList.contains('hidden')) {
            pendingRequestsListContainer.innerHTML = '<p class="loading">Loading requests...</p>';
        }
        try {
            const requests = await apiCall(`/api/connections/requests/pending`);
            const numRequests = Array.isArray(requests) ? requests.length : 0;
            pendingRequestsCountSpan.textContent = `(${numRequests})`;
            togglePendingRequestsBtn.classList.toggle('has-requests', numRequests > 0);
            if (!pendingRequestsSection.classList.contains('hidden') || numRequests > 0) {
                 updateListContainer(pendingRequestsListContainer, requests, createPendingRequestItem, "No pending connection requests.", 'pending-request');
            } else if (numRequests === 0 && !pendingRequestsSection.classList.contains('hidden')) {
                 pendingRequestsListContainer.innerHTML = '<p class="no-data">No pending connection requests.</p>';
            }
        } catch (error) {
            if (!pendingRequestsSection.classList.contains('hidden')) {
                 pendingRequestsListContainer.innerHTML = `<p class="error-message">Could not load pending requests: ${escapeHtml(error.message)}</p>`;
            }
            pendingRequestsCountSpan.textContent = '(E)';
            togglePendingRequestsBtn.classList.remove('has-requests');
        }
    }

    function createPendingRequestItem(req) {
        if (!req || typeof req.requester_id !== 'number' || typeof req.requester_username !== 'string' || !req.requester_username) {
            console.warn("Invalid pending request data:", req);
            const errorCard = document.createElement('div'); errorCard.classList.add('user-card');
            errorCard.innerHTML = `<div class="user-info"><span class="username" style="color:red;">Data Error</span></div>`;
            return errorCard;
        }
        const item = document.createElement('div');
        item.classList.add('user-card');
        const requestedAt = req.requested_at ? new Date(req.requested_at).toLocaleDateString() : 'Unknown date';
        item.innerHTML = `
            <div class="avatar-placeholder">${escapeHtml(req.requester_username.substring(0,2).toUpperCase())}</div>
            <div class="user-info">
                <span class="username">${escapeHtml(req.requester_username)}</span>
                <span class="profession">${escapeHtml(req.requester_profession || 'Profession not specified')}</span>
                <span class="request-date">Requested: ${escapeHtml(requestedAt)}</span>
            </div>
            <div class="user-actions">
                <button class="accept-btn" data-requester-id="${req.requester_id}"><i class="fas fa-check"></i> Accept</button>
                <button class="ignore-btn" data-requester-id="${req.requester_id}"><i class="fas fa-times"></i> Ignore</button>
                <button class="view-profile-btn" data-username="${escapeHtml(req.requester_username)}"><i class="fas fa-user"></i> View</button>
            </div>`;
        return item;
    }

    // --- Search Users ---
    async function searchUsers() {
        if (!currentUserData) {
            searchResultsListContainer.innerHTML = '<p class="error-message">Please log in to search.</p>'; return;
        }
        const searchTerm = userSearchInput.value.trim();
        if (searchTerm.length < 2) {
            searchResultsListContainer.innerHTML = '<p class="no-data">Enter at least 2 characters.</p>';
            return;
        }
        searchResultsListContainer.innerHTML = '<p class="loading">Searching...</p>';
        try {
            const users = await apiCall(`/api/users/searchable?term=${encodeURIComponent(searchTerm)}`);
            updateListContainer(searchResultsListContainer, users, createUserListItem, `No users found matching "${escapeHtml(searchTerm)}".`, 'search_result');
        } catch (error) {
            searchResultsListContainer.innerHTML = `<p class="error-message">Search failed: ${escapeHtml(error.message)}</p>`;
        }
    }

    // --- Create User Card Item ---
    function createUserListItem(user, type, isForOwnConnectionsPage = false) {
        if (!user || typeof user.id !== 'number' || typeof user.username !== 'string' || !user.username) {
             console.warn(`Invalid user data for list item (type: ${type}):`, user);
             const errorCard = document.createElement('div'); errorCard.classList.add('user-card');
             errorCard.innerHTML = `<div class="user-info"><span class="username" style="color:red;">User Data Error</span><span class="profession">Required info missing</span></div>`;
             return errorCard;
        }
        const card = document.createElement('div');
        card.classList.add('user-card');
        const avatarInitials = escapeHtml(user.username.substring(0,2).toUpperCase());

        let actionButtonsHtml = '';
        if (type === 'connection') {
            actionButtonsHtml = `<button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Profile</button>`;
            if (isForOwnConnectionsPage) {
                actionButtonsHtml += `
                    <button class="message-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-comment-dots"></i> Message</button>
                    <button class="remove-conn-btn" data-username="${escapeHtml(user.username)}" title="Remove Connection"><i class="fas fa-user-times"></i></button>`;
            }
        } else if (type === 'suggestion' || type === 'search_result') {
             actionButtonsHtml = `
                <button class="request-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-plus"></i> Send Request</button>
                <button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Profile</button>`;
        }

        card.innerHTML = `
            <div class="avatar-placeholder">${avatarInitials}</div>
            <div class="user-info">
                <span class="username">${escapeHtml(user.username)}</span>
                <span class="profession">${escapeHtml(user.profession || 'Profession not specified')}</span>
            </div>
            <div class="user-actions">${actionButtonsHtml}</div>`;
        return card;
    }

    // --- Action Event Handlers (Delegated) ---
    document.body.addEventListener('click', async (event) => {
        const button = event.target.closest('button');
        if (!button) return;

        if (!currentUserData && !button.classList.contains('view-profile-btn') && !button.classList.contains('message-btn')) {
            console.warn("User data not loaded, action blocked (except profile/message navigation).");
            return;
        }

        const username = button.dataset.username;
        const requesterIdStr = button.dataset.requesterId;
        const requesterId = requesterIdStr ? parseInt(requesterIdStr, 10) : null;

        const originalButtonHtml = button.innerHTML;

        if (button.classList.contains('message-btn') || button.classList.contains('view-profile-btn')) {
            button.disabled = true; // Briefly disable navigation buttons
        } else {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }

        try {
            if (button.classList.contains('view-profile-btn') && username) {
                window.location.href = `/profile.html?username=${encodeURIComponent(username)}`;
                // Button will be re-enabled on page load or if navigation fails by browser
            } else if (button.classList.contains('message-btn') && username) {
                console.log(`[ConnectionsPage] Message button for ${username}. Redirecting to chat.html?user=${encodeURIComponent(username)}`);
                window.location.href = `/chat.html?user=${encodeURIComponent(username)}`;
                // Button will be re-enabled on page load or if navigation fails
            } else if (button.classList.contains('request-btn') && username) {
                await sendConnectionRequestAction(username, button, originalButtonHtml);
            } else if (button.classList.contains('accept-btn') && Number.isInteger(requesterId)) {
                await acceptRequestAction(requesterId, button, originalButtonHtml);
            } else if (button.classList.contains('ignore-btn') && Number.isInteger(requesterId)) {
                await ignoreRequestAction(requesterId, button, originalButtonHtml);
            } else if (button.classList.contains('remove-conn-btn') && username) {
                await removeConnectionAction(username, button, originalButtonHtml);
            } else {
                // If no specific action matched, and it wasn't a nav button
                if (!button.classList.contains('view-profile-btn') && !button.classList.contains('message-btn')) {
                    button.disabled = false;
                    button.innerHTML = originalButtonHtml;
                }
            }
        } catch (error) {
            console.error("Error in delegated action handler:", error);
            // Restore button state if it wasn't a navigation/redirection one
            if (!button.classList.contains('view-profile-btn') && !button.classList.contains('message-btn')) {
                 button.disabled = false;
                 button.innerHTML = originalButtonHtml;
            } else if (button.classList.contains('message-btn') || button.classList.contains('view-profile-btn')) {
                // Re-enable navigation buttons if the navigation itself failed or was blocked
                button.disabled = false;
            }
        }
    });

    async function sendConnectionRequestAction(targetUsername, button, originalHtml) {
        try {
            const result = await apiCall(`/api/connections/request/${encodeURIComponent(targetUsername)}`, 'POST');
            alert(result.message || "Request sent!");
            button.innerHTML = 'Sent';
            button.classList.remove('request-btn');
            button.classList.add('sent');
            // Keep button disabled as 'Sent'
            await Promise.all([fetchSuggestions(), (userSearchInput.value.trim().length > 0 ? searchUsers() : Promise.resolve())]);
        } catch (error) {
            alert(`Could not send request: ${escapeHtml(error.message)}`);
            button.disabled = false; button.innerHTML = originalHtml;
        }
    }

    async function acceptRequestAction(requesterId, button, originalHtml) {
        const parentItem = button.closest('.user-card');
        try {
            const result = await apiCall(`/api/connections/requests/accept/${requesterId}`, 'POST');
            alert(result.message || "Request accepted!");
            if(parentItem) { parentItem.style.transition = 'opacity 0.5s ease'; parentItem.style.opacity = '0'; }
            setTimeout(async () => {
                if(parentItem) parentItem.remove();
                await Promise.all([fetchConnections(), fetchSuggestions(), fetchPendingRequests()]);
            }, 500);
        } catch (error) {
            alert(`Could not accept request: ${escapeHtml(error.message)}`);
            button.disabled = false; button.innerHTML = originalHtml;
        }
    }

    async function ignoreRequestAction(requesterId, button, originalHtml) {
        const parentItem = button.closest('.user-card');
        try {
            const result = await apiCall(`/api/connections/requests/ignore/${requesterId}`, 'POST');
            alert(result.message || "Request ignored.");
            if(parentItem) { parentItem.style.transition = 'opacity 0.5s ease'; parentItem.style.opacity = '0'; }
            setTimeout(async () => {
                 if(parentItem) parentItem.remove();
                 await fetchPendingRequests();
            }, 500);
        } catch (error) {
            alert(`Could not ignore request: ${escapeHtml(error.message)}`);
            button.disabled = false; button.innerHTML = originalHtml;
        }
    }

    async function removeConnectionAction(targetUsername, button, originalHtml) {
        if (!confirm(`Are you sure you want to remove ${escapeHtml(targetUsername)} from your connections?`)) {
             button.disabled = false; button.innerHTML = originalHtml; return;
        }
        const parentItem = button.closest('.user-card');
        try {
            const result = await apiCall(`/api/connections/${encodeURIComponent(targetUsername)}`, 'DELETE');
            alert(result.message || "Connection removed.");
            if(parentItem) { parentItem.style.transition = 'opacity 0.5s ease'; parentItem.style.opacity = '0'; }
            setTimeout(async () => {
                 if(parentItem) parentItem.remove();
                 else await fetchConnections(); // Fallback refresh
                 await fetchSuggestions();
            }, 500);
        } catch (error) {
            alert(`Could not remove connection: ${escapeHtml(error.message)}`);
            button.disabled = false; button.innerHTML = originalHtml;
        }
    }

    // --- Initialize Page ---
    async function initializeConnectionPage() {
        await fetchCurrentUser();
        if (!currentUsername) {
            console.error("CRITICAL: Page initialization failed - current user not available.");
            if (connectionsListContainer) connectionsListContainer.innerHTML = '<p class="error-message">Could not load your data. Please log in again.</p>';
            [userSearchInput, userSearchButton, togglePendingRequestsBtn].forEach(el => { if(el) el.disabled = true; });
            return;
        }
        const pageTitle = document.querySelector('.top-nav .nav-title');
        if (pageTitle) pageTitle.textContent = "My Network";

        document.querySelectorAll('.section-card, .toggle-requests-container').forEach(el => {
            if(el) el.style.display = 'block';
        });
        if (pendingRequestsSection && pendingRequestsSection.classList.contains('hidden')) {
            // initial hidden state is respected
        } else if (pendingRequestsSection) {
             pendingRequestsSection.style.display = 'block';
        }

        fetchConnections();
        fetchSuggestions();
        fetchPendingRequests();
    }

    // --- Attach General Event Listeners ---
    if (userSearchButton) userSearchButton.addEventListener('click', searchUsers);
    if (userSearchInput) {
        userSearchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { e.preventDefault(); searchUsers(); } });
        let searchDebounceTimer;
        userSearchInput.addEventListener('input', () => {
            clearTimeout(searchDebounceTimer);
            const searchTerm = userSearchInput.value.trim();
            if (searchTerm.length === 0) {
                if (searchResultsListContainer) searchResultsListContainer.innerHTML = '<p class="no-data">Enter a name or profession to find users.</p>';
            } else if (searchTerm.length >= 2) {
                searchDebounceTimer = setTimeout(searchUsers, 400);
            }
        });
    }

    if (togglePendingRequestsBtn) {
        togglePendingRequestsBtn.addEventListener('click', () => {
            const isHidden = pendingRequestsSection.classList.toggle('hidden');
            const iconClass = isHidden ? 'fa-user-clock' : 'fa-eye-slash';
            const buttonText = isHidden ? 'View Pending Requests' : 'Hide Pending Requests';
            const currentCountText = pendingRequestsCountSpan.textContent || '(0)'; // Read before changing innerHTML
            togglePendingRequestsBtn.innerHTML = `<i class="fas ${iconClass}"></i> ${buttonText} <span class="count-badge" id="pending-requests-count">${currentCountText}</span>`;
            // After innerHTML is replaced, the old 'pendingRequestsCountSpan' reference is no longer valid.
            // We need to get the new reference if we intend to update its textContent again without re-reading from the button.
            // However, since fetchPendingRequests updates it anyway, this might not be strictly necessary here
            // unless other functions directly manipulate pendingRequestsCountSpan.textContent later.
            // For safety, re-assign:
            pendingRequestsCountSpan = document.getElementById('pending-requests-count');


            if (!isHidden && (pendingRequestsListContainer.innerHTML.includes('loading') || pendingRequestsListContainer.children.length === 0 || pendingRequestsListContainer.querySelector('.no-data'))) {
                fetchPendingRequests();
            }
        });
    }

    if (showMoreConnectionsBtn) {
        showMoreConnectionsBtn.addEventListener('click', () => displayMoreConnections(currentUsername));
    }

    // --- START INITIALIZATION ---
    initializeConnectionPage();
});