// --- Utility: Simple HTML Escaping ---
function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) {
        return '';
    }
    const str = String(unsafe);
    return str
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
}

// --- Navbar Update Logic ---
async function updateNavbar() {
    const navProfileLink = document.getElementById('nav-profile-link');
    if (!navProfileLink) {
        // This console.warn was seen in your screenshot, so the ID might be missing in leaderboard.html nav
        console.warn("Navbar profile link element (id='nav-profile-link') not found.");
        return null;
    }
    try {
        const response = await fetch('/api/users/me');
        if (!response.ok) {
            if (response.status === 401 || response.status === 307) {
                navProfileLink.href = "/login.html";
            } else {
                console.warn("Navbar update: Failed to fetch current user, status:", response.status);
                navProfileLink.href = "/login.html";
            }
            localStorage.removeItem('username');
            return null;
        }
        const userData = await response.json();
        if (userData && userData.username) {
            // Assuming leaderboard.html and profile.html are under /user/
            navProfileLink.href = `/user/profile.html?username=${encodeURIComponent(userData.username)}`;
            localStorage.setItem('username', userData.username);
            return userData;
        } else {
            console.warn("Navbar update: User data fetched but username missing.");
            navProfileLink.href = "/login.html";
            localStorage.removeItem('username');
            return null;
        }
    } catch (error) {
        console.error("Navbar update error:", error);
        navProfileLink.href = "/login.html";
        localStorage.removeItem('username');
        return null;
    }
}


// --- Leaderboard Logic ---
let currentSortKey = 'activity_score';
let sortDirection = 'desc';
let leaderboardData = [];

const leaderboardList = document.getElementById("leaderboard-list");
// Sort buttons will be selected inside DOMContentLoaded

async function fetchLeaderboardData() {
    if (!leaderboardList) {
        console.error("Leaderboard list container not found. Aborting fetch.");
        return;
    }
    leaderboardList.innerHTML = '<p class="loading">Loading leaderboard...</p>';
    console.log("Fetching leaderboard data from /api/leaderboard...");
    try {
        const response = await fetch("/api/leaderboard"); // Make sure BASE_API_PATH is part of this if used consistently
        console.log("API Response Status:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error("API Error Response Text:", errorText);
            let errorDetail = `HTTP error ${response.status}`;
            try {
                const errorJson = JSON.parse(errorText);
                errorDetail = errorJson.detail || errorDetail;
            } catch (e) {
                if(errorText.length < 200 && errorText.length > 0) errorDetail += `: ${errorText}`;
            }
            throw new Error(errorDetail);
        }
        leaderboardData = await response.json();
        console.log("Fetched leaderboard data (raw):", JSON.parse(JSON.stringify(leaderboardData))); // Log a deep copy

        if (!Array.isArray(leaderboardData)) {
            console.error("Fetched data is not an array:", leaderboardData);
            throw new Error("Invalid data format: Expected an array.");
        }
        renderLeaderboard();
    } catch (error) {
        console.error("Error fetching leaderboard data:", error);
        leaderboardList.innerHTML = `<p class="error-message">Failed to load leaderboard: ${escapeHtml(error.message)}</p>`;
    }
}

function sortData() {
    if (!Array.isArray(leaderboardData)) {
        console.error("Cannot sort: leaderboardData is not an array.", leaderboardData);
        return;
    }

    leaderboardData.sort((a, b) => {
        if (typeof a !== 'object' || a === null || typeof b !== 'object' || b === null) return 0;

        const valueA = a[currentSortKey];
        const valueB = b[currentSortKey];

        const valA = valueA === null || valueA === undefined ? (sortDirection === 'asc' ? Infinity : -Infinity) : valueA;
        const valB = valueB === null || valueB === undefined ? (sortDirection === 'asc' ? Infinity : -Infinity) : valueB;

        if (currentSortKey === 'username') {
            return sortDirection === 'asc'
                ? String(valA).localeCompare(String(valB), undefined, { sensitivity: 'base' })
                : String(valB).localeCompare(String(valA), undefined, { sensitivity: 'base' });
        } else {
             return sortDirection === 'asc' ? Number(valA) - Number(valB) : Number(valB) - Number(valA);
        }
    });
}

