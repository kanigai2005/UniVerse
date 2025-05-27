// static/connection.js (JS-Only Search from Connections/Suggestions)

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
    console.log("Connections Page DOM Loaded - Version: JS_INTERNAL_SEARCH");

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

    let allFetchedConnections = []; // For "My Connections" section
    let rawSuggestionsData = []; // For "Suggestions" section
    let combinedSearchableList = []; // For client-side search from connections & suggestions

    let displayedConnectionsCount = 0;
    const CONNECTIONS_PER_PAGE = 9;

    let connectionsFetched = false;
    let suggestionsFetched = false;


    // --- Check Core Elements ---
    const essentialElements = {
        connectionsListContainer, suggestionsListContainer, pendingRequestsListContainer,
        userSearchInput, userSearchButton, searchResultsListContainer,
        togglePendingRequestsBtn, pendingRequestsSection, pendingRequestsCountSpan, showMoreConnectionsBtn
    };
    for (const elName in essentialElements) {
        if (!essentialElements[elName]) {
            console.error(`CRITICAL: UI element '${elName}' is missing! Page may not function correctly.`);
        }
    }

    // --- Helper to fetch current user ---
    async function fetchCurrentUser() {
        console.log("Attempting to fetch current user...");
        try {
            const response = await fetch('/api/users/me', {credentials: 'include'});
            if (!response.ok) {
                if (response.status === 401 || response.status === 307) {
                    console.warn("User not authenticated or session expired.");
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

            if (response.status === 401) {
                console.warn(`API call to ${url} resulted in 401. Redirecting to login.`);
                window.location.href = '/?error=Session+expired_or_unauthorized';
                throw new Error("User not authenticated. Session may have expired.");
            }

            if (contentType && contentType.includes("application/json")) {
                responseData = await response.json();
            } else if (!response.ok) {
                const textError = await response.text();
                throw new Error(textError || `Request failed: ${response.status} ${response.statusText}`);
            }

            if (!response.ok) {
                const errorMessage = responseData.detail || responseData.message || `Request to ${url} failed: ${response.status} ${response.statusText}`;
                throw new Error(errorMessage);
            }
            return responseData;
        } catch (error) {
            if (error.message !== "User not authenticated. Session may have expired.") {
                console.error(`Error during API call to ${url} (method: ${method}):`, error);
            }
            throw error;
        }
    }

    // --- UI Update Helpers ---
    // Note: isOwnPage and isAnonymousView args passed to itemCreatorFunc
    function updateListContainer(container, items, itemCreatorFunc, noDataMessage, itemTypeContext) {
        if (!container) { console.error("updateListContainer: container is null for itemType", itemTypeContext); return; }
        container.innerHTML = '';
        if (!Array.isArray(items) || items.length === 0) {
            container.innerHTML = `<p class="no-data">${escapeHtml(noDataMessage)}</p>`;
            if (container === connectionsListContainer && showMoreConnectionsBtn) showMoreConnectionsBtn.classList.add('hidden');
            return;
        }
        // For 'connection' type, isOwnPage is relevant. For 'search_result' & 'suggestion', isAnonymousView is relevant.
        const isOwnConnectionsPage = itemTypeContext === 'connection' && currentUserData && ( (new URLSearchParams(window.location.search).get('username') || currentUsername) === currentUsername);
        const isEffectivelyAnonymous = !currentUserData; // For search and suggestions if user isn't logged in

        items.forEach(item => container.appendChild(itemCreatorFunc(item, itemTypeContext, isOwnConnectionsPage, isEffectivelyAnonymous)));
    }


    // --- Build Combined List for JS Search ---
    function buildCombinedSearchableList() {
        if (!currentUserData) { // Should not be called if not logged in
            combinedSearchableList = [];
            return;
        }
        console.log("Building combined searchable list from connections and suggestions...");
        const combinedMap = new Map();

        // Add connections
        (Array.isArray(allFetchedConnections) ? allFetchedConnections : []).forEach(user => {
            if (user && typeof user.id === 'number') {
                combinedMap.set(user.id, { ...user, isConnection: true, isSuggestion: false });
            }
        });

        // Add suggestions (and mark if they were already a connection)
        (Array.isArray(rawSuggestionsData) ? rawSuggestionsData : []).forEach(user => {
            if (user && typeof user.id === 'number') {
                if (combinedMap.has(user.id)) {
                    // User is both a connection and was suggested (unlikely, but handle)
                    const existingUser = combinedMap.get(user.id);
                    combinedMap.set(user.id, { ...existingUser, ...user, isSuggestion: true }); // Prioritize connection data but mark as suggestion too
                } else {
                    combinedMap.set(user.id, { ...user, isConnection: false, isSuggestion: true });
                }
            }
        });
        combinedSearchableList = Array.from(combinedMap.values());
        console.log(`Built combined searchable list with ${combinedSearchableList.length} unique users.`);

        // If a search is active, re-filter
        if (userSearchInput && userSearchInput.value.trim().length >=2) {
            searchUsers();
        }
    }


    // --- Fetch Connections (User-Specific) ---
    async function fetchConnections(usernameToFetchFor = currentUsername) {
        connectionsFetched = false;
        if (!usernameToFetchFor) { console.warn("fetchConnections: usernameToFetchFor is missing"); return; }
        if (!connectionsListContainer) return;
        connectionsListContainer.innerHTML = '<p class="loading">Loading connections...</p>';
        if (showMoreConnectionsBtn) showMoreConnectionsBtn.classList.add('hidden');
        try {
            const connections = await apiCall(`/api/users/${encodeURIComponent(usernameToFetchFor)}/connections`);
            allFetchedConnections = Array.isArray(connections) ? connections : [];
            displayedConnectionsCount = 0;
            connectionsListContainer.innerHTML = '';
            displayMoreConnections(usernameToFetchFor);
            connectionsFetched = true;
            if (suggestionsFetched) buildCombinedSearchableList(); // Build if suggestions also done
        } catch (error) {
            connectionsListContainer.innerHTML = `<p class="error-message">Could not load connections: ${escapeHtml(error.message)}</p>`;
            connectionsFetched = true; // Mark as fetched even on error to allow combined list build
            if (suggestionsFetched) buildCombinedSearchableList();
        }
    }

    function displayMoreConnections(displayedUsername) {
        // ... (This function remains largely the same as your provided version,
        // just ensure createUserListItem gets correct args)
        if (!connectionsListContainer) return;
        const isOwn = (currentUsername === displayedUsername);
        const newConnections = allFetchedConnections.slice(displayedConnectionsCount, displayedConnectionsCount + CONNECTIONS_PER_PAGE);
        if (newConnections.length === 0 && displayedConnectionsCount === 0) {
            updateListContainer(connectionsListContainer, [], createUserListItem, "No connections yet. Find new people!", 'connection');
            return;
        }
        newConnections.forEach(user => {
            connectionsListContainer.appendChild(createUserListItem(user, 'connection', isOwn, !currentUserData));
        });
        displayedConnectionsCount += newConnections.length;
        if (showMoreConnectionsBtn) {
            showMoreConnectionsBtn.classList.toggle('hidden', displayedConnectionsCount >= allFetchedConnections.length);
        }
    }

    // --- Fetch and Display Suggestions (User-Specific) ---
    async function fetchSuggestions() {
        suggestionsFetched = false;
        if (!currentUsername) { console.warn("fetchSuggestions: currentUsername is missing"); return; }
        if (!suggestionsListContainer) return;
        suggestionsListContainer.innerHTML = '<p class="loading">Loading suggestions...</p>';
        try {
            const suggestionsApiResult = await apiCall(`/api/users/${encodeURIComponent(currentUsername)}/suggestions`);
            rawSuggestionsData = Array.isArray(suggestionsApiResult) ? suggestionsApiResult : [];
            updateListContainer(suggestionsListContainer, rawSuggestionsData.slice(0, 9), createUserListItem, "No new suggestions right now.", 'suggestion');
            suggestionsFetched = true;
            if (connectionsFetched) buildCombinedSearchableList(); // Build if connections also done
        } catch (error) {
            suggestionsListContainer.innerHTML = `<p class="error-message">Could not load suggestions: ${escapeHtml(error.message)}</p>`;
            suggestionsFetched = true; // Mark as fetched even on error
            if (connectionsFetched) buildCombinedSearchableList();
        }
    }

    // --- Fetch and Display Pending Requests (User-Specific) ---
    async function fetchPendingRequests() {
        // ... (This function remains the same as your provided version)
        if (!currentUserData) { console.warn("fetchPendingRequests: currentUserData is missing"); return; }
        if (!pendingRequestsListContainer || !pendingRequestsCountSpan || !togglePendingRequestsBtn) return;

        if (!pendingRequestsSection.classList.contains('hidden')) {
            pendingRequestsListContainer.innerHTML = '<p class="loading">Loading requests...</p>';
        }
        try {
            const requests = await apiCall(`/api/connections/requests/pending`);
            const numRequests = Array.isArray(requests) ? requests.length : 0;
            pendingRequestsCountSpan.textContent = `(${numRequests})`;
            togglePendingRequestsBtn.classList.toggle('has-requests', numRequests > 0);
            if (!pendingRequestsSection.classList.contains('hidden')) {
                 updateListContainer(pendingRequestsListContainer, requests, createPendingRequestItem, "No pending connection requests.", 'pending-request');
            }
        } catch (error) {
            pendingRequestsCountSpan.textContent = '(E)';
            togglePendingRequestsBtn.classList.remove('has-requests');
            if (!pendingRequestsSection.classList.contains('hidden')) {
                 pendingRequestsListContainer.innerHTML = `<p class="error-message">Could not load pending requests: ${escapeHtml(error.message)}</p>`;
            }
        }
    }

    function createPendingRequestItem(req) {
        // ... (This function remains the same as your provided version)
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

    // --- Search Users (Client-Side Filtering from combinedSearchableList) ---
    function searchUsers() {
        if (!searchResultsListContainer) return;

        if (!currentUserData) {
            searchResultsListContainer.innerHTML = '<p class="no-data">Please log in to search users.</p>';
            return;
        }

        const searchTerm = userSearchInput.value.trim().toLowerCase();
        if (searchTerm.length < 2) {
            searchResultsListContainer.innerHTML = '<p class="no-data">Enter at least 2 characters to search.</p>';
            return;
        }

        if (!connectionsFetched || !suggestionsFetched) {
            searchResultsListContainer.innerHTML = '<p class="loading">Loading user data for search, please wait...</p>';
            return;
        }
        if (combinedSearchableList.length === 0 && (connectionsFetched && suggestionsFetched)) {
             searchResultsListContainer.innerHTML = '<p class="no-data">No users in your connections or suggestions to search. Explore to find more people!</p>';
            return;
        }


        const filteredUsers = combinedSearchableList.filter(user => {
            if (!user || !user.username) return false;
            // User objects in combinedSearchableList will have 'name', 'username', 'profession'
            const nameMatch = user.name && user.name.toLowerCase().includes(searchTerm);
            const usernameMatch = user.username.toLowerCase().includes(searchTerm);
            const professionMatch = user.profession && user.profession.toLowerCase().includes(searchTerm);
            return nameMatch || usernameMatch || professionMatch;
        });
        // For search results, isOwnConnectionsPage is false, isAnonymousView is false (since search is logged-in only)
        updateListContainer(searchResultsListContainer, filteredUsers, createUserListItem, `No users found matching "${escapeHtml(userSearchInput.value.trim())}".`, 'search_result');
    }


    // --- Create User Card Item ---
    // isForOwnConnectionsPage: true if type is 'connection' and viewing own profile's connections
    // isAnonymousView: true if currentUserData is null (used for suggestions if anonymous browsing was allowed for them)
    function createUserListItem(user, type, isForOwnConnectionsPage = false, isAnonymousView = false) {
        if (!user || typeof user.id !== 'number' || typeof user.username !== 'string' || !user.username) {
             console.warn(`Invalid user data for list item (type: ${type}):`, user);
             const errorCard = document.createElement('div'); errorCard.classList.add('user-card');
             errorCard.innerHTML = `<div class="user-info"><span class="username" style="color:red;">User Data Error</span><span class="profession">Info missing</span></div>`;
             return errorCard;
        }
        const card = document.createElement('div');
        card.classList.add('user-card');
        const avatarInitials = escapeHtml(user.username.substring(0,2).toUpperCase());

        let actionButtonsHtml = '';
        const isSelf = !isAnonymousView && currentUserData && user.id === currentUserData.id;

        if (type === 'connection') { // "My Connections" list
            actionButtonsHtml = `<button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Profile</button>`;
            if (isForOwnConnectionsPage && !isSelf) { // Must be on own connections page and not self
                actionButtonsHtml += `
                    <button class="message-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-comment-dots"></i> Message</button>
                    <button class="remove-conn-btn" data-username="${escapeHtml(user.username)}" title="Remove Connection"><i class="fas fa-user-times"></i></button>`;
            }
        } else if (type === 'suggestion') { // "Suggestions" list
            if (isAnonymousView) { // Should not happen if suggestions require login
                 actionButtonsHtml = `<button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Profile</button>`;
            } else if (isSelf) {
                actionButtonsHtml = `<button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Your Profile</button>`;
            } else { // Logged in, viewing another user as a suggestion
                actionButtonsHtml = `
                    <button class="request-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-plus"></i> Send Request</button>
                    <button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Profile</button>`;
            }
        } else if (type === 'search_result') { // Search results (logged-in only context)
            if (isSelf) {
                actionButtonsHtml = `<button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Your Profile</button>`;
            } else {
                // User object from combinedSearchableList has `isConnection`
                if (user.isConnection) { // User is an existing connection
                     actionButtonsHtml = `
                        <button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Profile</button>
                        <button class="message-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-comment-dots"></i> Message</button>
                        <span class="status-text"><i class="fas fa-check-circle"></i> Connected</span>`;
                        // Optionally add remove button: <button class="remove-conn-btn" ...>
                } else { // User is a suggestion or not yet interacted with
                    actionButtonsHtml = `
                        <button class="request-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-plus"></i> Send Request</button>
                        <button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Profile</button>`;
                }
            }
        }


        card.innerHTML = `
            <div class="avatar-placeholder">${avatarInitials}</div>
            <div class="user-info">
                 <a href="/user/profile.html?username=${encodeURIComponent(user.username)}" class="username-link" title="View ${escapeHtml(user.username)}'s profile">${escapeHtml(user.username)}</a>
                <span class="profession">${escapeHtml(user.profession || 'Profession not specified')}</span>
            </div>
            <div class="user-actions">${actionButtonsHtml}</div>`;
        return card;
    }

    // --- Action Event Handlers (Delegated) ---
    document.body.addEventListener('click', async (event) => {
        // ... (This function remains largely the same as your provided version)
        // Ensure currentUserData checks are in place for actions requiring login.
        const button = event.target.closest('button');
        if (!button) return;

        const username = button.dataset.username;
        const requesterIdStr = button.dataset.requesterId;
        const requesterId = requesterIdStr ? parseInt(requesterIdStr, 10) : null;

        if (button.classList.contains('view-profile-btn') && username) {
            window.location.href = `/user/profile.html?username=${encodeURIComponent(username)}`;
            return;
        }

        if (!currentUserData) {
            if (button.classList.contains('message-btn') || button.classList.contains('request-btn') ||
                button.classList.contains('accept-btn') || button.classList.contains('ignore-btn') ||
                button.classList.contains('remove-conn-btn')) {
                alert("Please log in to perform this action.");
                return;
            }
        }

        const originalButtonHtml = button.innerHTML;
        let isNavigationButton = false;

        if (button.classList.contains('message-btn')) {
            isNavigationButton = true;
        } else {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }

        try {
            if (button.classList.contains('message-btn') && username) {
                window.location.href = `/user/chat.html?user=${encodeURIComponent(username)}`;
            } else if (button.classList.contains('request-btn') && username) {
                await sendConnectionRequestAction(username, button, originalButtonHtml);
            } else if (button.classList.contains('accept-btn') && Number.isInteger(requesterId)) {
                await acceptRequestAction(requesterId, button, originalButtonHtml);
            } else if (button.classList.contains('ignore-btn') && Number.isInteger(requesterId)) {
                await ignoreRequestAction(requesterId, button, originalButtonHtml);
            } else if (button.classList.contains('remove-conn-btn') && username) {
                await removeConnectionAction(username, button, originalButtonHtml);
            } else {
                if (!isNavigationButton && !button.classList.contains('view-profile-btn')) {
                    button.disabled = false;
                    button.innerHTML = originalButtonHtml;
                }
            }
        } catch (error) {
            console.error("Error in delegated action handler:", error.message);
            if (!isNavigationButton && !button.classList.contains('view-profile-btn')) {
                 button.disabled = false;
                 button.innerHTML = originalButtonHtml;
            }
        }
    });

    // --- Action Implementations (sendConnectionRequestAction, etc.) ---
    // These functions should now also re-fetch connections AND suggestions,
    // which will then trigger buildCombinedSearchableList() and re-filter search if active.

    async function sendConnectionRequestAction(targetUsername, button, originalHtml) {
        try {
            const result = await apiCall(`/api/connections/request/${encodeURIComponent(targetUsername)}`, 'POST');
            alert(result.message || "Request sent!");
            button.innerHTML = 'Sent <i class="fas fa-check-circle"></i>';
            button.classList.remove('request-btn');
            button.classList.add('sent');
            // Re-fetch suggestions (which might change) and connections (status for this user might change in some views)
            // This will trigger buildCombinedSearchableList
            await Promise.all([fetchSuggestions(), fetchConnections()]);
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
        // ... (This function remains the same as your provided version)
        // If ignoring a request should impact suggestions, then fetchSuggestions() also here.
        const parentItem = button.closest('.user-card');
        try {
            if (typeof requesterId !== 'number' || isNaN(requesterId)) {
                throw new Error("Invalid requester ID.");
            }
            const result = await apiCall(`/api/connections/requests/ignore/${requesterId}`, 'POST');
            alert(result.message || "Request ignored.");
            if(parentItem) { parentItem.style.transition = 'opacity 0.5s ease'; parentItem.style.opacity = '0'; }
            setTimeout(async () => {
                 if(parentItem) parentItem.remove();
                 await fetchPendingRequests();
                 // Consider if suggestions need refresh: await fetchSuggestions();
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
        try {
            const result = await apiCall(`/api/connections/${encodeURIComponent(targetUsername)}`, 'DELETE');
            alert(result.message || "Connection removed.");
            await Promise.all([fetchConnections(), fetchSuggestions()]);
        } catch (error) {
            alert(`Could not remove connection: ${escapeHtml(error.message)}`);
            button.disabled = false; button.innerHTML = originalHtml;
        }
    }

    // --- Initialize Page ---
    async function initializeConnectionPage() {
        await fetchCurrentUser();

        const pageTitleElement = document.querySelector('title');
        if (pageTitleElement) pageTitleElement.textContent = "Network - UniVerse";

        if (currentUserData) { // User is logged in
            console.log("User is logged in. Initializing network page.");
            const mainHeader = document.querySelector('h1.page-title') || document.querySelector('.top-nav .nav-title');
            if (mainHeader) mainHeader.textContent = "My Network";

            if (userSearchInput) userSearchInput.disabled = false;
            if (userSearchButton) userSearchButton.disabled = false;
            if (searchResultsListContainer && userSearchInput && userSearchInput.value.trim().length === 0) {
                searchResultsListContainer.innerHTML = '<p class="no-data">Enter a name or profession to search your network.</p>';
            }


            document.querySelectorAll('.section-card, .toggle-requests-container').forEach(el => {
                if(el) el.style.display = 'block';
            });
            if (pendingRequestsSection && pendingRequestsSection.classList.contains('hidden')) {
                // respect initial hidden state
            } else if (pendingRequestsSection) {
                 pendingRequestsSection.style.display = 'block';
            }

            // Fetch connections and suggestions. buildCombinedSearchableList will be called once both are done.
            fetchConnections();
            fetchSuggestions();
            fetchPendingRequests();

        } else { // User is not logged in
            console.log("User is not logged in. Search disabled. Other network features hidden.");
            const mainHeader = document.querySelector('h1.page-title') || document.querySelector('.top-nav .nav-title');
            if (mainHeader) mainHeader.textContent = "Find People"; // Or "Network"

            if (userSearchInput) {
                userSearchInput.disabled = true;
                userSearchInput.placeholder = "Log in to search users";
            }
            if (userSearchButton) userSearchButton.disabled = true;
            if (searchResultsListContainer) searchResultsListContainer.innerHTML = '<p class="no-data">Please log in to search for users.</p>';

            if (connectionsListContainer) connectionsListContainer.innerHTML = '<p class="no-data">Log in to see your connections.</p>';
            if (suggestionsListContainer) suggestionsListContainer.innerHTML = '<p class="no-data">Log in to get suggestions.</p>';
            if (pendingRequestsSection) pendingRequestsSection.style.display = 'none';
            if (togglePendingRequestsBtn) togglePendingRequestsBtn.style.display = 'none';
            if (showMoreConnectionsBtn) showMoreConnectionsBtn.style.display = 'none';
        }
    }

    // --- Attach General Event Listeners ---
    if (userSearchButton) userSearchButton.addEventListener('click', searchUsers);
    if (userSearchInput) {
        userSearchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { e.preventDefault(); searchUsers(); } });
        let searchDebounceTimer;
        userSearchInput.addEventListener('input', () => {
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(searchUsers, 300);
        });
    }

    // ... (togglePendingRequestsBtn and showMoreConnectionsBtn event listeners remain the same as your provided version)
    if (togglePendingRequestsBtn && pendingRequestsSection) {
        const initPendingHidden = pendingRequestsSection.classList.contains('hidden');
        const initPendingIcon = initPendingHidden ? 'fa-user-clock' : 'fa-eye-slash';
        const initPendingText = initPendingHidden ? 'View Pending Requests' : 'Hide Pending Requests';
        const currentCount = pendingRequestsCountSpan ? pendingRequestsCountSpan.textContent : '(0)';
        togglePendingRequestsBtn.innerHTML = `<i class="fas ${initPendingIcon}"></i> ${initPendingText} <span class="count-badge" id="pending-requests-count">${currentCount}</span>`;
        pendingRequestsCountSpan = document.getElementById('pending-requests-count');


        togglePendingRequestsBtn.addEventListener('click', () => {
            if (!currentUserData) { // Should not be clickable if not logged in due to display:none
                alert("Please log in to view pending requests.");
                return;
            }
            const isNowHidden = pendingRequestsSection.classList.toggle('hidden');
            const iconClass = isNowHidden ? 'fa-user-clock' : 'fa-eye-slash';
            const buttonText = isNowHidden ? 'View Pending Requests' : 'Hide Pending Requests';
            const countVal = pendingRequestsCountSpan ? pendingRequestsCountSpan.textContent : '(?)';
            togglePendingRequestsBtn.innerHTML = `<i class="fas ${iconClass}"></i> ${buttonText} <span class="count-badge" id="pending-requests-count">${countVal}</span>`;
            pendingRequestsCountSpan = document.getElementById('pending-requests-count');

            if (!isNowHidden && (!pendingRequestsListContainer.hasChildNodes() || pendingRequestsListContainer.querySelector('.no-data, .loading, .error-message'))) {
                fetchPendingRequests();
            }
        });
    }

    if (showMoreConnectionsBtn) {
        showMoreConnectionsBtn.addEventListener('click', () => {
            if(currentUserData) displayMoreConnections(currentUsername);
        });
    }

    // --- START INITIALIZATION ---
    initializeConnectionPage();
});