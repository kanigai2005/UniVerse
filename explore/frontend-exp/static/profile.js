document.addEventListener('DOMContentLoaded', () => {
    const profileNameElement = document.getElementById('profile-name');
    const profileTitleElement = document.getElementById('profile-title');
    const profileRankElement = document.getElementById('profile-rank');
    const profileAlmagemsElement = document.getElementById('profile-almagems');
    const profileBadgesElement = document.getElementById('profile-badges');
    const profileSolvedElement = document.getElementById('profile-solved');
    const profileLinksElement = document.getElementById('profile-links');
    const editProfileButton = document.getElementById('edit-profile-button');
    const connectButton = document.getElementById('connect-button');
    const achievement1Element = document.getElementById('achievement-1');
    const achievement2Element = document.getElementById('achievement-2');
    const achievement3Element = document.getElementById('achievement-3');

    // Get the username from localStorage
    const loggedInUserName = localStorage.getItem('username');

    // Function to fetch and display user data
    function fetchAndDisplayUserData(userName) {
        if (!userName) {
            console.error('Username is undefined. Cannot fetch user data.');
            profileNameElement.textContent = 'Error: No User Identified';
            profileTitleElement.textContent = 'Please ensure you are logged in.';
            return;
        }

        fetch(`/api/users/${userName}`)
            .then(response => {
                if (!response.ok) {
                    console.error(`Error fetching user data: ${response.status}`);
                    profileNameElement.textContent = 'Error Loading Data';
                    profileTitleElement.textContent = `HTTP error: ${response.status}`;
                    return Promise.reject(new Error(`Failed to fetch user data: ${response.status}`));
                }
                return response.json();
            })
            .then(user => {
                if (user) {
                    profileNameElement.textContent = user.name;
                    profileTitleElement.textContent = user.profession ? `Alumni of ${user.alma_mater}, ${user.profession}` : `Alumni of ${user.alma_mater}`;
                    profileRankElement.textContent = `#${user.rank || 'N/A'}`;
                    profileAlmagemsElement.textContent = user.alumni_gems || 'N/A';
                    profileBadgesElement.textContent = user.badges || '0';
                    profileSolvedElement.textContent = user.solved || '0';
                    profileLinksElement.textContent = user.links || '0';

                    const achievements = user.achievements || [];
                    achievement1Element.textContent = achievements.length > 0 ? achievements[0] : "No achievements available";
                    achievement2Element.textContent = achievements.length > 1 ? achievements[1] : "No achievements available";
                    achievement3Element.textContent = achievements.length > 2 ? achievements[2] : "No achievements available";
                } else {
                    profileNameElement.textContent = 'User Not Found';
                    profileTitleElement.textContent = 'User Not Found';
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
                profileTitleElement.textContent = 'An error occurred while fetching user data.';
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

    // Function to create and show the edit profile pop-up
    function showEditProfilePopup() {
        if (!loggedInUserName) {
            alert('Please log in to edit your profile.');
            return;
        }

        const popupContainer = document.createElement('div');
        popupContainer.id = 'edit-profile-popup';
        popupContainer.style.position = 'fixed';
        popupContainer.style.top = '50%';
        popupContainer.style.left = '50%';
        popupContainer.style.transform = 'translate(-50%, -50%)';
        popupContainer.style.backgroundColor = '#fff';
        popupContainer.style.padding = '20px';
        popupContainer.style.border = '1px solid #ccc';
        popupContainer.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
        popupContainer.style.zIndex = '1000';

        const title = document.createElement('h2');
        title.textContent = 'Edit Profile';
        popupContainer.appendChild(title);

        const almaMaterLabel = document.createElement('label');
        almaMaterLabel.textContent = 'Alma Mater:';
        const almaMaterInput = document.createElement('input');
        almaMaterInput.type = 'text';
        almaMaterInput.id = 'edit-alma-mater';
        almaMaterInput.value = profileTitleElement.textContent.split('Alumni of ')[1]?.split(',')[0] || ''; // Pre-fill if possible
        popupContainer.appendChild(almaMaterLabel);
        popupContainer.appendChild(almaMaterInput);
        popupContainer.appendChild(document.createElement('br'));

        const professionLabel = document.createElement('label');
        professionLabel.textContent = 'Profession:';
        const professionInput = document.createElement('input');
        professionInput.type = 'text';
        professionInput.id = 'edit-profession';
        professionInput.value = profileTitleElement.textContent.includes(',') ? profileTitleElement.textContent.split(', ')[1] : ''; // Pre-fill if possible
        popupContainer.appendChild(professionLabel);
        popupContainer.appendChild(professionInput);
        popupContainer.appendChild(document.createElement('br'));

        const saveButton = document.createElement('button');
        saveButton.textContent = 'Save Changes';
        saveButton.addEventListener('click', () => {
            const newAlmaMater = document.getElementById('edit-alma-mater').value;
            const newProfession = document.getElementById('edit-profession').value;
            saveProfileChanges(newAlmaMater, newProfession);
            document.body.removeChild(popupContainer);
        });
        popupContainer.appendChild(saveButton);

        const cancelButton = document.createElement('button');
        cancelButton.textContent = 'Cancel';
        cancelButton.style.marginLeft = '10px';
        cancelButton.addEventListener('click', () => {
            document.body.removeChild(popupContainer);
        });
        popupContainer.appendChild(cancelButton);

        document.body.appendChild(popupContainer);
    }

    // Function to send updated profile data to the backend
    function saveProfileChanges(almaMater, profession) {
        if (!loggedInUserName) {
            alert('Please log in to save changes.');
            return;
        }

        fetch(`/api/users/${loggedInUserName}`, { // Use PUT or PATCH to update
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ alma_mater: almaMater, profession: profession }),
        })
            .then(response => {
                if (response.ok) {
                    alert('Profile updated successfully!');
                    fetchAndDisplayUserData(loggedInUserName); // Refresh UI
                } else {
                    return response.json().then(data => {
                        alert(`Failed to update profile: ${data.message || response.statusText}`);
                    });
                }
            })
            .catch(error => {
                console.error('Error updating profile:', error);
                alert('An error occurred while updating your profile.');
            });
    }

    // Event listener for the Edit Profile button
    editProfileButton.addEventListener('click', showEditProfilePopup);

    // Connect button functionality (remains the same)
    connectButton.addEventListener('click', () => {
        if (loggedInUserName) {
            fetch(`/api/users/${loggedInUserName}/connect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ userToConnectWith: profileNameElement.textContent }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                    } else {
                        alert(data.message || 'Failed to connect.');
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

    // Initial fetch of user data
    if (loggedInUserName) {
        fetchAndDisplayUserData(loggedInUserName);
    } else {
        profileNameElement.textContent = "Please Login";
        profileTitleElement.textContent = "Please Login";
        window.location.href = '/login.html';
    }
});