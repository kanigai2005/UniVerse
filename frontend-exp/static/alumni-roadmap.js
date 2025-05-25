// --- Utility: Simple HTML Escaping ---
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') { return unsafe === null || unsafe === undefined ? '' : unsafe; }
    return unsafe
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
}

// --- Profile Page Logic ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("Alumni Roadmaps DOM Loaded");
    // --- Element References ---
    const searchInput = document.getElementById('searchInput');
    const resetButton = document.getElementById('resetButton');
    const roadmapModal = document.getElementById('roadmap-modal');
    const closeButton = document.querySelector('#roadmap-modal .close-button');
    const roadmapsContainer = document.getElementById("roadmaps-dynamic-container");
    const modalName = document.getElementById('modal-name');
    const modalProfession = document.getElementById('modal-profession');
    const modalAlmaMater = document.getElementById('modal-almaMater');
    const modalInterviews = document.getElementById('modal-interviews');
    const modalInternships = document.getElementById('modal-internships');
    const modalStartups = document.getElementById('modal-startups');
    const modalCurrentCompany = document.getElementById('modal-currentCompany');
    const modalMilestones = document.getElementById('modal-milestones');
    const modalAdvice = document.getElementById('modal-advice');

    // --- State ---
    let allAlumniList = [];
    let currentFilteredAndGroupedData = {};
    let myLikedAlumniIds = new Set();

    // --- Event Listeners ---
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            console.log("Reset button clicked.");
            // Apply filter with empty term (shows all)
            filterAndGroupAlumni('');
        });
    } else { console.error("Reset button not found"); }

    if (closeButton) { closeButton.addEventListener('click', closeModal); }
    else { console.error("Modal close button not found"); }

    if (roadmapModal) {
        roadmapModal.addEventListener('click', (event) => {
            if (event.target === roadmapModal) { closeModal(); }
        });
    } else { console.error("Roadmap modal container not found"); }

    if (searchInput) {
        // Use 'input' for immediate feedback as user types
        searchInput.addEventListener('input', function () {
            // Debounce slightly to avoid filtering on every single keystroke (optional but good practice)
            // Simple debounce implementation:
            clearTimeout(searchInput.debounceTimer);
            searchInput.debounceTimer = setTimeout(() => {
                 filterAndGroupAlumni(this.value);
            }, 250); // Adjust delay as needed (e.g., 250-500ms)
        });
    } else { console.error("Search input not found"); }


    // --- Core Functions ---

    async function fetchAllAlumni() {
        console.log("Fetching ALL alumni data for Roadmaps...");
        if (!roadmapsContainer) return [];
        try {
            const response = await fetch("/api/alumni");
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error ${response.status}: ${errorText}`);
            }
            const data = await response.json();
            if (!Array.isArray(data)) throw new Error("Invalid data format received.");
            console.log(`Fetched ${data.length} total alumni.`);
            return data;
        } catch (error) {
            console.error("Error fetching all alumni:", error);
            if(roadmapsContainer) roadmapsContainer.innerHTML = `<p style="color: var(--error-color); text-align: center;">Failed to load alumni roadmaps: ${error.message}. Please try again later.</p>`;
            return [];
        }
    }

    async function fetchMyLikedAlumni() {
        console.log("Fetching liked alumni IDs...");
        try {
            const response = await fetch("/api/alumni/me/liked");
            if (!response.ok) { console.warn(`Failed to fetch liked IDs: ${response.status}`); return new Set(); }
            const likedIdsArray = await response.json();
            if (!Array.isArray(likedIdsArray)) { console.warn("Invalid format for liked IDs."); return new Set(); }
            console.log("Fetched liked alumni IDs:", likedIdsArray);
            myLikedAlumniIds = new Set(likedIdsArray);
        } catch (error) { console.error("Error fetching liked alumni IDs:", error); myLikedAlumniIds = new Set(); }
    }

    async function fetchAlumniDetails(alumniId) {
        console.log(`Fetching details for alumni ID: ${alumniId}`);
        try {
            const response = await fetch(`/api/alumni/${alumniId}`);
            if (!response.ok) {
                 const errorText = await response.text();
                 console.error(`HTTP error fetching details! status: ${response.status}`, errorText);
                 alert(`Could not load details. Server returned status ${response.status}.`);
                 return null;
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error("Error fetching alumni details:", error);
            alert(`Could not load alumni details: ${error.message}`);
            return null;
        }
    }

    function groupAlumniByDepartment(alumniList) {
        const grouped = {};
        if (!Array.isArray(alumniList)) { console.error("Cannot group non-array:", alumniList); return {}; }
        alumniList.forEach(alumni => {
            if (!alumni || typeof alumni !== 'object') { console.warn("Skipping invalid alumni object:", alumni); return; }
            const dept = alumni.department || "Other";
            if (!grouped[dept]) grouped[dept] = [];
            grouped[dept].push(alumni);
        });
        return grouped; // Return grouped data
    }

    function createRoadmapCard(alumni) {
        if (!alumni || !alumni.id || !alumni.username) { console.warn("Invalid alumni data for card:", alumni); return null; } // Return null if data invalid

        const card = document.createElement('div');
        card.classList.add('roadmap-card');
        const usernameStr = String(alumni.username || '');
        const initials = usernameStr.substring(0, 2).toUpperCase();
        const isLiked = myLikedAlumniIds.has(alumni.id);
        const likedClass = isLiked ? 'liked' : '';
        const buttonTitle = isLiked ? `You liked ${escapeHtml(alumni.username)}` : `Like ${escapeHtml(alumni.username)}`;
        // Determine if button should be disabled from the start
        const buttonDisabled = isLiked ? 'disabled' : '';

        card.innerHTML = `
            <div class="avatar">${initials}</div>
            <div class="name">${escapeHtml(alumni.username)}</div>
            <div class="profession">${escapeHtml(alumni.profession || 'N/A')}</div>
            <div class="card-footer">
                 <button class="like-button ${likedClass}" data-alumni-id="${alumni.id}" title="${buttonTitle}" ${buttonDisabled}>
                    <span class="like-icon">${isLiked ? '❤️' : '👍'}</span> 
                    <span class="likes-count" id="likes-count-${alumni.id}">${alumni.likes ?? 0}</span>
                 </button>
            </div>
        `;
        card.addEventListener('click', (event) => {
            if (!event.target.closest('.like-button')) { openRoadmapModal(alumni.id); }
        });
        const likeButton = card.querySelector('.like-button');
        if (likeButton) {
            likeButton.addEventListener('click', (event) => {
                event.stopPropagation();
                // Check disabled attribute instead of class for click prevention
                if (!likeButton.disabled) {
                     likeAlumni(alumni.id, likeButton);
                } else {
                    console.log(`Like button for ${alumni.id} is disabled (already liked).`);
                }
            });
        }
        return card;
    }

    function populateRoadmaps(groupedAlumni) {
        console.log("Populating roadmaps...");
        if (!roadmapsContainer) { console.error("Roadmaps container not found!"); return; }
        roadmapsContainer.innerHTML = ""; // Clear previous

        if (!groupedAlumni || Object.keys(groupedAlumni).length === 0) {
             roadmapsContainer.innerHTML = "<p>No alumni roadmaps found matching criteria.</p>";
             console.log("No grouped alumni data to display.");
             return;
        }

        const sortedDepartments = Object.keys(groupedAlumni).sort();
        console.log("Departments to render:", sortedDepartments);

        for (const department of sortedDepartments) {
            const alumniList = groupedAlumni[department];
            if (Array.isArray(alumniList) && alumniList.length > 0) {
                 // *** Sort alumni within this department by likes ***
                 console.log(`Sorting ${alumniList.length} alumni in department: ${department}`);
                 alumniList.sort((a, b) => (b.likes ?? 0) - (a.likes ?? 0)); // Descending likes
                 console.log(`Likes after sort (first 5):`, alumniList.slice(0, 5).map(a => a.likes));


                 const section = document.createElement('section');
                 section.classList.add('roadmap-section');
                 const departmentClass = department.toLowerCase().replace(/[^a-z0-9-_]+/g, '-').replace(/-$/, '');
                 section.innerHTML = `
                     <h3 class="section-heading">${escapeHtml(department)} Roadmaps</h3>
                     <div class="roadmap-list ${escapeHtml(departmentClass)}-roadmaps"></div>
                 `;
                 roadmapsContainer.appendChild(section);
                 const listContainer = section.querySelector(`.${escapeHtml(departmentClass)}-roadmaps`);
                 if (listContainer) {
                     alumniList.forEach(alumni => {
                         const card = createRoadmapCard(alumni);
                         if (card) listContainer.appendChild(card); // Append valid cards
                     });
                 } else { console.error(`Could not find list container for class: ${departmentClass}-roadmaps`); }
            } else {
                console.log(`Skipping empty or invalid alumni list for department: ${department}`);
            }
        }
        console.log("Roadmaps population complete.");
    }

    async function initializePage() {
        await fetchMyLikedAlumni(); // Fetch liked status FIRST
        allAlumniList = await fetchAllAlumni(); // Then fetch all alumni
        if (allAlumniList.length > 0) {
            currentFilteredAndGroupedData = groupAlumniByDepartment(allAlumniList);
            populateRoadmaps(currentFilteredAndGroupedData); // Initial render (will be sorted by likes)
        }
    }

    async function openRoadmapModal(alumniId) {
        const alumniData = await fetchAlumniDetails(alumniId);
        if (!alumniData || !roadmapModal || !modalName) { return; }
        // ... (rest of modal population logic is likely okay) ...
        modalName.textContent = escapeHtml(alumniData.username || 'N/A');
        modalProfession.textContent = escapeHtml(alumniData.profession || 'N/A');
        modalAlmaMater.textContent = `Alma Mater: ${escapeHtml(alumniData.alma_mater || 'N/A')}`;
        modalCurrentCompany.textContent = `Current Company: ${escapeHtml(alumniData.current_company || 'N/A')}`;
        modalInterviews.innerHTML = `<strong>Interview Experiences:</strong><br>${escapeHtml(alumniData.interviews || 'Not shared').replace(/\n/g, '<br>')}`;
        modalInternships.innerHTML = `<strong>Internship Experiences:</strong><br>${escapeHtml(alumniData.internships || 'Not shared').replace(/\n/g, '<br>')}`;
        modalStartups.innerHTML = `<strong>Startup Ventures:</strong><br>${escapeHtml(alumniData.startups || 'Not shared').replace(/\n/g, '<br>')}`;
        modalMilestones.innerHTML = `<strong>Milestones:</strong><br>${escapeHtml(alumniData.milestones || 'Not shared').replace(/\n/g, '<br>')}`;
        modalAdvice.innerHTML = `<strong>Advice:</strong><br>${escapeHtml(alumniData.advice || 'Not shared').replace(/\n/g, '<br>')}`;
        roadmapModal.style.display = 'flex';
    }

    function closeModal() {
         if (roadmapModal) roadmapModal.style.display = 'none';
    }

    async function likeAlumni(alumniId, buttonElement) {
        console.log(`Attempting to like alumni ID: ${alumniId}`);
        if (!buttonElement) return;
        buttonElement.disabled = true; // Disable button during request

        try {
            const response = await fetch(`/api/alumni/${alumniId}/like`, { method: 'POST' });
            const resultData = await response.json(); // Try to parse JSON regardless of status for error detail

            if (!response.ok) {
                 let errorMsg = `Like failed: ${resultData.detail || `Status ${response.status}`}`;
                 if (response.status === 401 || response.status === 307) errorMsg = "Session expired. Please log in again to like.";
                 // Handle case where backend says "Already liked" (though button should be disabled)
                 if (response.status === 200 && resultData.message === "Already liked.") {
                      console.warn(`Like request sent for already liked user ${alumniId}, backend confirmed.`);
                      // Ensure button state is correct and exit
                      buttonElement.classList.add('liked');
                      const iconSpan = buttonElement.querySelector('.like-icon'); if (iconSpan) iconSpan.textContent = '❤️';
                      buttonElement.disabled = true; // Keep it disabled
                      return; // No further state update needed
                 }
                 throw new Error(errorMsg);
            }

            console.log("Like API call successful:", resultData);

            // --- Update UI and State ---
            const likesElement = buttonElement.querySelector('.likes-count');
            if (likesElement) likesElement.textContent = `${resultData.likes}`;

            // Visually update the button to 'liked' state
            buttonElement.classList.add('liked');
            const iconSpan = buttonElement.querySelector('.like-icon'); if (iconSpan) iconSpan.textContent = '❤️';
            buttonElement.disabled = true; // Keep button disabled after successful like
            buttonElement.title = `You liked this alumni`;

            // Update the global liked set
            myLikedAlumniIds.add(alumniId);

            // Update master list data
            const indexInAll = allAlumniList.findIndex(a => a && a.id === alumniId);
            if (indexInAll > -1) allAlumniList[indexInAll].likes = resultData.likes;

            // Update currently displayed grouped data
            for (const dept in currentFilteredAndGroupedData) {
                 if (Array.isArray(currentFilteredAndGroupedData[dept])) {
                      const indexInGroup = currentFilteredAndGroupedData[dept].findIndex(a => a && a.id === alumniId);
                      if (indexInGroup > -1) { currentFilteredAndGroupedData[dept][indexInGroup].likes = resultData.likes; break; }
                 }
            }

            // Re-render the list to apply sorting based on the new like count
            // Use the current search term to maintain filtering state
            console.log("Re-rendering list after like...");
            filterAndGroupAlumni(searchInput ? searchInput.value : '');

        } catch (error) {
            console.error("Error liking alumni:", error);
            alert(`Failed to record like: ${error.message}`);
            // Re-enable button only on error
            buttonElement.disabled = false;
        }
    }

    // Filters master list, then groups and renders (including sorting)
    function filterAndGroupAlumni(searchTerm) {
        const lowerSearchTerm = (searchTerm || '').toLowerCase().trim();
        let filteredList;
        console.log(`Filtering alumni with term: "${lowerSearchTerm}"`); // Log search term

        if (!lowerSearchTerm) {
             filteredList = allAlumniList; // Use full list if search is empty
        } else {
             filteredList = allAlumniList.filter(alumni => {
                // Robustly check properties before searching
                const username = (alumni?.username || '').toLowerCase();
                const profession = (alumni?.profession || '').toLowerCase();
                const department = (alumni?.department || '').toLowerCase();
                const company = (alumni?.current_company || '').toLowerCase();
                const searchStr = `${username} ${profession} ${department} ${company}`;
                return searchStr.includes(lowerSearchTerm);
            });
        }
        console.log(`Found ${filteredList.length} alumni after filtering.`);
        // Group the *filtered* results
        currentFilteredAndGroupedData = groupAlumniByDepartment(filteredList);
        // Re-render the roadmaps section - populateRoadmaps will sort the groups internally
        populateRoadmaps(currentFilteredAndGroupedData);
    }

    // --- Initial Load ---
    initializePage(); // Fetch liked status, then all alumni, group, sort, and display

}); // End DOMContentLoaded