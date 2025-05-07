 // --- Utility: Simple HTML Escaping ---
 function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') { return unsafe || ''; }
    return unsafe
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
 }

// --- Navbar Update Logic ---
async function updateNavbar() {
    const navProfileLink = document.getElementById('nav-profile-link');
    if (!navProfileLink) { console.warn("Navbar profile link element not found."); return null; }
    try {
        const response = await fetch('/api/users/me');
        if (!response.ok) {
            if (response.status === 401 || response.status === 307) { navProfileLink.href = "/login.html"; localStorage.removeItem('username'); }
            else { navProfileLink.href = "/login.html"; localStorage.removeItem('username'); }
            return null;
        }
        const userData = await response.json();
        if (userData && userData.username) {
            navProfileLink.href = `/profile.html?username=${encodeURIComponent(userData.username)}`;
            localStorage.setItem('username', userData.username);
            return userData;
        } else { navProfileLink.href = "/login.html"; localStorage.removeItem('username'); return null; }
    } catch (error) { console.error("Navbar update error:", error); navProfileLink.href = "/login.html"; localStorage.removeItem('username'); return null; }
}


// --- Leaderboard Logic ---
let currentSortKey = 'activity_score'; // Default sort
let sortDirection = 'desc';
let leaderboardData = []; // Cache fetched data

const leaderboardList = document.getElementById("leaderboard-list");
const sortButtons = {
     gems: document.getElementById("sort-gems"),
     activity: document.getElementById("sort-activity"),
     name: document.getElementById("sort-name")
};


async function fetchLeaderboardData() {
    leaderboardList.innerHTML = '<p class="loading">Loading leaderboard...</p>'; // Show loading
    try {
        const response = await fetch("/api/leaderboard"); // Fetch data
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error ${response.status}: ${errorText}`);
        }
        leaderboardData = await response.json(); // Store data
        renderLeaderboard(); // Render sorted data
    } catch (error) {
        console.error("Error fetching leaderboard data:", error);
        leaderboardList.innerHTML = `<p class="error-message">Failed to load leaderboard: ${error.message}</p>`;
    }
}

function sortData() {
    leaderboardData.sort((a, b) => {
        const valueA = a[currentSortKey];
        const valueB = b[currentSortKey];

        // Handle potential nulls or inconsistencies if necessary
        const valA = valueA === null || valueA === undefined ? (sortDirection === 'asc' ? Infinity : -Infinity) : valueA;
        const valB = valueB === null || valueB === undefined ? (sortDirection === 'asc' ? Infinity : -Infinity) : valueB;


        if (typeof valA === 'string' && typeof valB === 'string') {
            // Case-insensitive string comparison
            return sortDirection === 'asc'
                ? valA.localeCompare(valB, undefined, { sensitivity: 'base' })
                : valB.localeCompare(valA, undefined, { sensitivity: 'base' });
        } else {
            // Numeric comparison (handles numbers and potentially dates if comparable)
             return sortDirection === 'asc' ? valA - valB : valB - valA;
        }
    });
}

function renderLeaderboard() {
     if (!leaderboardList) {
         console.error("Leaderboard list element not found during render.");
         return;
     }
     leaderboardList.innerHTML = ''; // Clear previous entries or loading message

     if(leaderboardData.length === 0) {
         leaderboardList.innerHTML = '<p class="no-data">Leaderboard is currently empty.</p>';
         return;
     }

     sortData(); // Sort the cached data

     leaderboardData.forEach((user, index) => {
        const listItem = document.createElement("li");
        // Add click listener to the whole item for navigation
        listItem.addEventListener('click', () => {
            // Navigate using the username, assuming profile page uses ?username=... query parameter
            window.location.href = `/profile.html?username=${encodeURIComponent(user.username)}`;
        });
        listItem.style.cursor = 'pointer'; // Indicate clickable item

        listItem.innerHTML = `
            <div class="leaderboard-item-details">
                <span class="leader-rank">#${index + 1}</span>
                <div class="leader-info">
                    <div class="leader-name">${escapeHtml(user.username)}</div>
                    <div class="leader-details">
                        ${user.profession ? `<span>${escapeHtml(user.profession)}</span>` : ''}
                        ${user.department ? `<span>${escapeHtml(user.department)}</span>` : ''}
                    </div>
                </div>
            </div>
            <div class="score-section">
                 <div class="gem-count">${user.alumni_gems || 0} <i class="fas fa-gem" style="font-size: 0.8em;"></i></div>
                 <div class="activity-score">Score: ${user.activity_score || 0}</div>
            </div>
            <!-- Removed explicit button, click the name/row instead -->
        `;
        leaderboardList.appendChild(listItem);
    });

    updateSortIndicatorsUI(); // Update button styles and indicators
}

function updateSortIndicatorsUI() {
    for (const btn of Object.values(sortButtons)) {
         if (btn) {
             btn.classList.remove('active');
             const indicator = btn.querySelector('.sort-indicator');
             if (indicator) indicator.textContent = '';
         }
    }
    let activeButton;
    if (currentSortKey === 'alumni_gems') activeButton = sortButtons.gems;
    else if (currentSortKey === 'activity_score') activeButton = sortButtons.activity;
    else if (currentSortKey === 'username') activeButton = sortButtons.name;

     if (activeButton) {
         activeButton.classList.add('active');
         const indicator = activeButton.querySelector('.sort-indicator');
         if (indicator) indicator.textContent = sortDirection === 'asc' ? '▲' : '▼';
     }
}

function handleSortClick(event) {
     const button = event.target.closest('button');
     if(!button || !button.dataset.sortkey) return; // Click wasn't on a sort button

     const newSortKey = button.dataset.sortkey;

     if (newSortKey === currentSortKey) {
         // Toggle direction if clicking the same key
         sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
     } else {
         // Switch to new key, default direction
         currentSortKey = newSortKey;
         sortDirection = (newSortKey === 'username') ? 'asc' : 'desc'; // Default name asc, others desc
     }
     renderLeaderboard(); // Re-sort and re-render the existing data
}


// --- Initial Setup ---
document.addEventListener('DOMContentLoaded', () => {
    updateNavbar(); // Update navbar on load
    fetchLeaderboardData(); // Fetch and display initial data

    // Add listeners to sort buttons
    sortButtons.gems?.addEventListener('click', handleSortClick);
    sortButtons.activity?.addEventListener('click', handleSortClick);
    sortButtons.name?.addEventListener('click', handleSortClick);

    // **Important:** The code to handle clicking on a leaderboard item
    // to go to the profile page is now handled by the event listener
    // added directly to each `<li>` element within the `renderLeaderboard` function.
    // No separate listener on the `<ul>` is strictly needed for that anymore,
    // but the sorting listeners on the buttons are kept.

}); // End DOMContentLoaded
