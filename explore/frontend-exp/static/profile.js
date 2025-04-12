// profile.js
document.addEventListener('DOMContentLoaded', () => {
    const profileName = document.getElementById('profile-name');
    const profileTitle = document.getElementById('profile-title');
    const profileRank = document.getElementById('profile-rank');
    const profileAlmagems = document.getElementById('profile-almagems');
    const profileBadges = document.getElementById('profile-badges');
    const profileSolved = document.getElementById('profile-solved');
    const profileLinks = document.getElementById('profile-links');
    const achievements = document.getElementById('achievements');
    const editProfileButton = document.getElementById('edit-profile-button');
    const userName = "John Doe"; //Replace with logic to get the logged in user's name

    async function fetchUserProfile() {
        try {
            const response = await fetch(`/api/users/${userName}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const userData = await response.json();

            // Check if userData has the expected properties
            console.log("API Response:", userData); // Log the API response for inspection

            profileName.textContent = userData.name;
            profileTitle.textContent = `${userData.profession} of ${userData.alma_mater}`;
            profileRank.textContent = userData.activity_score; // Replace with actual data
            profileAlmagems.textContent = userData.alumni_gems;
            profileBadges.textContent = "5"; // Replace with actual data
            profileSolved.textContent = "75"; // Replace with actual data
            profileLinks.textContent = "250"; // Replace with actual data
            achievements.textContent = userData.achievements;
        } catch (error) {
            console.error('Error fetching user profile:', error);
        }

    fetchUserProfile();

    editProfileButton.addEventListener('click', () => {
        // Implement edit profile functionality here (e.g., show a modal)
        alert('Edit profile functionality to be implemented.');
    });
});