function renderLeaderboard() {
     if (!leaderboardList) {
         console.error("Leaderboard list element not found during render.");
         return;
     }
     leaderboardList.innerHTML = '';

     if(!Array.isArray(leaderboardData) || leaderboardData.length === 0) {
         leaderboardList.innerHTML = '<p class="no-data">Leaderboard is currently empty or data is unavailable.</p>';
         return;
     }

     sortData();

     leaderboardData.forEach((user, index) => {
        if (typeof user !== 'object' || user === null || !user.username) {
            console.warn("Skipping invalid user data in leaderboard:", user);
            return;
        }

        const listItem = document.createElement("li");
        listItem.classList.add('leaderboard-list-item');

        listItem.addEventListener('click', () => {
            window.location.href = `/user/profile.html?username=${encodeURIComponent(user.username)}`;
        });

        const displayName = user.name || user.username;

        let detailsArray = [];
        if (user.profession) detailsArray.push(escapeHtml(user.profession));
        if (user.department) detailsArray.push(escapeHtml(user.department));


        listItem.innerHTML = `
            <div class="leaderboard-item-details">
                <span class="leader-rank">#${index + 1}</span>
                <div class="leader-info">
                    <div class="leader-name">${escapeHtml(displayName)}</div>
                    ${detailsArray.length > 0 ? `<p class="leader-details"><span>${detailsArray.join('</span> | <span>')}</span></p>` : ''}
                </div>
            </div>
            <div class="score-section">
                 <div class="gem-count">${user.alumni_gems !== undefined ? user.alumni_gems : 0} <i class="fas fa-gem"></i></div>
                 <div class="activity-score">Score: ${user.activity_score !== undefined ? user.activity_score : 0}</div>
            </div>
        `;
        leaderboardList.appendChild(listItem);
    });
    // Get sortButtons here as they are now in DOM if not already global
    const sortButtons = {
        gems: document.getElementById("sort-gems"),
        activity: document.getElementById("sort-activity"),
        name: document.getElementById("sort-name")
    };
    updateSortIndicatorsUI(sortButtons);
}

function updateSortIndicatorsUI(sortButtons) {
    if (!sortButtons || !sortButtons.gems || !sortButtons.activity || !sortButtons.name) {
        // If called before DOMContentLoaded fully initializes sortButtons object
        console.warn("Sort buttons not fully initialized for UI update.");
        return;
    }

    Object.values(sortButtons).forEach(btn => {
        if (btn) {
            btn.classList.remove('active');
            const indicator = btn.querySelector('.sort-indicator');
            if (indicator) indicator.textContent = '';
        }
    });

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

function handleSortClick(event, sortButtons) {
     const button = event.target.closest('button');
     if(!button || !button.dataset.sortkey) return;

     const newSortKey = button.dataset.sortkey;

     if (newSortKey === currentSortKey) {
         sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
     } else {
         currentSortKey = newSortKey;
         sortDirection = (newSortKey === 'username') ? 'asc' : 'desc';
     }
     renderLeaderboard(); // sortData is called within renderLeaderboard
     // updateSortIndicatorsUI is also called at the end of renderLeaderboard
}


// --- Initial Setup ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("Leaderboard DOMContentLoaded.");

    const sortButtons = { // Define sortButtons here after DOM is loaded
         gems: document.getElementById("sort-gems"),
         activity: document.getElementById("sort-activity"),
         name: document.getElementById("sort-name")
    };

    if (sortButtons.gems) sortButtons.gems.addEventListener('click', (event) => handleSortClick(event, sortButtons));
    if (sortButtons.activity) sortButtons.activity.addEventListener('click', (event) => handleSortClick(event, sortButtons));
    if (sortButtons.name) sortButtons.name.addEventListener('click', (event) => handleSortClick(event, sortButtons));

    updateNavbar(); // This should now find #nav-profile-link
    fetchLeaderboardData();
    // Initial call to set indicators based on default sort
    // updateSortIndicatorsUI is called at the end of renderLeaderboard, so this might be redundant
    // but safe to call if fetchLeaderboardData is very quick and renderLeaderboard hasn't set them yet.
    updateSortIndicatorsUI(sortButtons);
});