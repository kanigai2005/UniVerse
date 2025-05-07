// --- Utility: Simple HTML Escaping ---
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') { return unsafe === null || unsafe === undefined ? '' : unsafe; }
    // Corrected escaping for all necessary characters
    return unsafe
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
}

document.addEventListener('DOMContentLoaded', async () => {
    console.log("Connections Page DOM Loaded.");

    // --- Element References ---
    const connectionsListContainer = document.getElementById('connections-list');
    const suggestionsListContainer = document.getElementById('suggestions-list');
    const pendingRequestsListContainer = document.getElementById('pending-requests-list');
    const userSearchInput = document.getElementById('user-search-input');
    const userSearchButton = document.getElementById('user-search-button');
    const searchResultsListContainer = document.getElementById('search-results-list');
    const togglePendingRequestsBtn = document.getElementById('toggle-pending-requests-btn');
    const pendingRequestsSection = document.getElementById('pending-requests-section');
    const pendingRequestsCountSpan = document.getElementById('pending-requests-count');
    const showMoreConnectionsBtn = document.getElementById('show-more-connections-btn');

    // --- State ---
    let currentUsername = null;
    let currentUserData = null; // Store full current user object
    let allFetchedConnections = [];
    let displayedConnectionsCount = 0;
    const CONNECTIONS_PER_PAGE = 9; // Number of connection cards per 'page'

    // --- Check Core Elements ---
    if (!connectionsListContainer || !suggestionsListContainer || !pendingRequestsListContainer ||
        !userSearchInput || !userSearchButton || !searchResultsListContainer ||
        !togglePendingRequestsBtn || !pendingRequestsSection || !pendingRequestsCountSpan || !showMoreConnectionsBtn) {
        console.error("CRITICAL: One or more essential UI elements are missing from connections.html!");
        document.body.insertAdjacentHTML('afterbegin', '<p style="background:red; color:white; padding:10px; text-align:center; position:fixed; top: 60px; width:100%; z-index:1001;">Page Error: UI elements missing.</p>');
        return; // Stop initialization
    }

    // --- Helper to fetch current user ---
    async function fetchCurrentUser() {
        console.log("Attempting to fetch current user...");
        try {
            const response = await fetch('/api/users/me');
            if (!response.ok) {
                if (response.status === 401 || response.status === 307) {
                    window.location.href = '/?error=Session+expired'; // Redirect if not authenticated
                }
                return null;
            }
            currentUserData = await response.json();
            if (currentUserData && currentUserData.username) {
                currentUsername = currentUserData.username; // Set global username
                console.log("Current user fetched:", currentUsername);
                return currentUserData; // Return full data
            }
            console.warn("User data fetched but username missing.");
            return null;
        } catch (error) {
            console.error('Error in fetchCurrentUser:', error);
            const mainContainer = document.querySelector('.container');
            if (mainContainer && !mainContainer.querySelector('.api-error-message')) {
                mainContainer.insertAdjacentHTML('afterbegin', '<p class="error-message api-error-message" style="padding: 10px; background-color: var(--error-color); color: white;">Could not verify user session. Please log in.</p>');
            }
            return null;
        }
    }

    // --- API Call Helper ---
    async function apiCall(url, method = 'GET', body = null) {
        const options = { method, headers: {} };
        if (body) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
        const response = await fetch(url, options);
        const responseData = await response.json().catch(() => ({}));
        if (!response.ok) {
            const errorMessage = responseData.detail || `Request failed: ${response.status} ${response.statusText}`;
            console.error(`API call to ${url} failed:`, errorMessage, responseData);
            throw new Error(errorMessage);
        }
        return responseData;
    }

    // --- Fetch Connections ---
    async function fetchConnections(usernameToFetchFor) {
        if (!usernameToFetchFor) return;
        connectionsListContainer.innerHTML = '<p class="loading">Loading connections...</p>';
        showMoreConnectionsBtn.classList.add('hidden');
        try {
            const connections = await apiCall(`/api/users/${encodeURIComponent(usernameToFetchFor)}/connections`);
            allFetchedConnections = Array.isArray(connections) ? connections : [];
            displayedConnectionsCount = 0;
            connectionsListContainer.innerHTML = ''; // Clear loading
            displayMoreConnections(usernameToFetchFor); // Display initial batch
        } catch (error) {
            connectionsListContainer.innerHTML = `<p class="error-message">Could not load connections: ${escapeHtml(error.message)}</p>`;
        }
    }

    // --- Display More Connections (Pagination) ---
    function displayMoreConnections(displayedUsername) {
        const isOwn = (currentUsername === displayedUsername);
        const newConnections = allFetchedConnections.slice(displayedConnectionsCount, displayedConnectionsCount + CONNECTIONS_PER_PAGE);

        if (newConnections.length === 0 && displayedConnectionsCount === 0) {
            connectionsListContainer.innerHTML = `<p class="no-data">You have no connections yet.</p>`; // Changed message
            showMoreConnectionsBtn.classList.add('hidden');
            return;
        }

        newConnections.forEach(user => {
            connectionsListContainer.appendChild(createUserListItem(user, 'connection', isOwn));
        });
        displayedConnectionsCount += newConnections.length;
        showMoreConnectionsBtn.classList.toggle('hidden', displayedConnectionsCount >= allFetchedConnections.length);
    }

    // --- Fetch and Display Suggestions ---
    async function fetchSuggestions() {
        if (!currentUsername) return;
        suggestionsListContainer.innerHTML = '<p class="loading">Loading suggestions...</p>';
        try {
            const suggestions = await apiCall(`/api/users/${encodeURIComponent(currentUsername)}/suggestions`);
            console.log("RAW SUGGESTIONS DATA FROM API:", JSON.stringify(suggestions, null, 2));
            displaySuggestions(suggestions);
        } catch (error) {
            suggestionsListContainer.innerHTML = `<p class="error-message">Could not load suggestions: ${escapeHtml(error.message)}</p>`;
        }
    }

    function displaySuggestions(suggestions) {
        suggestionsListContainer.innerHTML = '';
        if (!Array.isArray(suggestions) || suggestions.length === 0) {
            suggestionsListContainer.innerHTML = '<p class="no-data">No new suggestions right now.</p>'; return;
        }
        console.log("Displaying suggestions. First item:", suggestions[0]);
        // Optionally limit suggestions shown initially
        suggestions.slice(0, 9).forEach((user, index) => { // Show 9 suggestions initially
            console.log(`Suggestion item ${index}:`, user);
            suggestionsListContainer.appendChild(createUserListItem(user, 'suggestion'));
        });
    }

    // --- Fetch and Display Pending Requests ---
    async function fetchPendingRequests() {
        if (!currentUserData) return; // Use the full user object check
        if (!pendingRequestsSection.classList.contains('hidden')) {
            pendingRequestsListContainer.innerHTML = '<p class="loading">Loading requests...</p>';
        }
        try {
            const requests = await apiCall(`/api/connections/requests/pending`);
            const numRequests = Array.isArray(requests) ? requests.length : 0;
            pendingRequestsCountSpan.textContent = `(${numRequests})`;
            togglePendingRequestsBtn.classList.toggle('has-requests', numRequests > 0);
            if (!pendingRequestsSection.classList.contains('hidden') || numRequests > 0) {
                displayPendingRequests(requests);
            }
        } catch (error) {
            if (!pendingRequestsSection.classList.contains('hidden')) {
                 pendingRequestsListContainer.innerHTML = `<p class="error-message">Could not load pending requests: ${escapeHtml(error.message)}</p>`;
            }
            pendingRequestsCountSpan.textContent = '(E)';
            togglePendingRequestsBtn.classList.remove('has-requests');
        }
    }

    function displayPendingRequests(requests) {
        pendingRequestsListContainer.innerHTML = '';
        if (!Array.isArray(requests) || requests.length === 0) {
            pendingRequestsListContainer.innerHTML = '<p class="no-data">No pending connection requests.</p>';
            pendingRequestsCountSpan.textContent = '(0)';
            togglePendingRequestsBtn.classList.remove('has-requests');
            return;
        }
        pendingRequestsCountSpan.textContent = `(${requests.length})`;
        togglePendingRequestsBtn.classList.toggle('has-requests', requests.length > 0);
        requests.forEach(req => pendingRequestsListContainer.appendChild(createPendingRequestItem(req)));
    }

    function createPendingRequestItem(req) {
        // Check specifically for requester_username
        if (!req || typeof req.requester_id === 'undefined' || typeof req.requester_username === 'undefined' || req.requester_username === null) {
            console.warn("Invalid pending request data:", req); return document.createElement('div');
        }
        const item = document.createElement('div');
        item.classList.add('user-card');
        item.innerHTML = `
            <div class="avatar-placeholder">${escapeHtml(req.requester_username.substring(0,2).toUpperCase())}</div>
            <div class="user-info">
                <span class="username">${escapeHtml(req.requester_username)}</span>
                <span class="profession">${escapeHtml(req.requester_profession || 'Profession not specified')}</span>
                <span class="request-date">Requested: ${new Date(req.requested_at).toLocaleDateString()}</span>
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
        if (!currentUserData) { searchResultsListContainer.innerHTML = '<p class="error-message">Please log in to search.</p>'; return; }
        const searchTerm = userSearchInput.value.trim();
        if (searchTerm.length < 2) {
            searchResultsListContainer.innerHTML = '<p class="no-data" style="text-align:left; padding-left:0;">Enter at least 2 characters.</p>';
            return;
        }
        searchResultsListContainer.innerHTML = '<p class="loading">Searching...</p>';
        try {
            const users = await apiCall(`/api/users/searchable?term=${encodeURIComponent(searchTerm)}`);
            displaySearchResults(users);
        } catch (error) {
            searchResultsListContainer.innerHTML = `<p class="error-message">Search failed: ${escapeHtml(error.message)}</p>`;
        }
    }

    function displaySearchResults(users) {
        searchResultsListContainer.innerHTML = '';
        if (!Array.isArray(users) || users.length === 0) {
            searchResultsListContainer.innerHTML = '<p class="no-data">No users found.</p>'; return;
        }
        users.forEach(user => searchResultsListContainer.appendChild(createUserListItem(user, 'search_result')));
    }

    // --- Helper to create user card item (for grid) ---
    function createUserListItem(user, type, isForOwnConnectionsPage = false) {
        if (!user || typeof user.id === 'undefined' || typeof user.username !== 'string' || !user.username) { // Stricter check
             console.warn(`Invalid or incomplete user data for list item (type: ${type}):`, user);
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
    function handleUserListActions(event) {
        if (!currentUserData) { // Check if user is loaded before allowing actions
            console.warn("User data not loaded, ignoring action.");
            return;
        }
        const target = event.target.closest('button');
        if (!target) return;

        const username = target.dataset.username;
        const requesterId = target.dataset.requesterId;

        target.disabled = true;
        const originalButtonHtml = target.innerHTML; // Store original content
        target.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; // Generic spinner

        // Use a map for cleaner action dispatch
        const actions = {
            'view-profile-btn': () => {
                if(username) window.location.href = `/profile.html?username=${encodeURIComponent(username)}`;
            },
            'message-btn': () => initiateChat(username),
            'request-btn': () => sendConnectionRequestAction(username, target, originalButtonHtml),
            'accept-btn': () => acceptRequestAction(requesterId, target, originalButtonHtml),
            'ignore-btn': () => ignoreRequestAction(requesterId, target, originalButtonHtml),
            'remove-conn-btn': () => removeConnectionAction(username, target, originalButtonHtml)
        };

        let actionFound = false;
        for (const btnClass in actions) {
            if (target.classList.contains(btnClass)) {
                actions[btnClass]();
                actionFound = true;
                break;
            }
        }

        // Re-enable immediately only for navigation actions
        if (target.classList.contains('view-profile-btn') || target.classList.contains('message-btn')) {
             setTimeout(() => { // Slight delay to allow navigation to start if successful
                  target.disabled = false;
                  target.innerHTML = originalButtonHtml;
              }, 100);
        } else if (!actionFound) {
            // If no action matched, re-enable immediately
             target.disabled = false;
             target.innerHTML = originalButtonHtml;
        }
    }

    async function initiateChat(targetUsername) { /* ... (keep as before) ... */ }

    async function sendConnectionRequestAction(targetUsername, button, originalHtml) {
        try {
            const result = await apiCall(`/api/connections/request/${encodeURIComponent(targetUsername)}`, 'POST');
            alert(result.message || "Request sent!");
            button.textContent = 'Request Sent';
            button.classList.remove('request-btn'); // Remove old class
            button.classList.add('sent'); // Add new class for styling
            // Keep button disabled after sending
            fetchSuggestions(); // Refresh suggestions
            if (userSearchInput.value.trim().length > 0) searchUsers();
        } catch (error) {
            alert(`Could not send request: ${escapeHtml(error.message)}`);
            button.disabled = false; button.innerHTML = originalHtml; // Restore on error
        }
    }

    async function acceptRequestAction(requesterId, button, originalHtml) {
        const parentItem = button.closest('.user-card');
        button.textContent = 'Accepting...'; // Keep spinner from handleUserListActions
        try {
            const result = await apiCall(`/api/connections/requests/accept/${requesterId}`, 'POST');
            alert(result.message || "Request accepted! Almagems awarded.");
            if(parentItem) parentItem.remove();
            fetchConnections(); // Use global currentUsername
            fetchSuggestions();
            fetchPendingRequests();
        } catch (error) {
            alert(`Could not accept request: ${escapeHtml(error.message)}`);
            button.disabled = false; button.innerHTML = originalHtml; // Restore on error
        }
    }

    async function ignoreRequestAction(requesterId, button, originalHtml) {
        const parentItem = button.closest('.user-card');
        button.textContent = 'Ignoring...';
        try {
            const result = await apiCall(`/api/connections/requests/ignore/${requesterId}`, 'POST');
            alert(result.message || "Request ignored.");
            if(parentItem) parentItem.remove();
            fetchPendingRequests();
        } catch (error) {
            alert(`Could not ignore request: ${escapeHtml(error.message)}`);
            button.disabled = false; button.innerHTML = originalHtml;
        }
    }
    async function removeConnectionAction(targetUsername, button, originalHtml) {
        if (!confirm(`Are you sure you want to remove ${targetUsername}?`)) {
             button.disabled = false; button.innerHTML = originalHtml; return;
        }
        const parentItem = button.closest('.user-card');
        try {
            const result = await apiCall(`/api/connections/${encodeURIComponent(targetUsername)}`, 'DELETE');
            alert(result.message || "Connection removed.");
            if(parentItem) parentItem.remove(); // Remove directly
            else fetchConnections(currentUsername); // Fallback refresh
            fetchSuggestions();
        } catch (error) {
            alert(`Could not remove connection: ${escapeHtml(error.message)}`);
            button.disabled = false; button.innerHTML = originalHtml;
        }
    }

    // --- Initialize Page ---
    async function initializeConnectionPage() {
        await fetchCurrentUser(); // Fetch current user data first
        if (!currentUsername) { 
            console.error("Cannot initialize page: current user not available.");
            connectionsListContainer.innerHTML = '<p class="error-message">Could not load page data. Please try logging in again.</p>';
            suggestionsListContainer.innerHTML = '';
            pendingRequestsListContainer.innerHTML = '';
            searchResultsListContainer.innerHTML = '';
            return; }

        // Page is always "My Network"
        const pageTitle = document.querySelector('.top-nav .nav-title');
        if (pageTitle) pageTitle.textContent = "My Network";

        // Show relevant sections
        document.querySelectorAll('.section-card, .toggle-requests-container').forEach(el => {
            if (el.id === 'pending-requests-section') {
                // Visibility for pending-requests-section is handled by its 'hidden' class
                // No explicit style.display setting needed here if it's not hidden by class
                if (!el.classList.contains('hidden')) {
                    el.style.display = 'block'; // Or 'grid' if it's a grid container directly
                }
            } else {
                el.style.display = 'block'; // Make other sections visible
            }
        });
        // Fetch data for the logged-in user
        fetchConnections(currentUsername);
        fetchSuggestions();
        fetchPendingRequests();
    }

    // --- Attach Global Event Listeners ---
    connectionsListContainer?.addEventListener('click', handleUserListActions);
    suggestionsListContainer?.addEventListener('click', handleUserListActions);
    pendingRequestsListContainer?.addEventListener('click', handleUserListActions);
    searchResultsListContainer?.addEventListener('click', handleUserListActions);

    if (userSearchButton && userSearchInput) {
        userSearchButton.addEventListener('click', searchUsers);
        userSearchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { e.preventDefault(); searchUsers(); } });
        let searchDebounceTimer;
        userSearchInput.addEventListener('input', () => { clearTimeout(searchDebounceTimer); searchDebounceTimer = setTimeout(searchUsers, 400); });
    }

    if (togglePendingRequestsBtn && pendingRequestsSection) {
        togglePendingRequestsBtn.addEventListener('click', () => {
            const isHidden = pendingRequestsSection.classList.toggle('hidden');
            const iconClass = isHidden ? 'fa-user-clock' : 'fa-eye-slash';
            const buttonText = isHidden ? 'View Pending Requests' : 'Hide Pending Requests';
            togglePendingRequestsBtn.innerHTML = `<i class="fas ${iconClass}"></i> ${buttonText} <span class="count-badge" id="pending-requests-count">${pendingRequestsCountSpan.textContent}</span>`;
            if (!isHidden && (pendingRequestsListContainer.innerHTML.includes('loading') || pendingRequestsListContainer.children.length === 0)) {
                fetchPendingRequests(); // Fetch data if opening an empty/loading list
            }
        });
    }

    if (showMoreConnectionsBtn) {
        showMoreConnectionsBtn.addEventListener('click', () => displayMoreConnections(currentUsername));
    }

    // --- START INITIALIZATION ---
    initializeConnectionPage();

}); // End DOMContentLoaded