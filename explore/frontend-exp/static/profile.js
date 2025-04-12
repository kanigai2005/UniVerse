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

    const userName = localStorage.getItem('username'); // Get username from local storage

    if (!userName) {
        console.error('Username not found in local storage.');
        alert('Please log in to view your profile.');
        return; // Stop execution if username is not found
    }

    async function fetchUserProfile() {
        try {
            const response = await fetch(`/api/users/${userName}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const userData = await response.json();

            console.log("API Response:", userData);

            if (userData) {
                profileName.textContent = userData.name || 'N/A';
                profileTitle.textContent = userData.profession ? `${userData.profession} of ${userData.alma_mater}` : 'N/A';
                profileRank.textContent = userData.activity_score || 'N/A';
                profileAlmagems.textContent = userData.alumni_gems || 'N/A';
                profileBadges.textContent = userData.badges || 'N/A'; // Replace "5"
                profileSolved.textContent = userData.solved || 'N/A'; // Replace "75"
                profileLinks.textContent = userData.links || 'N/A'; // Replace "250"
                achievements.textContent = userData.achievements || 'N/A';
            }
        } catch (error) {
            console.error('Error fetching user profile:', error);
            alert('Failed to load profile. Please try again.');
        }
    }

    fetchUserProfile();

    editProfileButton.addEventListener('click', () => {
        alert('Edit profile functionality to be implemented.');
    });
});