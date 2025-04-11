function getUsernameFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('name');
}

async function loadUserProfile() {
    const username = getUsernameFromUrl();
    if (!username) {
        console.error("Username not provided in URL.");
        alert("No user specified to view.");
        return;
    }

    try {
        const response = await fetch(`/api/user/${encodeURIComponent(username)}`);
        console.log("Fetch Response:", response); // Log the entire response object

        if (!response.ok) {
            console.error("Fetch failed with status:", response.status);
            let errorMessage = `Failed to fetch user profile: ${response.status}`;
            try {
                const errorData = await response.json();
                console.error("Error Data from Backend:", errorData);
                errorMessage += ` - ${JSON.stringify(errorData)}`;
            } catch (e) {
                console.error("Failed to parse error JSON:", e);
            }
            alert(errorMessage);
            return;
        }

        const user = await response.json();
        console.log("User Data Received:", user);

        document.getElementById('profile-name').textContent = user.name;
        const profileEmailElement = document.getElementById('profile-email');
        if (profileEmailElement) {
            profileEmailElement.textContent = user.email || 'N/A';
        } else {
            console.error("Element with ID 'profile-email' not found.");
        }
        const profileActivityElement = document.getElementById('profile-activity');
        if (profileActivityElement) {
            profileActivityElement.textContent = user.activity_score || 'N/A';
        } else {
            console.error("Element with ID 'profile-activity' not found.");
        }
        const profileGemsElement = document.getElementById('profile-gems');
        if (profileGemsElement) {
            profileGemsElement.textContent = user.alumni_gems || 'N/A';
        } else {
            console.error("Element with ID 'profile-gems' not found.");
        }

        const achievementsList = document.getElementById('achievements-list');
        if (achievementsList) {
            achievementsList.innerHTML = '';
            if (user.achievements && Array.isArray(user.achievements)) {
                user.achievements.forEach(achievement => {
                    const listItem = document.createElement('li');
                    listItem.textContent = achievement;
                    achievementsList.appendChild(listItem);
                });
            } else {
                const listItem = document.createElement('li');
                listItem.textContent = 'No achievements listed.';
                achievementsList.appendChild(listItem);
            }
        } else {
            console.error("Element with ID 'achievements-list' not found.");
        }

    } catch (error) {
        console.error("Error loading user profile:", error);
        alert(`Failed to load user profile: ${error.message}`);
    }
}

document.addEventListener('DOMContentLoaded', loadUserProfile);