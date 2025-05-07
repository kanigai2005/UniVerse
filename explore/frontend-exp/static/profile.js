// --- Utility: Simple HTML Escaping ---
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') { return unsafe === null || unsafe === undefined ? '' : unsafe; }
    // Corrected escaping
    return unsafe
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
}

// --- Navbar Update Logic (Optional but recommended) ---
async function updateNavbar() {
    const navProfileLink = document.getElementById('nav-profile-link');
    if (!navProfileLink) { console.warn("Navbar profile link element not found."); return null; }
    try {
        const response = await fetch('/api/users/me');
        if (!response.ok) {
            if (response.status === 401 || response.status === 307) { navProfileLink.href = "/login.html"; localStorage.removeItem('username'); }
            else { navProfileLink.href = "/login.html"; localStorage.removeItem('username'); }
            return null;
        }
        const userData = await response.json();
        if (userData && userData.username) {
            // Link navbar profile item to the user's own profile page
            navProfileLink.href = `/profile.html?username=${encodeURIComponent(userData.username)}`;
            localStorage.setItem('username', userData.username);
            return userData; // Return user data for potential use
        } else { navProfileLink.href = "/login.html"; localStorage.removeItem('username'); return null; }
    } catch (error) { console.error("Navbar update error:", error); navProfileLink.href = "/login.html"; localStorage.removeItem('username'); return null; }
}


