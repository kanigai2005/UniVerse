// static/connection.js

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
    console.log("Connections Page DOM Loaded - Combined Search Version");

    // --- Element References ---
    const connectionsListContainer = document.getElementById('connections-list');
    const suggestionsListContainer = document.getElementById('suggestions-list'); // Still used for initial suggestions
    const pendingRequestsListContainer = document.getElementById('pending-requests-list');
    const userSearchInput = document.getElementById('user-search-input');
    const userSearchButton = document.getElementById('user-search-button');
    const searchResultsListContainer = document.getElementById('search-results-list'); // This will show combined results
    const togglePendingRequestsBtn = document.getElementById('toggle-pending-requests-btn');
    const pendingRequestsSection = document.getElementById('pending-requests-section');
    let pendingRequestsCountSpan = document.getElementById('pending-requests-count');
    const showMoreConnectionsBtn = document.getElementById('show-more-connections-btn');

    // --- State ---
    let currentUsername = null;
    let currentUserData = null;
    
    let allMyConnections = []; // Stores ONLY existing connections
    let allPotentialNewConnections = []; // Stores users from suggestions/all-searchable (excluding existing connections)
    let combinedSearchableList = []; // Merged list for active search

    let displayedConnectionsCount = 0; // For "My Connections" pagination
    const CONNECTIONS_PER_PAGE = 9;

    // --- Check Core Elements ---
    // ... (essentialElements check remains the same) ...
    const essentialElements = {
        connectionsListContainer, suggestionsListContainer, pendingRequestsListContainer,
        userSearchInput, userSearchButton, searchResultsListContainer,
        togglePendingRequestsBtn, pendingRequestsSection, pendingRequestsCountSpan, showMoreConnectionsBtn
    };
    for (const elName in essentialElements) {
        if (!essentialElements[elName]) {
            console.error(`CRITICAL: UI element '${elName}' is missing!`);
            return;
        }
    }

    async function apiCall(url, method = 'GET', body = null) {
        // ... (apiCall function remains the same - robust version) ...
        const options = { method, headers: {}, credentials: 'include' };
        if (body && (method === 'POST' || method === 'PUT' || method === 'DELETE')) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
        try {
            const response = await fetch(url, options);
            if (response.status === 401) {
                console.warn(`API call to ${url} resulted in 401 Unauthorized. Redirecting to login.`);
                window.location.href = '/login.html?error=Session+expired_or_invalid';
                throw new Error("User not authenticated. Session may have expired.");
            }
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
            if (error.message !== "User not authenticated. Session may have expired.") {
                 console.error(`Error during API call to ${url} (method: ${method}):`, error);
            }
            throw error;
        }
    }

    async function fetchCurrentUser() {
        // ... (fetchCurrentUser function remains the same) ...
        console.log("Attempting to fetch current user...");
        try {
            const userData = await apiCall('/api/users/me');
            if (userData && userData.username && typeof userData.id === 'number') {
                currentUserData = userData;
                currentUsername = userData.username;
                console.log("Current user fetched:", currentUsername, "ID:", currentUserData.id);
                return true;
            }
            console.warn("User data from /api/users/me is incomplete or user not found.");
            if (!window.location.pathname.endsWith('/login.html')) {
                window.location.href = '/login.html?error=User_data_issue';
            }
            return false;
        } catch (error) {
            console.error('Error in fetchCurrentUser wrapper:', error.message);
            return false;
        }
    }

    function updateListContainer(container, items, itemCreatorFunc, noDataMessage, itemTypeContext) {
        if (!container) { console.error("updateListContainer: container is null for itemType", itemTypeContext); return; }
        container.innerHTML = '';
        if (!Array.isArray(items) || items.length === 0) {
            container.innerHTML = `<p class="no-data">${escapeHtml(noDataMessage)}</p>`;
            if (container === connectionsListContainer && showMoreConnectionsBtn) showMoreConnectionsBtn.classList.add('hidden');
            return;
        }
        // For combined search results, itemCreatorFunc needs to know if user is already a connection
        items.forEach(item => container.appendChild(itemCreatorFunc(item, itemTypeContext)));
    }


    async function fetchMyConnectionsData(usernameToFetchFor = currentUsername) { // Renamed from fetchConnections
        if (!usernameToFetchFor) { console.warn("fetchMyConnectionsData: usernameToFetchFor is missing"); return []; }
        try {
            const connections = await apiCall(`/api/users/${encodeURIComponent(usernameToFetchFor)}/connections`);
            allMyConnections = Array.isArray(connections) ? connections : [];
            console.log(`Fetched ${allMyConnections.length} existing connections for ${usernameToFetchFor}`);
            return allMyConnections;
        } catch (error) {
            if (!error.message.startsWith("User not authenticated")) {
                console.error(`Could not load connections for ${usernameToFetchFor}: ${escapeHtml(error.message)}`);
            }
            allMyConnections = [];
            return [];
        }
    }

    function displayMyConnectionsSegment(usernameForDisplay) { // Specifically for "My Connections" section
        connectionsListContainer.innerHTML = ''; // Clear before displaying segment
        displayedConnectionsCount = 0;
        const isOwn = (currentUsername === usernameForDisplay);
        // Filter allMyConnections if viewing someone else's (though this func is usually for own)
        const connectionsToDisplay = (isOwn) ? allMyConnections : allMyConnections.filter(c => c.owner_username === usernameForDisplay); // Example filter

        if (connectionsToDisplay.length === 0) {
            connectionsListContainer.innerHTML = '<p class="no-data">No connections yet. Find new people!</p>';
            if (showMoreConnectionsBtn) showMoreConnectionsBtn.classList.add('hidden');
            return;
        }
        displayMoreMyConnections(usernameForDisplay);
    }


    function displayMoreMyConnections(displayedUsername) { // Specifically for "My Connections" pagination
        const isOwn = (currentUsername === displayedUsername);
        const newConnectionsToRender = allMyConnections.slice(displayedConnectionsCount, displayedConnectionsCount + CONNECTIONS_PER_PAGE);

        newConnectionsToRender.forEach(user => {
            // Pass 'my_connection' type to distinguish from search/suggestion
            connectionsListContainer.appendChild(createUserListItem(user, 'my_connection', isOwn));
        });
        displayedConnectionsCount += newConnectionsToRender.length;
        if (showMoreConnectionsBtn) {
            showMoreConnectionsBtn.classList.toggle('hidden', displayedConnectionsCount >= allMyConnections.length);
        }
    }
    
    async function fetchPotentialNewConnections() { // Formerly fetchAllSearchableUsers
        if (!currentUsername) {
            console.warn("Cannot fetch potential new connections, current user not available.");
            return [];
        }
        console.log("Fetching potential new connections (e.g., suggestions)...");
        try {
            // This endpoint should return users NOT already connected and NOT self, etc.
            const users = await apiCall(`/api/users/${encodeURIComponent(currentUsername)}/suggestions?limit=1000`);
            allPotentialNewConnections = Array.isArray(users) ? users : [];
            console.log(`Loaded ${allPotentialNewConnections.length} potential new connections.`);
            return allPotentialNewConnections;
        } catch (error) {
            console.error("Error fetching potential new connections:", error);
            allPotentialNewConnections = [];
            return [];
        }
    }

    function buildCombinedSearchableList() {
        const combinedMap = new Map();
        // Add all potential new connections
        allPotentialNewConnections.forEach(user => {
            if (user && user.id) { // Ensure user and user.id are valid
                combinedMap.set(user.id, { ...user, isConnection: false });
            }
        });
        // Add all my connections, marking them as such
        allMyConnections.forEach(user => {
             if (user && user.id) { // Ensure user and user.id are valid
                combinedMap.set(user.id, { ...user, isConnection: true });
            }
        });
        combinedSearchableList = Array.from(combinedMap.values());
        console.log(`Built combined searchable list with ${combinedSearchableList.length} unique users.`);
    }


    async function fetchInitialSuggestions() { // For the "People You May Know" section
        if (!currentUsername) { console.warn("fetchSuggestions: currentUsername is missing"); return; }
        suggestionsListContainer.innerHTML = '<p class="loading">Loading suggestions...</p>';
        try {
            // Use the allPotentialNewConnections if already fetched, or fetch fresh suggestions
            let suggestionsToShow = allPotentialNewConnections;
            if (suggestionsToShow.length === 0) { // If not pre-fetched or empty
                 suggestionsToShow = await apiCall(`/api/users/${encodeURIComponent(currentUsername)}/suggestions`);
            }
            updateListContainer(suggestionsListContainer, suggestionsToShow.slice(0, 9), createUserListItem, "No new suggestions right now.", 'suggestion');
        } catch (error) {
             if (!error.message.startsWith("User not authenticated")) {
                suggestionsListContainer.innerHTML = `<p class="error-message">Could not load suggestions: ${escapeHtml(error.message)}</p>`;
            }
        }
    }


    async function fetchPendingRequests() { /* ... (remains the same) ... */ }
    function createPendingRequestItem(req) { /* ... (remains the same) ... */ }


    // ***** MODIFIED searchUsers for COMBINED client-side filtering *****
    function searchUsers() {
        if (!currentUserData) {
            searchResultsListContainer.innerHTML = '<p class="error-message">Please log in to search.</p>';
            return;
        }

        const searchTerm = userSearchInput.value.trim().toLowerCase();
        if (searchTerm.length < 2) {
            searchResultsListContainer.innerHTML = '<p class="no-data">Enter at least 2 characters to search.</p>';
            return;
        }

        if (combinedSearchableList.length === 0) {
            // This might happen if initial fetches failed or are slow
            searchResultsListContainer.innerHTML = '<p class="no-data">User data not yet available for search. Please wait or refresh.</p>';
            return;
        }

        searchResultsListContainer.innerHTML = '<p class="loading">Searching...</p>';

        const filteredUsers = combinedSearchableList.filter(user => {
            if (!user) return false; // Skip if user object is somehow null/undefined
            const nameMatch = user.name && user.name.toLowerCase().includes(searchTerm);
            const usernameMatch = user.username && user.username.toLowerCase().includes(searchTerm);
            const professionMatch = user.profession && user.profession.toLowerCase().includes(searchTerm);
            // const departmentMatch = user.department && user.department.toLowerCase().includes(searchTerm);
            return nameMatch || usernameMatch || professionMatch; // || departmentMatch;
        });
        
        // When rendering search results, we pass 'search_result' as context
        updateListContainer(searchResultsListContainer, filteredUsers, createUserListItem, `No users found matching "${escapeHtml(userSearchInput.value.trim())}".`, 'search_result');
    }
    // ***** END OF MODIFIED searchUsers *****


    // ***** MODIFIED createUserListItem to handle different contexts *****
    function createUserListItem(user, typeContext) {
        // typeContext can be 'my_connection', 'suggestion', 'search_result', 'pending_request_target'
        if (!user || typeof user.id !== 'number' || typeof user.username !== 'string' || !user.username) {
             console.warn(`Invalid user data for list item (type: ${typeContext}):`, user);
             const errorCard = document.createElement('div'); errorCard.classList.add('user-card');
             errorCard.innerHTML = `<div class="user-info"><span class="username" style="color:red;">Data Error</span></div>`;
             return errorCard;
        }
        const card = document.createElement('div');
        card.classList.add('user-card');
        const avatarInitials = escapeHtml(user.username.substring(0,2).toUpperCase());

        let actionButtonsHtml = '';
        const isAlreadyConnection = allMyConnections.some(conn => conn.id === user.id);
        // For search results, the user object itself might have an 'isConnection' flag from combinedSearchableList
        const isMarkedAsConnection = user.isConnection === true;


        if (typeContext === 'my_connection' || (typeContext === 'search_result' && isMarkedAsConnection)) {
            // User is an existing connection
            actionButtonsHtml = `<button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Profile</button>`;
            // Only add message/remove if it's the logged-in user viewing their own connections/search result of a connection
             if (currentUserData && currentUserData.username) { // Check if loggedInUser is current user
                actionButtonsHtml += `
                    <button class="message-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-comment-dots"></i> Message</button>
                    <button class="remove-conn-btn" data-username="${escapeHtml(user.username)}" title="Remove Connection"><i class="fas fa-user-times"></i></button>`;
            }
        } else if (typeContext === 'suggestion' || (typeContext === 'search_result' && !isMarkedAsConnection)) {
            // User is a suggestion or a search result who is NOT an existing connection
            // Here, you might also want to check for pending requests before showing "Send Request"
            // For simplicity, assuming allSearchableUsers/suggestions are already filtered for pending.
            actionButtonsHtml = `
                <button class="request-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-plus"></i> Send Request</button>
                <button class="view-profile-btn" data-username="${escapeHtml(user.username)}"><i class="fas fa-user-circle"></i> Profile</button>`;
        }
        // 'pending_request_target' would be handled by createPendingRequestItem

        card.innerHTML = `
            <div class="avatar-placeholder">${avatarInitials}</div>
            <div class="user-info">
                <span class="username">${escapeHtml(user.username)}</span>
                <span class="profession">${escapeHtml(user.profession || 'Profession not specified')}</span>
            </div>
            <div class="user-actions">${actionButtonsHtml}</div>`;
        return card;
    }
    // ***** END OF MODIFIED createUserListItem *****


    document.body.addEventListener('click', async (event) => { /* ... (delegated event handler) ... */ });
    async function sendConnectionRequestAction(targetUsername, button, originalHtml) {
        try {
            const result = await apiCall(`/api/connections/request/${encodeURIComponent(targetUsername)}`, 'POST');
            alert(result.message || "Request sent!");
            button.innerHTML = 'Sent <i class="fas fa-check-circle"></i>';
            button.classList.remove('request-btn');
            button.classList.add('sent');
            button.disabled = true; // Keep it disabled after sending

            // Refresh relevant lists
            await fetchInitialSuggestions(); // Suggestions will change
            await fetchAllSearchableUsers(); // The user is no longer "searchable" for a new request
            buildCombinedSearchableList(); // Rebuild the master list
            if (userSearchInput.value.trim().length >= 2) { // If a search was active, re-run it
                searchUsers();
            }
            await fetchPendingRequests(); // Own pending requests might be affected if backend auto-accepts or similar

        } catch (error) {
            if (!error.message.startsWith("User not authenticated")) {
                alert(`Could not send request: ${escapeHtml(error.message)}`);
            }
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
                // Refresh everything that could have changed
                await fetchMyConnectionsData(currentUsername);
                await fetchInitialSuggestions();
                await fetchPendingRequests();
                await fetchAllSearchableUsers();
                buildCombinedSearchableList();
                if (userSearchInput.value.trim().length >= 2) searchUsers();

            }, 500);
        } catch (error) {
             if (!error.message.startsWith("User not authenticated")) {
                alert(`Could not accept request: ${escapeHtml(error.message)}`);
            }
            button.disabled = false; button.innerHTML = originalHtml;
        }
    }
    async function ignoreRequestAction(requesterId, button, originalHtml) { /* ... same logic, but might need to refresh allSearchableUsers if an ignored user becomes searchable again ... */ }
    async function removeConnectionAction(targetUsername, button, originalHtml) { /* ... same logic, refresh allSearchableUsers, suggestions, and own connections ... */ }


    async function initializeConnectionPage() {
        const userIsAuthenticated = await fetchCurrentUser();
        if (!userIsAuthenticated) {
            console.error("CRITICAL: Page initialization failed - current user not authenticated.");
            if (connectionsListContainer) connectionsListContainer.innerHTML = '<p class="error-message">Could not load your data. Please <a href="/login.html">log in</a> again.</p>';
            [userSearchInput, userSearchButton, togglePendingRequestsBtn].forEach(el => { if(el) el.disabled = true; });
            return;
        }
        
        userSearchInput.disabled = false;
        userSearchButton.disabled = false;

        const urlParams = new URLSearchParams(window.location.search);
        const viewUserParam = urlParams.get('view_user');
        const pageTitleElement = document.querySelector('title');

        // Fetch both lists needed for combined search and display
        await fetchMyConnectionsData(currentUsername); // Populates allMyConnections
        await fetchPotentialNewConnections(); // Populates allPotentialNewConnections
        buildCombinedSearchableList(); // Merges them for searching

        if (viewUserParam && viewUserParam !== currentUsername) {
            if (pageTitleElement) pageTitleElement.textContent = `${escapeHtml(viewUserParam)}'s Network - UniVerse`;
            const mainHeader = document.querySelector('.section-card h2'); // Assuming the first h2 is for connections
            if(mainHeader) mainHeader.textContent = `${escapeHtml(viewUserParam)}'s Connections`;
            
            if (suggestionsListContainer.parentElement) suggestionsListContainer.parentElement.style.display = 'none';
            if (pendingRequestsSection) pendingRequestsSection.style.display = 'none';
            if (togglePendingRequestsBtn) togglePendingRequestsBtn.style.display = 'none';
            
            // For viewing OTHERS' connections, we still use fetchMyConnectionsData but pass their username
            // This assumes your backend /api/users/{username}/connections can return public connections of others
            await fetchMyConnectionsData(viewUserParam);
            displayMyConnectionsSegment(viewUserParam); // Display their connections
        } else {
            // Viewing own network
            if (pageTitleElement) pageTitleElement.textContent = "My Network - UniVerse";
            document.querySelectorAll('.section-card, .toggle-requests-container').forEach(el => {
                if(el && el.id !== 'pending-requests-section') el.style.display = 'block';
            });
             if (pendingRequestsSection && pendingRequestsSection.classList.contains('hidden')) {
                // initial hidden state
             } else if (pendingRequestsSection) {
                 pendingRequestsSection.style.display = 'block';
             }
            displayMyConnectionsSegment(currentUsername); // Display own connections
            fetchInitialSuggestions(); // Display initial suggestions
            fetchPendingRequests();
        }
    }

    // Event Listeners for search and toggles
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
                searchDebounceTimer = setTimeout(searchUsers, 300);
            }
        });
    }
    if (togglePendingRequestsBtn) { /* ... (remains the same) ... */ }
    if (showMoreConnectionsBtn) { /* ... (remains the same, but ensure it uses the correct data for pagination) ... */ 
        showMoreConnectionsBtn.addEventListener('click', () => {
            const urlParams = new URLSearchParams(window.location.search);
            const viewUserParam = urlParams.get('view_user');
            displayMoreMyConnections(viewUserParam || currentUsername);
        });
    }

    initializeConnectionPage();
});