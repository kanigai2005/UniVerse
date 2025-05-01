let currentSortKey = 'alumni_gems';
let sortDirection = 'desc';

async function loadLeaderboard(sortBy = 'alumni_gems', direction = 'desc') {
    try {
        const response = await fetch("/api/leaderboard");
        if (!response.ok) {
            throw new Error(`Failed to fetch leaderboard: ${response.status}`);
        }
        const users = await response.json();

        const leaderboardList = document.getElementById("leaderboard-list");
        if (!leaderboardList) {
            console.error("Leaderboard list element not found.");
            return; // Stop if the list is not found
        }

        // Sort users based on the specified key and direction
        users.sort((a, b) => {
            const valueA = a[sortBy];
            const valueB = b[sortBy];

            if (typeof valueA === 'string') {
                return direction === 'asc' ? valueA.localeCompare(valueB) : valueB.localeCompare(valueA);
            } else {
                return direction === 'asc' ? valueA - valueB : valueB - valueA;
            }
        });

        // Clear the list before adding new data
        leaderboardList.innerHTML = '';

        users.forEach((user) => {
            const listItem = document.createElement("li");
            listItem.addEventListener('click', () => {
                window.location.href = `profile/${encodeURIComponent(user.profile_id)}`;
            });
            listItem.innerHTML = `
                <div class="leaderboard-item-details">
                    <div class="leader-info">
                        <div class="leader-name">${user.name}</div>
                        <div class="leader-details">
                            ${user.role ? `<span>Role: ${user.role}</span><br>` : ''}
                            ${user.domain ? `<span>Domain: ${user.domain}</span>` : ''}
                        </div>
                    </div>
                    <div class="gem-count">${user.alumni_gems} <span style="font-size: 0.8em;">Gems</span></div>
                </div>
                <a href="profile/${encodeURIComponent(user.profile_id)}" class="view-profile-btn">View Profile</a>
            `;
            leaderboardList.appendChild(listItem);
        });

        // Update sort indicators (optional visual feedback)
        updateSortIndicators(sortBy, direction);

    } catch (error) {
        console.error("Error loading leaderboard:", error);
        alert("Failed to load the Gemstone Gallery.");
    }
}

function updateSortIndicators(sortBy, direction) {
    const listItems = document.querySelectorAll('#leaderboard-list li');
    listItems.forEach(item => {
        // Basic indicator - you can enhance this with icons
        const gemCountSpan = item.querySelector('.gem-count');
        const nameDiv = item.querySelector('.leader-name');

        if (sortBy === 'alumni_gems') {
            gemCountSpan.innerHTML = `${parseInt(gemCountSpan.textContent)} Gems ${direction === 'asc' ? '▲' : '▼'}`;
            nameDiv.innerHTML = nameDiv.textContent.replace(/ [▲▼]$/, ''); // Remove previous indicator
        } else if (sortBy === 'name') {
            nameDiv.innerHTML = `${nameDiv.textContent} ${direction === 'asc' ? '▲' : '▼'}`;
            const prevGemCount = gemCountSpan.textContent.replace(/ [▲▼]$/, '').replace(' Gems', '');
            gemCountSpan.innerHTML = `${prevGemCount} Gems`; // Reset gem sort indicator
        } else {
            const prevGemCount = gemCountSpan.textContent.replace(/ [▲▼]$/, '').replace(' Gems', '');
            gemCountSpan.innerHTML = `${prevGemCount} Gems`;
            nameDiv.innerHTML = nameDiv.textContent.replace(/ [▲▼]$/, '');
        }
    });
}

// Event listener for clicking list items to view profile
document.addEventListener('DOMContentLoaded', () => {
    loadLeaderboard(currentSortKey, sortDirection);

    const leaderboardList = document.getElementById('leaderboard-list');
    if (leaderboardList) {
        leaderboardList.addEventListener('click', (event) => {
            const listItem = event.target.closest('li');
            if (listItem) {
                const userNameElement = listItem.querySelector('.leader-name');
                if (userNameElement) {
                    // Extract profile ID (you might need to store this as a data attribute)
                    // For now, using the name as in the previous logic
                    const userName = userNameElement.textContent;
                    const user = Array.from(leaderboardList.children).find(li => li.querySelector('.leader-name').textContent === userName);
                    if (user) {
                        const profileLink = user.querySelector('.view-profile-btn');
                        if (profileLink) {
                            window.location.href = profileLink.href;
                        }
                    }
                }
            }
        });
    }

    const refreshButton = document.getElementById('refresh-leaderboard-button');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            loadLeaderboard(currentSortKey, sortDirection);
        });
    }

    // Make the list items sortable by clicking
    leaderboardList?.addEventListener('click', (event) => {
        const clickedElement = event.target.closest('li');
        if (clickedElement) {
            const gemCountElement = clickedElement.querySelector('.gem-count');
            const nameElement = clickedElement.querySelector('.leader-name');

            if (event.target === gemCountElement || event.target.parentNode === gemCountElement) {
                const newSortKey = 'alumni_gems';
                if (newSortKey === currentSortKey) {
                    sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSortKey = newSortKey;
                    sortDirection = 'desc'; // Default sort for gems
                }
                loadLeaderboard(currentSortKey, sortDirection);
            } else if (event.target === nameElement) {
                const newSortKey = 'name';
                if (newSortKey === currentSortKey) {
                    sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSortKey = newSortKey;
                    sortDirection = 'asc'; // Default sort for names
                }
                loadLeaderboard(currentSortKey, sortDirection);
            }
        }
    });
});