// --- Profile Page Logic ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("Profile page DOM loaded.");

    // --- Get Elements ---
    const profileContainerMain = document.getElementById('profile-container-main');
    const profileUsernameElement = document.getElementById('profile-username');
    const profileTitleElement = document.getElementById('profile-title');
    const profileActivityElement = document.getElementById('profile-activity');
    const profileAlmagemsElement = document.getElementById('profile-almagems');
    const profileBadgesElement = document.getElementById('profile-badges');
    const profileSolvedElement = document.getElementById('profile-solved');
    const profileLinksElement = document.getElementById('profile-links');
    const profileProfessionElement = document.getElementById('profile-profession');
    const profileCompanyElement = document.getElementById('profile-company');
    const profileDepartmentElement = document.getElementById('profile-department');
    const profileAlmaMaterElement = document.getElementById('profile-alma-mater');
    const profileInterviewsElement = document.getElementById('profile-interviews');
    const profileInternshipsElement = document.getElementById('profile-internships');
    const profileStartupsElement = document.getElementById('profile-startups');
    const profileMilestonesElement = document.getElementById('profile-milestones');
    const profileAdviceElement = document.getElementById('profile-advice');
    const profileAchievementsElement = document.getElementById('profile-achievements');
    // Action Elements
    const editProfileButton = document.getElementById('edit-profile-button');
    const networkLink = document.getElementById('network-link'); // The <a> tag
    const networkButton = document.getElementById('network-button'); // The <button> inside <a>

    let profileData = null; // Stores the profile data object
    let isOwnProfile = false; // Flag: is the viewer looking at their own profile?
    let currentUserDataForCheck = null; // Store fetched current user to compare username

    // --- Check Essential Elements ---
     if (!profileContainerMain || !profileUsernameElement || !editProfileButton || !networkLink || !networkButton) {
        console.error("CRITICAL ERROR: One or more essential profile elements (container, username, action buttons/links) not found!");
        if(profileContainerMain) profileContainerMain.innerHTML = '<p class="error-message" style="color:red;">Page setup error.</p>';
        return; // Stop initialization
    }


    // --- Read Embedded Data ---
    // Attempt to read data passed directly from the backend template rendering
    function readEmbeddedData() {
        console.log("Attempting to read embedded data...");
        try {
            const profileDataScript = document.getElementById('profile-data-script');
            const flagsScript = document.getElementById('profile-flags-script');

            if (profileDataScript && profileDataScript.textContent.trim() && profileDataScript.textContent.trim().toLowerCase() !== 'null') {
                profileData = JSON.parse(profileDataScript.textContent);
                console.log("Parsed profile data from script:", profileData);
            } else {
                console.warn("Embedded profile data script not found or empty/null.");
            }

            if (flagsScript && flagsScript.textContent.trim()) {
                 const flagsData = JSON.parse(flagsScript.textContent);
                 // Trust the backend flag if provided
                 isOwnProfile = flagsData?.is_own_profile ?? false; // Use nullish coalescing
                 console.log("Read isOwnProfile flag from script:", isOwnProfile);
                 return true; // Indicate flags were read
             } else {
                 console.warn("Embedded profile flags script not found or empty.");
                 // We'll determine isOwnProfile after fetching data if flags missing
                 return false; // Indicate flags were not read
             }

        } catch (e) {
            console.error("Error parsing embedded JSON data:", e);
            if (profileContainerMain) profileContainerMain.innerHTML = `<p class="error-message" style="color:red;">Error loading profile data. Please try refreshing.</p>`;
            // Hide all action buttons if parsing fails
             editProfileButton.style.display = 'none';
             networkLink.style.display = 'none';
            return false; // Indicate failure
        }
    }


    // --- Populate Profile UI ---
    function populateProfile(user) {
        if (!user) { /* ... (error handling as before) ... */ return; }
        if (!profileUsernameElement || !profileTitleElement) { /* ... (error handling) ... */ return; }

        console.log("Populating profile UI for user:", user.username);
        document.title = `${escapeHtml(user.username) || 'User'}'s Profile - UniVerse`;
        profileUsernameElement.textContent = escapeHtml(user.username) || '--';

        // Construct Title
        const profession = escapeHtml(user.profession);
        const company = escapeHtml(user.current_company);
        const almaMater = escapeHtml(user.alma_mater);
        let titleText = profession || (user.is_alumni ? 'Alumni' : 'Student');
        if (company) { titleText += ` at ${company}`; }
        else if (almaMater && !profession) { titleText += ` from ${almaMater}`; }
        else if (!company && !almaMater && !profession) { titleText += ` at UniVerse`;}
        profileTitleElement.textContent = titleText;

        // Populate Stats safely
        if(profileActivityElement) profileActivityElement.textContent = user.activity_score ?? '0';
        if(profileAlmagemsElement) profileAlmagemsElement.textContent = user.alumni_gems ?? '0';
        if(profileBadgesElement) profileBadgesElement.textContent = user.badges ?? '0';
        if(profileSolvedElement) profileSolvedElement.textContent = user.solved ?? '0';
        if(profileLinksElement) profileLinksElement.textContent = user.links ?? '0';

        // Populate Professional Info safely
        if(profileProfessionElement) profileProfessionElement.textContent = escapeHtml(user.profession) || '--';
        if(profileCompanyElement) profileCompanyElement.textContent = escapeHtml(user.current_company) || '--';
        if(profileDepartmentElement) profileDepartmentElement.textContent = escapeHtml(user.department) || '--';
        if(profileAlmaMaterElement) profileAlmaMaterElement.textContent = escapeHtml(user.alma_mater) || '--';

        // Populate Multi-line Fields safely
        const multiLineFields = {
            'profile-interviews': user.interviews, 'profile-internships': user.internships,
            'profile-startups': user.startups, 'profile-milestones': user.milestones,
            'profile-advice': user.advice, 'profile-achievements': user.achievements
        };
        for (const id in multiLineFields) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = escapeHtml(multiLineFields[id]) || (id === 'profile-achievements' ? 'No achievements listed.' : 'Not shared yet.');
            }
        }

        // --- Control Buttons Visibility ---
        console.log("Setting button visibility based on final isOwnProfile:", isOwnProfile);

        // Edit Profile Button
        editProfileButton.style.display = isOwnProfile ? 'inline-flex' : 'none';

        // Network Link/Button (Always shown)
        networkLink.style.display = 'inline-flex';
        if (isOwnProfile) {
            networkButton.innerHTML = '<i class="fas fa-users"></i> My Network';
            networkLink.href = "/connection.html"; // Links to own connections
        } else {
            networkButton.innerHTML = '<i class="fas fa-user-friends"></i> View Network';
            // Link to the viewed user's connections page
            networkLink.href = `/connection.html?username=${encodeURIComponent(user.username)}`;
        }
    }

    // --- Edit Profile Popup Logic ---
    function showEditProfilePopup() {
        if (document.getElementById('edit-profile-popup')) return;
        if (!profileData) { alert("Cannot edit profile, data not loaded."); return; }
        const popupContainer = document.createElement('div');
        popupContainer.id = 'edit-profile-popup';
        popupContainer.innerHTML = `
            <h2>Edit Profile</h2>
            <div><label for="edit-profession">Profession:</label><input type="text" id="edit-profession" value="${escapeHtml(profileData.profession || '')}"></div>
            <div><label for="edit-company">Current Company:</label><input type="text" id="edit-company" value="${escapeHtml(profileData.current_company || '')}"></div>
            <div><label for="edit-department">Department:</label><input type="text" id="edit-department" value="${escapeHtml(profileData.department || '')}"></div>
            <div><label for="edit-alma-mater">Alma Mater:</label><input type="text" id="edit-alma-mater" value="${escapeHtml(profileData.alma_mater || '')}"></div>
            <div><label for="edit-achievements">Achievements:</label><textarea id="edit-achievements">${escapeHtml(profileData.achievements || '')}</textarea></div>
            <div><label for="edit-interviews">Interview Experiences:</label><textarea id="edit-interviews">${escapeHtml(profileData.interviews || '')}</textarea></div>
            <div><label for="edit-internships">Internship Experiences:</label><textarea id="edit-internships">${escapeHtml(profileData.internships || '')}</textarea></div>
            <div><label for="edit-startups">Startup Ventures:</label><textarea id="edit-startups">${escapeHtml(profileData.startups || '')}</textarea></div>
            <div><label for="edit-milestones">Milestones:</label><textarea id="edit-milestones">${escapeHtml(profileData.milestones || '')}</textarea></div>
            <div><label for="edit-advice">Advice:</label><textarea id="edit-advice">${escapeHtml(profileData.advice || '')}</textarea></div>
            <div class="popup-actions">
                <button type="button" class="cancel-button">Cancel</button>
                <button type="button" class="save-button">Save Changes</button>
            </div>`;

        popupContainer.querySelector('.save-button').addEventListener('click', () => {
            const updatedData = {
                profession: document.getElementById('edit-profession').value.trim() || null,
                current_company: document.getElementById('edit-company').value.trim() || null,
                department: document.getElementById('edit-department').value.trim() || null,
                alma_mater: document.getElementById('edit-alma-mater').value.trim() || null,
                achievements: document.getElementById('edit-achievements').value.trim() || null,
                interviews: document.getElementById('edit-interviews').value.trim() || null,
                internships: document.getElementById('edit-internships').value.trim() || null,
                startups: document.getElementById('edit-startups').value.trim() || null,
                milestones: document.getElementById('edit-milestones').value.trim() || null,
                advice: document.getElementById('edit-advice').value.trim() || null,
            };
            saveProfileChanges(updatedData);
            if(document.body.contains(popupContainer)) document.body.removeChild(popupContainer);
        });
        popupContainer.querySelector('.cancel-button').addEventListener('click', () => {
            if(document.body.contains(popupContainer)) document.body.removeChild(popupContainer);
        });
        document.body.appendChild(popupContainer);
    }

    // --- Save Profile Changes ---
    async function saveProfileChanges(updatedData) {
        console.log("Saving profile changes via API:", updatedData);
        const saveButton = document.querySelector('#edit-profile-popup .save-button'); // Reference if needed for disabling
        if(saveButton) saveButton.disabled = true;

        try {
            const response = await fetch(`/api/users/me`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(updatedData)
            });
             const responseData = await response.json(); // Try parse always
            if (!response.ok) {
                if (response.status === 401 || response.status === 307) { window.location.href = '/login.html'; return; }
                throw new Error(responseData.detail || `Update failed: ${response.statusText}`);
            }
            alert('Profile updated successfully!');
            profileData = responseData; // Update local cache with response from backend
            populateProfile(profileData); // Refresh UI
        } catch (error) {
            console.error('Error updating profile:', error);
            alert(`Failed to update profile: ${error.message}`);
            if(saveButton) saveButton.disabled = false; // Re-enable only on error
        }
        // No need to re-enable button on success as popup closes
    }

     // --- Event Listeners ---
     if (editProfileButton) {
         editProfileButton.addEventListener('click', showEditProfilePopup);
     }


    // --- Initialize ---
    async function initializeProfilePage() {
        currentUserData = await updateNavbar(); // Fetch logged-in user data & update nav
        const flagsRead = readEmbeddedData(); // Try reading data embedded by backend

        if (profileData) {
            // Data was embedded, isOwnProfile was potentially set by backend flag
             if (!flagsRead && currentUserData) {
                 // Fallback: Determine isOwnProfile if flags weren't read but we have current user
                 isOwnProfile = (currentUserData.username === profileData.username);
                 console.log("Determined isOwnProfile after fetch:", isOwnProfile);
             }
            populateProfile(profileData);
        } else {
            // Data not embedded, try fetching based on URL parameter
            const params = new URLSearchParams(window.location.search);
            const usernameFromUrl = params.get('username');

            if (!usernameFromUrl && currentUserData) { // No username in URL, viewing own profile
                 profileData = currentUserData;
                 isOwnProfile = true;
                 console.log("Using logged-in user data for profile display.");
                 populateProfile(profileData);
            } else if (usernameFromUrl) { // Username in URL, fetch that profile
                 console.log(`Fetching profile data for: ${usernameFromUrl} via public API...`);
                 try {
                     const response = await fetch(`/api/public/users/${encodeURIComponent(usernameFromUrl)}`);
                     if (!response.ok) { throw new Error(`User '${usernameFromUrl}' not found or API error: ${response.status}`); }
                     profileData = await response.json();
                     isOwnProfile = (currentUserData && currentUserData.username === profileData.username); // Determine after fetch
                     console.log(`Fetched profile for ${usernameFromUrl}. Is own profile: ${isOwnProfile}`);
                     populateProfile(profileData);
                 } catch (error) {
                     console.error("Error fetching profile from URL:", error);
                     if (profileContainerMain) profileContainerMain.innerHTML = `<p class="error-message" style="color:red;">Could not load profile: ${escapeHtml(error.message)}</p>`;
                     if(editProfileButton) editProfileButton.style.display = 'none';
                     if(networkLink) networkLink.style.display = 'none';
                 }
            } else { // No URL param AND not logged in
                 if (profileContainerMain) profileContainerMain.innerHTML = `<p class="error-message" style="color:red; text-align:center;">Please log in or specify a user.</p>`;
                 if(editProfileButton) editProfileButton.style.display = 'none';
                 if(networkLink) networkLink.style.display = 'none';
            }
        }
    }

    initializeProfilePage(); // Start the process

}); // End DOMContentLoaded