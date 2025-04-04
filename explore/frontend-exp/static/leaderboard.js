// static/leaderboard.js

// Function to fetch and display the leaderboard
// static/leaderboard.js

// Function to fetch and display the leaderboard
async function loadLeaderboard() {
    try {
        const response = await fetch("/api/leaderboard");
        if (!response.ok) {
            throw new Error("Failed to fetch leaderboard");
        }
        const users = await response.json();

        const leaderboardTable = document.getElementById("leaderboard-table");
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
        `; // Clear and initialize table

        const tableBody = leaderboardTable.querySelector("tbody");

        users.forEach((user, index) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${user.name}</td>
                <td>${user.activity_score}</td>
                <td>${user.achievements.join(', ')}</td>
                <td>${user.alumni_gems}</td>
                <td><a href="leader-profile.html?name=${encodeURIComponent(user.name)}">View Profile</a></td>
            `;
            tableBody.appendChild(row);
        });

    } catch (error) {
        console.error("Error loading leaderboard:", error);
        alert("Failed to load leaderboard.");
    }
}

// Load the leaderboard when the page loads
document.addEventListener('DOMContentLoaded', loadLeaderboard);

// Function to fetch and display job referrals
async function loadJobReferrals() {
    try {
        const response = await fetch("http://127.0.0.1:8000/job_referrals");
        if (!response.ok) {
            throw new Error("Failed to fetch job referrals");
        }
        const referrals = await response.json();

        const referralList = document.getElementById("job-referral-list");
        referralList.innerHTML = ''; // Clear existing list items

        referrals.forEach(referral => {
            const listItem = document.createElement("li");
            listItem.innerHTML = `
                🔥 ${referral.name} referred ${referral.referral_count} alumni to jobs!
                <button class="view-profile" onclick="location.href='profile.html?name=${encodeURIComponent(referral.name)}'">View Profile</button>
            `;
            referralList.appendChild(listItem);
        });

    } catch (error) {
        console.error("Error loading job referrals:", error);
        alert("Failed to load job referrals.");
    }
}

// Function to fetch and display badges
async function loadBadges() {
    try {
        const response = await fetch("http://127.0.0.1:8000/badges");
        if (!response.ok) {
            throw new Error("Failed to fetch badges");
        }
        const badges = await response.json();

        const badgeContainer = document.getElementById("badge-container");
        badgeContainer.innerHTML = ''; // Clear existing badges

        badges.forEach(badge => {
            const badgeDiv = document.createElement("div");
            badgeDiv.classList.add("badge");
            badgeDiv.textContent = badge.name;
            badgeContainer.appendChild(badgeDiv);
        });

    } catch (error) {
        console.error("Error loading badges:", error);
        alert("Failed to load badges.");
    }
}

// Load data when the page loads
document.addEventListener('DOMContentLoaded', () => {
    loadLeaderboard();
    loadJobReferrals();
    loadBadges();
});