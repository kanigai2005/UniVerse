// Get the username from localStorage
const loggedInUserName = localStorage.getItem('username');
const profileNameElement = document.getElementById('profile-name');
const profileTitleElement = document.getElementById('profile-title');
const profileRankElement = document.getElementById('profile-rank');
const profileAlmagemsElement = document.getElementById('profile-almagems');
const profileBadgesElement = document.getElementById('profile-badges');
const profileSolvedElement = document.getElementById('profile-solved');
const profileLinksElement = document.getElementById('profile-links');
const editProfileButton = document.getElementById('edit-profile-button');
const connectButton = document.getElementById('connect-button'); // Get the connect button
const achievement1Element = document.getElementById('achievement-1');
const achievement2Element = document.getElementById('achievement-2');
const achievement3Element = document.getElementById('achievement-3');

// Function to fetch and display user data
function fetchAndDisplayUserData(userName) {
    fetch(`/api/users/${userName}`) //  Fetch user data
        .then(response => response.json())
        .then(user => {
            if (user) {
                profileNameElement.textContent = user.name;
                profileTitleElement.textContent = user.profession ? `Alumni of ${user.alma_mater}, ${user.profession}` : `Alumni of ${user.alma_mater}`;
                profileRankElement.textContent = `#${user.rank || 'N/A'}`;
                profileAlmagemsElement.textContent = user.alumni_gems || 'N/A';
                profileBadgesElement.textContent = user.badges || '0';
                profileSolvedElement.textContent = user.solved || '0';
                profileLinksElement.textContent = user.links || '0';

                 //Dynamically set Achievements
                const achievements = user.achievements || [];
                achievement1Element.textContent = achievements.length > 0 ? achievements[0] : "No achievements available";
                achievement2Element.textContent = achievements.length > 1 ? achievements[1] : "No achievements available";
                achievement3Element.textContent = achievements.length > 2 ? achievements[2] : "No achievements available";

            } else {
                profileNameElement.textContent = 'User Not Found';
                profileTitleElement.textContent = 'User Not Found';
                // Clear other fields or set default values
                profileRankElement.textContent = 'N/A';
                profileAlmagemsElement.textContent = 'N/A';
                profileBadgesElement.textContent = '0';
                profileSolvedElement.textContent = '0';
                profileLinksElement.textContent = '0';
                achievement1Element.textContent = "No achievements available";
                achievement2Element.textContent = "No achievements available";
                achievement3Element.textContent = "No achievements available";
            }
        })
        .catch(error => {
            console.error('Error fetching user data:', error);
            profileNameElement.textContent = 'Error Loading Data';
            profileTitleElement.textContent = 'Error Loading Data';
            // Clear other fields or set default values
            profileRankElement.textContent = 'N/A';
            profileAlmagemsElement.textContent = 'N/A';
            profileBadgesElement.textContent = '0';
            profileSolvedElement.textContent = '0';
            profileLinksElement.textContent = '0';
            achievement1Element.textContent = "No achievements available";
            achievement2Element.textContent = "No achievements available";
            achievement3Element.textContent = "No achievements available";
        });
}

// Call the function to fetch and display data
if (loggedInUserName) {
     fetchAndDisplayUserData(loggedInUserName);
} else {
    profileNameElement.textContent = "Please Login";
    profileTitleElement.textContent = "Please Login";
}


// Edit profile functionality (remains the same as before)
editProfileButton.addEventListener('click', () => {
    // Redirect to the edit profile page, passing the username as a query parameter
    window.location.href = `/edit-profile.html?username=${loggedInUserName}`;
});

// Connect button functionality
connectButton.addEventListener('click', () => {
    if (loggedInUserName) {
        // Implement the connection logic here.
        alert(`Connecting with ${profileNameElement.textContent}! (Placeholder)`);
        // You would typically send a request to your backend API to handle the connection.
        fetch(`/api/users/${loggedInUserName}/connect`, { // Example API endpoint
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ userToConnectWith: profileNameElement.textContent }), //send the name of the profile to connect with
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message); // Show success message
            } else {
                alert(data.message || 'Failed to connect.'); // Show error message
            }
        })
        .catch(error => {
            console.error('Error connecting:', error);
            alert('An error occurred while connecting.');
        });
    } else {
        alert('Please log in to connect with others.');
    }
});
