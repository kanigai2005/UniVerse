document.addEventListener('DOMContentLoaded', () => {
    // --- Element References ---
    const searchInput = document.getElementById('searchInput');
    const resetButton = document.getElementById('resetButton');
    const roadmapModal = document.getElementById('roadmap-modal');
    const closeButton = document.querySelector('#roadmap-modal .close-button'); // More specific selector
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
    let allAlumniData = {}; // Store the structured data fetched initially

    // --- Initial Load ---
    loadTopLikedAlumni();

    // --- Event Listeners ---
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            searchInput.value = '';
            // Re-render using the originally fetched full data
            populateRoadmaps(allAlumniData);
        });
    } else {
        console.error("Reset button not found");
    }

    if (closeButton) {
        closeButton.addEventListener('click', () => {
            closeModal();
        });
    } else {
        console.error("Modal close button not found");
    }

    // Close modal if clicking outside the content area
    if (roadmapModal) {
        roadmapModal.addEventListener('click', (event) => {
            // Check if the click is directly on the modal background, not its children
            if (event.target === roadmapModal) {
                closeModal();
            }
        });
    } else {
        console.error("Roadmap modal container not found");
    }


    if (searchInput) {
        searchInput.addEventListener('input', function () {
            filterAlumni(this.value);
        });
    } else {
        console.error("Search input not found");
    }


    // --- Core Functions ---

    async function fetchTopLikedAlumni() {
        console.log("Fetching top liked alumni...");
        try {
            // Use the correct API endpoint defined in exp.py
            const response = await fetch("/api/alumni/top-liked");
            if (!response.ok) {
                console.error(`HTTP error! status: ${response.status}`, await response.text());
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log("Fetched top liked alumni data:", data);
            return data;
        } catch (error) {
            console.error("Error fetching top liked alumni:", error);
            if (roadmapsContainer) {
                 roadmapsContainer.innerHTML = "<p class='error-message'>Failed to load alumni roadmaps. Please try again later.</p>";
            }
            return {}; // Return empty object on failure
        }
    }

    async function fetchAlumniDetails(alumniId) {
        console.log(`Fetching details for alumni ID: ${alumniId}`);
        // IMPORTANT: Assumes you created a '/api/alumni/{alumni_id}' GET endpoint in exp.py
        try {
            // *** Add Authentication headers if needed ***
            // const headers = getAuthHeaders(); // Implement getAuthHeaders() if using tokens/sessions
            // const response = await fetch(`/api/alumni/${alumniId}`, { headers });
            const response = await fetch(`/api/alumni/${alumniId}`); // No auth headers shown here

            if (!response.ok) {
                 console.error(`HTTP error fetching details! status: ${response.status}`, await response.text());
                 throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log("Fetched alumni details:", data);
            return data;
        } catch (error) {
            console.error("Error fetching alumni details:", error);
            alert("Could not load alumni details."); // User feedback
            return null;
        }
    }

    function createRoadmapCard(alumni) {
        const card = document.createElement('div');
        card.classList.add('roadmap-card');
        // Use username for initials and display name
        const initials = alumni.username.substring(0, 2).toUpperCase();
        card.innerHTML = `
            <div class="avatar">${initials}</div>
            <div class="name">${alumni.username}</div>
            <div class="profession">${alumni.profession || 'N/A'}</div>
            <div class="card-footer">
                 <button class="like-button" data-alumni-id="${alumni.id}">Like</button>
                 <span class="likes-count">Likes: ${alumni.likes}</span>
            </div>
        `;

        // Add click listener to the card itself (excluding the button)
        card.addEventListener('click', (event) => {
            if (!event.target.classList.contains('like-button')) {
                openRoadmapModal(alumni.id); // Use the ID to fetch details
            }
        });

        // Add click listener specifically to the like button
        const likeButton = card.querySelector('.like-button');
        if (likeButton) {
            likeButton.addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent card click event from firing
                likeAlumni(alumni.id, likeButton); // Pass button for potential UI update
            });
        }

        return card;
    }

    function populateRoadmaps(groupedAlumni) {
        if (!roadmapsContainer) {
            console.error("Roadmaps container element not found!");
            return;
        };
        roadmapsContainer.innerHTML = ""; // Clear previous content

        if (Object.keys(groupedAlumni).length === 0) {
             roadmapsContainer.innerHTML = "<p>No alumni roadmaps found.</p>";
             return;
        }

        // Sort departments alphabetically (optional)
        const sortedDepartments = Object.keys(groupedAlumni).sort();

        // for (const department in groupedAlumni) { // Original order
        for (const department of sortedDepartments) { // Sorted order
            const alumniList = groupedAlumni[department];
            if (alumniList.length > 0) { // Only create section if there are alumni
                 const section = document.createElement('section');
                 section.classList.add('roadmap-section');
                 // Create a safe class name from department
                 const departmentClass = department.toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/-$/, '');
                 section.innerHTML = `
                     <h3 class="section-heading">${department} Roadmaps</h3>
                     <div class="roadmap-list ${departmentClass}-roadmaps"></div>
                 `;
                 roadmapsContainer.appendChild(section);
                 const listContainer = section.querySelector(`.${departmentClass}-roadmaps`);
                 alumniList.forEach(alumni => {
                     listContainer.appendChild(createRoadmapCard(alumni));
                 });
            }
        }
    }

    async function loadTopLikedAlumni() {
        const data = await fetchTopLikedAlumni();
        allAlumniData = data; // Store the full data for filtering
        populateRoadmaps(data); // Initial population
    }

    async function openRoadmapModal(alumniId) {
        const alumniData = await fetchAlumniDetails(alumniId);
        if (!alumniData || !roadmapModal) return; // Exit if data fetch failed or modal doesn't exist

        // Populate modal - Use username, handle nulls gracefully
        modalName.textContent = alumniData.username || 'N/A';
        modalProfession.textContent = `Profession: ${alumniData.profession || 'N/A'}`;
        modalAlmaMater.textContent = `Alma Mater: ${alumniData.alma_mater || 'N/A'}`;
        modalInterviews.textContent = `Interviews: ${alumniData.interviews || 'N/A'}`;
        modalInternships.textContent = `Internships: ${alumniData.internships || 'N/A'}`;
        modalStartups.textContent = `Startups: ${alumniData.startups || 'N/A'}`;
        modalCurrentCompany.textContent = `Current Company: ${alumniData.current_company || 'N/A'}`;
        modalMilestones.textContent = `Milestones: ${alumniData.milestones || 'N/A'}`;
        modalAdvice.textContent = `Advice: ${alumniData.advice || 'N/A'}`;

        // Display the modal
        roadmapModal.style.display = 'block'; // Use 'block' or 'flex' depending on CSS
    }

    function closeModal() {
         if (roadmapModal) {
             roadmapModal.style.display = 'none';
         }
    }

    async function likeAlumni(alumniId, buttonElement) {
        console.log(`Liking alumni ID: ${alumniId}`);
        // IMPORTANT: Assumes you created a '/api/alumni/{alumni_id}/like' POST endpoint
        try {
            // *** Add Authentication headers if needed ***
            // const headers = getAuthHeaders();
            // const response = await fetch(`/api/alumni/${alumniId}/like`, { method: 'POST', headers });
            const response = await fetch(`/api/alumni/${alumniId}/like`, {
                method: 'POST', // Use POST for actions that change state
            });

            if (!response.ok) {
                console.error(`HTTP error liking alumni! status: ${response.status}`, await response.text());
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const updatedData = await response.json(); // Expecting { likes: new_count }
            console.log("Like successful, updated data:", updatedData);

            // Find the card containing the button that was clicked
            const card = buttonElement.closest('.roadmap-card');
            if (card) {
                 const likesElement = card.querySelector('.likes-count');
                 if (likesElement) {
                     likesElement.textContent = `Likes: ${updatedData.likes}`; // Update text content
                 } else {
                     console.warn("Could not find likes count element to update in card.");
                 }
            } else {
                 console.warn("Could not find parent card for the like button.");
            }
            // Optionally disable the button or change its appearance after liking
            // buttonElement.disabled = true;
            // buttonElement.textContent = 'Liked';

        } catch (error) {
            console.error("Error liking alumni:", error);
            alert("Failed to record like."); // User feedback
        }
    }


    function filterAlumni(searchTerm) {
        const lowerSearchTerm = searchTerm.toLowerCase().trim();
        const filteredData = {};

        if (!lowerSearchTerm) {
             // If search term is empty, show all original data
             populateRoadmaps(allAlumniData);
             return;
        }

        for (const department in allAlumniData) {
            const matchingAlumni = allAlumniData[department].filter(alumni => {
                // Search in username and profession
                const searchStr = `${alumni.username} ${alumni.profession || ''}`.toLowerCase();
                return searchStr.includes(lowerSearchTerm);
            });
            // Only include department if it has matching alumni
            if (matchingAlumni.length > 0) {
                 filteredData[department] = matchingAlumni;
            }
        }
        populateRoadmaps(filteredData); // Populate with filtered results
    }
});