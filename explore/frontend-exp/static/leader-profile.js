// static/leader-profile.js

// Function to extract the user's name from the URL query parameters
function getUsernameFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('name');
}

// Function to fetch and display the user's profile
async function loadUserProfile() {
    const username = getUsernameFromUrl();
    if (!username) {
        console.error("Username not provided in URL.");
        return;
    }

    try {
        const response = await fetch(`/api/user/${username}`);
        if (!response.ok) {
            throw new Error("Failed to fetch user profile");
        }
        const user = await response.json();

        // Display user profile information
        document.getElementById('profile-name').textContent = user.name;
        document.getElementById('profile-activity').textContent = user.activity_score;
        document.getElementById('profile-gems').textContent = user.alumni_gems;

        // Display achievements
        const achievementsList = document.getElementById('achievements-list');
        achievementsList.innerHTML = ''; // Clear existing list
        user.achievements.forEach(achievement => {
            const listItem = document.createElement('li');
            listItem.textContent = achievement;
            achievementsList.appendChild(listItem);
        });

    } catch (error) {
        console.error("Error loading user profile:", error);
        alert("Failed to load user profile.");
    }
}

// Load the user profile when the page loads
document.addEventListener('DOMContentLoaded', loadUserProfile);