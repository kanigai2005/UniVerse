// --- Utility: Simple HTML Escaping ---
function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) { return ''; }
    const str = String(unsafe);
    return str
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("Internship Page DOM Loaded.");

    const internshipsListContainer = document.getElementById("internships-list");
    const addInternshipButton = document.getElementById('add-internship-button');
    const addInternshipSection = document.getElementById('add-internship');
    const internshipForm = document.getElementById('internship-form');
    const submitNewInternshipButton = document.getElementById('submit-new-internship');
    const cancelAddInternshipButton = addInternshipSection?.querySelector('.cancel-button');

    const popup = document.getElementById('popup-details');
    const overlay = document.getElementById('overlay');
    const popupCloseBtn = document.getElementById('popup-close-btn');
    const popupTitle = document.getElementById('popup-title');
    const popupCompany = document.getElementById('popup-company');
    const popupRole = document.getElementById('popup-role');
    const popupStartDate = document.getElementById('popup-start-date');
    const popupEndDate = document.getElementById('popup-end-date');
    const popupDescriptionText = document.getElementById('popup-description-text');
    const popupLink = document.getElementById('popup-link');

    // Search and Toggle Elements
    const internshipSearchInput = document.getElementById('internship-search-input');
    const internshipSearchButton = document.getElementById('internship-search-button');
    const toggleInternshipsBtn = document.getElementById('toggle-internships-visibility-btn');

    // --- State Variables ---
    let allInternshipsData = []; // Full dataset from API
    const ITEMS_DISPLAY_LIMIT = 6; // Number of *items* to show initially (3 rows if 2 per row)
    let showAllInternships = false;
    let currentFilteredInternships = []; // Stores internships after search/filter

    if (!internshipsListContainer || !addInternshipButton || !addInternshipSection || !internshipForm ||
        !submitNewInternshipButton || !cancelAddInternshipButton || !popup || !overlay || !popupCloseBtn ||
        !internshipSearchInput || !internshipSearchButton || !toggleInternshipsBtn) {
        console.error("Essential page elements are missing! Cannot initialize internship page correctly.");
        if(internshipsListContainer) internshipsListContainer.innerHTML = '<li class="error-message">Page setup error. Please contact support.</li>';
        return;
    }

    async function fetchAndDisplayInternships() {
        internshipsListContainer.innerHTML = '<li class="loading">Loading internships...</li>';
        try {
            const response = await fetch("/api/internships?upcoming_only=true");
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to fetch internships: ${response.status} ${errorText}`);
            }
            allInternshipsData = await response.json();
            if (!Array.isArray(allInternshipsData)) {
                 throw new Error("Received invalid data format from server.");
            }
            showAllInternships = false; // Reset on new data fetch
            renderInternships(allInternshipsData); // Pass the full dataset to render
        } catch (error) {
            console.error("Error in fetchAndDisplayInternships:", error);
            internshipsListContainer.innerHTML = `<li class="error-message">Error loading internships: ${error.message}.</li>`;
            if (toggleInternshipsBtn) toggleInternshipsBtn.style.display = 'none';
        }
    }

    function renderInternships(internshipsToProcess) {
        currentFilteredInternships = internshipsToProcess; // Update the working list for "Show More" & search
        internshipsListContainer.innerHTML = "";

        const itemsToRender = showAllInternships ? currentFilteredInternships : currentFilteredInternships.slice(0, ITEMS_DISPLAY_LIMIT);

        if (itemsToRender.length === 0) {
            internshipsListContainer.innerHTML = '<li class="no-data">No internship postings found matching criteria.</li>';
            toggleInternshipsBtn.style.display = 'none';
            return;
        }

        // Sort by start date (earliest first), nulls last
        itemsToRender.sort((a, b) => {
            const dateA = a.start_date ? new Date(a.start_date) : null;
            const dateB = b.start_date ? new Date(b.start_date) : null;
            if (dateA === null && dateB === null) return 0;
            if (dateA === null) return 1;
            if (dateB === null) return -1;
            return dateA - dateB;
        });

        let currentRow = null;
        itemsToRender.forEach((internship, index) => {
            if (!internship || typeof internship !== 'object' || !internship.id) {
                console.warn(`Skipping invalid item at index ${index}:`, internship);
                return;
            }

            if (index % 2 === 0) { // Start a new row for every two items
                currentRow = document.createElement('li'); // Each row is an <li>
                currentRow.classList.add('internship-row');
                internshipsListContainer.appendChild(currentRow);
            }

            const card = document.createElement('div'); // Each item in a row is a <div> (card)
            card.classList.add('internship-card');

            const title = escapeHtml(internship.title) || 'No Title Provided';
            const company = escapeHtml(internship.company) || 'Company Not Specified';
            const startDate = internship.start_date ? new Date(internship.start_date + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', year: 'numeric' }) : 'ASAP';
            const endDate = internship.end_date ? new Date(internship.end_date + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', year: 'numeric' }) : 'Ongoing';
            const url = escapeHtml(internship.url);

            card.innerHTML = `
                <h3>${title}</h3>
                <p><strong>Company:</strong> ${company}</p>
                <p class="dates"><strong>Dates:</strong> ${startDate} - ${endDate}</p>
                ${url ? `<a href="${url}" target="_blank" rel="noopener noreferrer" class="view-posting-link" onclick="event.stopPropagation()">View Posting</a>` : ''}
            `;
            card.addEventListener('click', () => showPopup(internship));
            currentRow.appendChild(card);
        });

        // Handle "Show More/Less" button
        if (currentFilteredInternships.length > ITEMS_DISPLAY_LIMIT) {
            toggleInternshipsBtn.style.display = 'block';
            const remaining = currentFilteredInternships.length - ITEMS_DISPLAY_LIMIT;
            toggleInternshipsBtn.textContent = showAllInternships ? 'Show Less Internships' : `Show More Internships (${remaining} more)`;
        } else {
            toggleInternshipsBtn.style.display = 'none';
        }
    }


    function showPopup(internshipData) {
        if (!popup || !overlay || !internshipData) return;
        popupTitle.textContent = escapeHtml(internshipData.title || 'Internship Details');
        popupCompany.textContent = escapeHtml(internshipData.company || 'N/A');
        popupRole.textContent = escapeHtml(internshipData.title || 'N/A'); // Or use a specific role field if available
        popupStartDate.textContent = internshipData.start_date ? new Date(internshipData.start_date + 'T00:00:00').toLocaleDateString() : 'Not Specified';
        popupEndDate.textContent = internshipData.end_date ? new Date(internshipData.end_date + 'T00:00:00').toLocaleDateString() : 'Ongoing or Not Specified';
        popupDescriptionText.textContent = escapeHtml(internshipData.description || 'No description provided.');
        if (internshipData.url) {
            popupLink.href = escapeHtml(internshipData.url);
            popupLink.style.display = 'block';
        } else {
            popupLink.href = '#';
            popupLink.style.display = 'none';
        }
        popup.style.display = 'block';
        overlay.style.display = 'block';
    }

    function closePopup() {
         if (popup) popup.style.display = 'none';
         if (overlay) overlay.style.display = 'none';
    }
    popupCloseBtn.addEventListener('click', closePopup);
    overlay.addEventListener('click', closePopup);


    addInternshipButton.addEventListener('click', () => {
        addInternshipSection.style.display = addInternshipSection.style.display === 'none' ? 'block' : 'none';
        if (addInternshipSection.style.display === 'block') {
            addInternshipSection.scrollIntoView({ behavior: 'smooth' });
        }
    });

    cancelAddInternshipButton.addEventListener('click', () => {
         addInternshipSection.style.display = 'none';
         internshipForm.reset();
    });

    submitNewInternshipButton.addEventListener('click', async () => {
        const title = document.getElementById('new-title').value.trim();
        const company = document.getElementById('new-company').value.trim();
        const startDate = document.getElementById('new-start-date').value;
        const endDate = document.getElementById('new-end-date').value;
        const description = document.getElementById('new-description').value.trim();
        const url = document.getElementById('new-url').value.trim();

        if (!title || !company || !url ) {
            alert('Please fill in required fields: Title, Company, and Application Link.');
            return;
        }
        try { new URL(url); } catch (_) {
            alert('Please enter a valid Application Link/URL (e.g., https://...)');
            return;
        }

        const newInternshipData = { title, company, start_date: startDate || null, end_date: endDate || null, description: description || null, url };
        submitNewInternshipButton.disabled = true;
        submitNewInternshipButton.textContent = 'Submitting...';
        try {
            const response = await fetch('/api/internships', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newInternshipData),
            });
            const responseData = await response.json();
            if (!response.ok) throw new Error(responseData.detail || `Failed to submit: ${response.statusText}`);
            alert('Internship suggestion submitted for review. Thank you!');
            addInternshipSection.style.display = 'none';
            internshipForm.reset();
        } catch (error) {
            alert(`Error submitting internship: ${error.message}. Please try again.`);
        } finally {
             submitNewInternshipButton.disabled = false;
             submitNewInternshipButton.textContent = 'Submit Suggestion';
        }
    });

    // --- Search Logic ---
    function performSearch() {
        const searchTerm = internshipSearchInput.value.toLowerCase().trim();
        const filteredInternships = allInternshipsData.filter(internship => {
            if (!internship) return false;
            const searchableText = `
                ${internship.title || ''}
                ${internship.company || ''}
                ${internship.description || ''}
            `.toLowerCase();
            return searchableText.includes(searchTerm);
        });
        showAllInternships = false; // Reset "Show More" for new search results
        renderInternships(filteredInternships);
    }

    internshipSearchButton.addEventListener('click', performSearch);
    let searchDebounceTimer;
    internshipSearchInput.addEventListener('input', () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(performSearch, 300); // 300ms debounce
    });
    internshipSearchInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent form submission if search is inside a form
            performSearch();
        }
    });

    // --- Toggle Visibility Logic ---
    toggleInternshipsBtn.addEventListener('click', () => {
        showAllInternships = !showAllInternships;
        renderInternships(currentFilteredInternships); // Re-render with the current filter and new showAll state
    });

    fetchAndDisplayInternships();
});