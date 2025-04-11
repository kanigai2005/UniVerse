async function loadLeaderboard() {
    try {
        const response = await fetch("/api/leaderboard");
        if (!response.ok) {
            throw new Error(`Failed to fetch leaderboard: ${response.status}`);
        }
        const users = await response.json();

        const leaderboardTable = document.getElementById("leaderboard-table");
        if (!leaderboardTable) return;

        leaderboardTable.innerHTML = `
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Name</th>
                    <th>Activity Score</th>
                    <th>Achievements</th>
                    <th>Alumni Gems</th>
                    <th>Profile</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        `;

        const tableBody = leaderboardTable.querySelector("tbody");

        users.forEach((user, index) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${user.name}</td>
                <td>${user.activity_score}</td>
                <td>${user.achievements.join(', ') || '-'}</td>
                <td>${user.alumni_gems}</td>
                <td><button class='view-profile-btn' data-name="${encodeURIComponent(user.name)}">View Profile</button></td>
            `;
            tableBody.appendChild(row);
        });

        // Add event listeners to the "View Profile" buttons
        const profileButtons = tableBody.querySelectorAll('.view-profile-btn');
        profileButtons.forEach(button => {
            button.addEventListener('click', function() {
                const username = this.getAttribute('data-name');
                window.location.href = `leader-profile.html?name=${username}`;
            });
        });

        // Optional: Add sorting functionality
        addSorting(leaderboardTable);

    } catch (error) {
        console.error("Error loading leaderboard:", error);
        alert("Failed to load leaderboard.");
    }
}

function addSorting(table) {
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        header.addEventListener('click', () => {
            sortTable(table, index);
        });
        // Add visual cue for sortable columns (optional)
        header.style.cursor = 'pointer';
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isNumber = columnIndex === 2 || columnIndex === 4; // Activity Score or Alumni Gems

    const sortedRows = rows.sort((rowA, rowB) => {
        const cellA = rowA.querySelectorAll('td')[columnIndex].textContent.trim();
        const cellB = rowB.querySelectorAll('td')[columnIndex].textContent.trim();

        let valueA = isNumber ? parseInt(cellA, 10) : cellA.toLowerCase();
        let valueB = isNumber ? parseInt(cellB, 10) : cellB.toLowerCase();

        if (isNaN(valueA)) valueA = cellA.toLowerCase();
        if (isNaN(valueB)) valueB = cellB.toLowerCase();

        if (valueA < valueB) {
            return -1;
        }
        if (valueA > valueB) {
            return 1;
        }
        return 0;
    });

    // Remove existing rows
    tbody.innerHTML = '';

    // Append sorted rows
    sortedRows.forEach(row => tbody.appendChild(row));

    // Re-number the rank column after sorting
    const rankCells = tbody.querySelectorAll('td:first-child');
    rankCells.forEach((cell, index) => {
        cell.textContent = index + 1;
    });
}

// Optional: Add a refresh button functionality
document.getElementById('refresh-leaderboard-button')?.addEventListener('click', loadLeaderboard);

document.addEventListener('DOMContentLoaded', loadLeaderboard);