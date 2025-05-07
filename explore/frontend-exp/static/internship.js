// --- Utility: Simple HTML Escaping ---
function escapeHtml(unsafe) {
    // Handles null/undefined/non-strings gracefully and performs correct escaping
    if (typeof unsafe !== 'string') { return unsafe === null || unsafe === undefined ? '' : unsafe; }
    return unsafe
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
}

// --- Internship Page Logic ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("Internship Page DOM Loaded.");

    // --- Element References ---
    const internshipsListContainer = document.getElementById("internships-list");
    const addInternshipButton = document.getElementById('add-internship-button');
    const addInternshipSection = document.getElementById('add-internship'); // The form section
    const internshipForm = document.getElementById('internship-form'); // The <form> element
    const submitNewInternshipButton = document.getElementById('submit-new-internship');
    const cancelAddInternshipButton = addInternshipSection?.querySelector('.cancel-button'); // Find cancel within section

    // Popup Elements
    const popup = document.getElementById('popup-details');
    const overlay = document.getElementById('overlay');
    const popupCloseBtn = document.getElementById('popup-close-btn');
    const popupTitle = document.getElementById('popup-title');
    const popupCompany = document.getElementById('popup-company');
    const popupRole = document.getElementById('popup-role'); // Assuming title maps to role here
    const popupStartDate = document.getElementById('popup-start-date');
    const popupEndDate = document.getElementById('popup-end-date');
    const popupDescriptionText = document.getElementById('popup-description-text');
    const popupLink = document.getElementById('popup-link');


    // --- Check if essential elements exist ---
    if (!internshipsListContainer || !addInternshipButton || !addInternshipSection || !internshipForm || !submitNewInternshipButton || !cancelAddInternshipButton || !popup || !overlay || !popupCloseBtn) {
        console.error("Essential page elements are missing! Cannot initialize internship page correctly.");
        // Display a user-friendly error on the page if possible
        if(internshipsListContainer) internshipsListContainer.innerHTML = '<p class="error-message">Page setup error. Please contact support.</p>';
        return; // Stop execution if critical elements are missing
    }

    // --- Fetch and Display Internships ---
    async function loadInternships() {
        console.log("Attempting to load internships from /api/internships...");
        internshipsListContainer.innerHTML = '<p class="loading">Loading internships...</p>';
        try {
            // Fetch the *verified* internships list
            const response = await fetch("/api/internships?upcoming_only=true"); // Fetch upcoming by default
            console.log("API Response Status:", response.status);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to fetch internships: ${response.status} ${errorText}`);
            }
            const internships = await response.json();
            console.log("Received Internships Data:", internships);

            internshipsListContainer.innerHTML = ""; // Clear loading/previous

            if (!Array.isArray(internships)) {
                 console.error("ERROR: Received data is not an array!", internships);
                 throw new Error("Received invalid data format from server.");
            }

            if (internships.length === 0) {
                console.log("No upcoming internships found.");
                internshipsListContainer.innerHTML = '<p class="no-data">No upcoming internship postings found currently.</p>';
                return;
            }

            // Sort by start date (earliest first), handling nulls (push nulls to end)
            internships.sort((a, b) => {
                const dateA = a.start_date ? new Date(a.start_date) : null;
                const dateB = b.start_date ? new Date(b.start_date) : null;
                if (dateA === null && dateB === null) return 0;
                if (dateA === null) return 1; // Nulls go last
                if (dateB === null) return -1; // Nulls go last
                return dateA - dateB; // Sort actual dates
            });

            internships.forEach((internship, index) => {
                // console.log(`Processing internship ${index}:`, internship); // Verbose log
                if (!internship || typeof internship !== 'object' || !internship.id) {
                    console.warn(`Skipping invalid item at index ${index}:`, internship);
                    return; // Skip null, non-object, or items missing ID
                }

                const item = document.createElement("div");
                item.classList.add("internship-item");

                const title = escapeHtml(internship.title) || 'No Title Provided';
                const company = escapeHtml(internship.company) || 'Company Not Specified';
                const startDate = internship.start_date ? new Date(internship.start_date + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', year: 'numeric' }) : 'ASAP';
                const endDate = internship.end_date ? new Date(internship.end_date + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', year: 'numeric' }) : 'Ongoing';
                const url = escapeHtml(internship.url); // Key is 'url'

                item.innerHTML = `
                    <h3>${title}</h3>
                    <p><strong>Company:</strong> ${company}</p>
                    <p class="dates"><strong>Dates:</strong> ${startDate} - ${endDate}</p>
                    ${url ? `<a href="${url}" target="_blank" rel="noopener noreferrer" class="view-posting-link" onclick="event.stopPropagation()">View Posting</a>` : ''}
                `;
                // Add listener to show popup with FULL details
                item.addEventListener('click', () => showPopup(internship)); // Pass the whole object
                internshipsListContainer.appendChild(item);
            });
            console.log("Finished rendering internships.");

        } catch (error) {
            console.error("Error in loadInternships:", error);
            internshipsListContainer.innerHTML = `<p class="error-message">Error loading internships: ${error.message}. Please try refreshing.</p>`;
        }
    }

    // --- Popup Logic ---
    function showPopup(internshipData) {
        if (!popup || !overlay || !internshipData) {
            console.error("Cannot show popup - elements or data missing");
            return;
        }

        console.log("Showing popup for:", internshipData);

        popupTitle.textContent = escapeHtml(internshipData.title || 'Internship Details');
        popupCompany.textContent = escapeHtml(internshipData.company || 'N/A');
        // Populate Role using title as well, assuming they are similar
        popupRole.textContent = escapeHtml(internshipData.title || 'N/A');
        popupStartDate.textContent = internshipData.start_date ? new Date(internshipData.start_date + 'T00:00:00').toLocaleDateString() : 'Not Specified';
        popupEndDate.textContent = internshipData.end_date ? new Date(internshipData.end_date + 'T00:00:00').toLocaleDateString() : 'Ongoing or Not Specified';
        popupDescriptionText.textContent = escapeHtml(internshipData.description || 'No description provided.');

        if (internshipData.url) {
            popupLink.href = escapeHtml(internshipData.url); // Use correct 'url' key
            popupLink.style.display = 'block'; // Show link if present
        } else {
            popupLink.href = '#'; // Reset href
            popupLink.style.display = 'none'; // Hide link if not present
        }

        popup.style.display = 'block';
        overlay.style.display = 'block';
    }

    function closePopup() {
         if (popup) popup.style.display = 'none';
         if (overlay) overlay.style.display = 'none';
    }

    // Add event listeners for closing the popup
    popupCloseBtn.addEventListener('click', closePopup);
    overlay.addEventListener('click', closePopup);


    // --- Add Internship Form Logic ---
    addInternshipButton.addEventListener('click', () => {
        // Toggle visibility
        addInternshipSection.style.display = addInternshipSection.style.display === 'none' ? 'block' : 'none';
        // Scroll to the form if opening it (optional)
        if (addInternshipSection.style.display === 'block') {
            addInternshipSection.scrollIntoView({ behavior: 'smooth' });
        }
    });

    cancelAddInternshipButton.addEventListener('click', () => {
         addInternshipSection.style.display = 'none';
         internshipForm.reset(); // Clear the form on cancel
    });

    submitNewInternshipButton.addEventListener('click', async () => {
        // Get values from form
        const title = document.getElementById('new-title').value.trim();
        const company = document.getElementById('new-company').value.trim();
        const startDate = document.getElementById('new-start-date').value; // Keep as string YYYY-MM-DD
        const endDate = document.getElementById('new-end-date').value; // Keep as string YYYY-MM-DD
        const description = document.getElementById('new-description').value.trim();
        const url = document.getElementById('new-url').value.trim();

        // Client-side validation
        if (!title || !company || !url ) {
            alert('Please fill in required fields: Title, Company, and Application Link.');
            return;
        }
        // Optional: Validate URL format roughly
        try {
            new URL(url); // Check if it parses as a URL
        } catch (_) {
            alert('Please enter a valid Application Link/URL (e.g., https://...)');
            return;
        }


        const newInternshipData = { // Matches InternshipCreate Pydantic model
            title: title,
            company: company,
            start_date: startDate || null, // Send null if empty
            end_date: endDate || null,     // Send null if empty
            description: description || null,
            url: url // Backend expects 'url'
        };

        console.log("Submitting new internship suggestion:", newInternshipData);

        submitNewInternshipButton.disabled = true;
        submitNewInternshipButton.textContent = 'Submitting...';

        try {
            // POST to the correct endpoint - this saves to `unverified_internships`
            // Requires user to be logged in (cookie auth).
            const response = await fetch('/api/internships', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // Cookie is sent automatically by browser
                body: JSON.stringify(newInternshipData),
            });

            const responseData = await response.json(); // Always try to parse response

            if (!response.ok) {
                // Use detail from backend error response if available
                throw new Error(responseData.detail || `Failed to submit: ${response.statusText}`);
            }

            console.log("Submission successful:", responseData);
            alert('Internship suggestion submitted for review. Thank you!');
            addInternshipSection.style.display = 'none'; // Hide form
            internshipForm.reset(); // Reset form fields

            // NOTE: Do NOT call loadInternships() here, as the submitted item
            // needs admin approval before appearing in the main list.

        } catch (error) {
            console.error('Error submitting new internship:', error);
            alert(`Error submitting internship: ${error.message}. Please try again.`);
        } finally {
             // Re-enable button regardless of success/failure
             submitNewInternshipButton.disabled = false;
             submitNewInternshipButton.textContent = 'Submit Suggestion';
        }
    });


    // --- Initial Load ---
    // updateNavbar(); // Removed as per request
    loadInternships(); // Load internships when the page is ready

}); // End DOMContentLoaded