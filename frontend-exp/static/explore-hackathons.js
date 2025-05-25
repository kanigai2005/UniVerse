 // --- Utility: Simple HTML Escaping ---
 function escapeHtml(unsafe) {
    // Handles null/undefined/non-strings gracefully and performs correct escaping
    if (typeof unsafe !== 'string') { return unsafe === null || unsafe === undefined ? '' : unsafe; }
    return unsafe
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "") // Escape quotes
         .replace(/'/g, "'"); // Escape single quotes
}

// --- Navbar Update Logic (Optional - keep if used on other pages referenced by navbar) ---
// If you are absolutely sure no dynamic navbar updates are needed on *this specific page*,
// you can remove this function and its call in Initial Load.
async function updateNavbar() {
    const navProfileLink = document.getElementById('nav-profile-link');
    if (!navProfileLink) { console.warn("Navbar profile link element not found."); return null; }
    try {
        const response = await fetch('/api/users/me'); // Assumes cookie auth
        if (!response.ok) { navProfileLink.href = "/login.html"; localStorage.removeItem('username'); return null; }
        const userData = await response.json();
        if (userData && userData.username) {
            navProfileLink.href = `/profile.html?username=${encodeURIComponent(userData.username)}`;
            localStorage.setItem('username', userData.username); return userData;
        } else { navProfileLink.href = "/login.html"; localStorage.removeItem('username'); return null; }
    } catch (error) { console.error("Navbar update error:", error); navProfileLink.href = "/login.html"; localStorage.removeItem('username'); return null; }
}

// --- Hackathon Page Logic ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("Explore Hackathons DOM Loaded.");
    // --- Element References ---
    const hackathonSearchInput = document.getElementById('hackathon-search-input');
    const hackathonSearchButton = document.getElementById('hackathon-search-button');
    const hackathonForm = document.getElementById('hackathon-form');
    const currentHackathonsList = document.getElementById('current-hackathons-list');
    const hackathonDetailsModal = document.getElementById('hackathon-details-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalTitle = hackathonDetailsModal?.querySelector('.modal-header h2'); // Use querySelector for safety
    const modalDate = document.getElementById('modal-date');
    const modalLocation = document.getElementById('modal-location');
    const modalTheme = document.getElementById('modal-theme');
    const modalPrize = document.getElementById('modal-prize');
    const modalDescription = document.getElementById('modal-description');
    const modalRegisterBtn = document.getElementById('modal-register-btn');

    // Check if essential elements exist
    if (!hackathonSearchInput || !hackathonSearchButton || !hackathonForm || !currentHackathonsList || !hackathonDetailsModal || !modalCloseBtn) {
         console.error("One or more essential elements for the Hackathon page are missing in the HTML!");
         if(currentHackathonsList) currentHackathonsList.innerHTML = '<p class="error-message">Page initialization failed. Required elements missing.</p>';
         return; // Stop if critical elements aren't found
    }


    let allHackathons = []; // Store all fetched hackathons for filtering

    // --- Fetch and Render Hackathons ---
    async function fetchAndRenderHackathons(searchTerm = '') {
        console.log("Fetching and rendering hackathons...");
        currentHackathonsList.innerHTML = '<p class="loading">Loading hackathons...</p>';
        try {
            // Fetch only upcoming verified hackathons for display
            const response = await fetch('/api/hackathons?upcoming_only=true'); // Fetches from *verified* table
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to fetch hackathons: ${response.status} - ${errorText}`);
            }
            allHackathons = await response.json();
            if (!Array.isArray(allHackathons)) throw new Error("Invalid data format received for hackathons.");

            console.log("Fetched hackathons:", allHackathons);
            renderHackathons(searchTerm); // Render (potentially filtered) list
        } catch (error) {
            console.error('Error fetching hackathons:', error);
            currentHackathonsList.innerHTML = `<p class="error-message">Failed to load hackathons: ${error.message}</p>`;
        }
    }

    function renderHackathons(filterTerm = '') {
         currentHackathonsList.innerHTML = ''; // Clear previous
         const lowerCaseFilter = filterTerm.toLowerCase().trim();

         const filteredHackathons = lowerCaseFilter
             ? allHackathons.filter(h => {
                   if (!h) return false; // Skip invalid entries
                   const searchableText = `
                       ${h.name || ''} ${h.location || ''} ${h.theme || ''} ${h.description || ''}
                   `.toLowerCase();
                   return searchableText.includes(lowerCaseFilter);
                })
             : allHackathons; // Show all if no filter

         if (filteredHackathons.length === 0) {
             currentHackathonsList.innerHTML = '<p class="no-data">No hackathons found matching your criteria.</p>';
             return;
         }

         // Sort by date (earliest first), nulls last
         filteredHackathons.sort((a, b) => {
                const dateA = a?.date ? new Date(a.date) : null;
                const dateB = b?.date ? new Date(b.date) : null;
                if (dateA === null && dateB === null) return 0;
                if (dateA === null) return 1;
                if (dateB === null) return -1;
                return dateA - dateB;
            });

         filteredHackathons.forEach(hackathon => {
             if (!hackathon || !hackathon.id) return; // Skip invalid items

             const card = document.createElement('div');
             card.classList.add('hackathon-card');

             const dateString = hackathon.date ? new Date(hackathon.date + 'T00:00:00').toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Date TBD';

             card.innerHTML = `
                 <div class="hackathon-name">${escapeHtml(hackathon.name)}</div>
                 ${hackathon.date ? `<div class="hackathon-date"><i class="fas fa-calendar-alt"></i> ${dateString}</div>` : ''}
                 ${hackathon.location ? `<div class="hackathon-location"><i class="fas fa-map-marker-alt"></i> ${escapeHtml(hackathon.location)}</div>` : ''}
                 ${hackathon.theme ? `<div class="hackathon-theme"><i class="fas fa-lightbulb"></i> Theme: ${escapeHtml(hackathon.theme)}</div>` : ''}
                 ${hackathon.prize_pool ? `<div class="hackathon-prize"><i class="fas fa-trophy"></i> Prize: ${escapeHtml(hackathon.prize_pool)}</div>` : ''}
                 <div class="hackathon-details-link">
                      <button class="view-details-btn">View Details</button> <!-- Changed text -->
                 </div>
             `;
             // Add click listener to the whole card
             card.addEventListener('click', (e) => {
                // Allow clicking details button without opening modal twice if propagation not stopped
                // Or better: check if target was button inside listener
                 showHackathonDetails(hackathon)
                });
             // Optional: Add separate listener to button if needed, stopping propagation
             const detailsButton = card.querySelector('.view-details-btn');
             if(detailsButton) {
                 detailsButton.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent card click listener
                    showHackathonDetails(hackathon);
                 });
             }

             currentHackathonsList.appendChild(card);
         });
     }


    // --- Show Hackathon Details Modal ---
    function showHackathonDetails(hackathon) {
        if (!hackathonDetailsModal || !hackathon || !modalTitle) return; // Check essential modal elements

        modalTitle.textContent = escapeHtml(hackathon.name);
        modalDate.textContent = hackathon.date ? new Date(hackathon.date + 'T00:00:00').toLocaleDateString() : 'Not Specified';
        modalLocation.textContent = escapeHtml(hackathon.location || 'Not Specified');
        modalTheme.textContent = escapeHtml(hackathon.theme || 'Not Specified');
        modalPrize.textContent = escapeHtml(hackathon.prize_pool || 'Not Specified');
        modalDescription.textContent = escapeHtml(hackathon.description || 'No description provided.');

        if (hackathon.url) {
             modalRegisterBtn.href = escapeHtml(hackathon.url);
             modalRegisterBtn.style.display = 'inline-block';
        } else {
             modalRegisterBtn.href = '#'; // Reset href
             modalRegisterBtn.style.display = 'none';
        }

        hackathonDetailsModal.style.display = 'flex'; // Use flex to show and help center
    }

    // --- Close Modal ---
     function closeModal() {
         if (hackathonDetailsModal) hackathonDetailsModal.style.display = 'none';
     }

     modalCloseBtn.addEventListener('click', closeModal);

     // Close modal if clicking the background overlay
     hackathonDetailsModal.addEventListener('click', (event) => {
         if (event.target === hackathonDetailsModal) {
             closeModal();
         }
     });

     // Close modal with Escape key
     window.addEventListener('keydown', (event) => {
         if (event.key === 'Escape' && hackathonDetailsModal.style.display === 'flex') {
             closeModal();
         }
     });


    // --- Handle Hackathon Submission ---
    hackathonForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const submitButton = this.querySelector('button[type="submit"]');
        if(!submitButton) return; // Should not happen

        submitButton.disabled = true;
        submitButton.textContent = 'Submitting...';

        // Gather data, matching backend Pydantic model (HackathonCreate)
        const hackathonData = {
            name: document.getElementById('hackathon-name')?.value.trim() || '', // Use optional chaining
            location: document.getElementById('hackathon-location')?.value.trim() || null,
            date: document.getElementById('hackathon-date')?.value || null, // Keep as YYYY-MM-DD string or null
            url: document.getElementById('hackathon-url')?.value.trim() || '', // URL is required here based on form
            description: document.getElementById('hackathon-description')?.value.trim() || null,
            theme: document.getElementById('hackathon-theme')?.value.trim() || null,
            prize_pool: document.getElementById('hackathon-prize_pool')?.value.trim() || null,
        };

        // Basic validation
        if (!hackathonData.name || !hackathonData.url) {
             alert("Hackathon Name and Registration/Info Link are required.");
             submitButton.disabled = false;
             submitButton.textContent = 'Submit Suggestion';
             return;
        }
        // Optional URL validation
        try { new URL(hackathonData.url); } catch (_) {
             alert("Please enter a valid URL for the Registration/Info Link (e.g., https://...)");
             submitButton.disabled = false; submitButton.textContent = 'Submit Suggestion'; return;
         }


        console.log("Submitting hackathon for verification:", hackathonData);

        try {
            // POST to the endpoint that saves to 'unverified_hackathons'
            // Requires user to be logged in (cookie auth is handled by browser)
            const response = await fetch('/api/hackathons', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(hackathonData)
            });

            const responseData = await response.json(); // Try to parse JSON response

            if (!response.ok) {
                // Use detail from backend error if available
                throw new Error(responseData.detail || `Failed to submit: ${response.statusText}`);
            }

            // *** MODIFICATION: Changed alert, removed list refresh ***
            alert('Hackathon submitted for verification. Thank you!');
            hackathonForm.reset();
            // DO NOT refresh the list here: fetchAndRenderHackathons();

        } catch (error) {
            console.error('Error adding hackathon:', error);
            alert(`Failed to submit hackathon: ${error.message}`);
        } finally {
            // Re-enable button
            submitButton.disabled = false;
            submitButton.textContent = 'Submit Suggestion';
        }
    });

    // --- Handle Search ---
    hackathonSearchButton.addEventListener('click', () => {
        const searchTerm = hackathonSearchInput.value;
        // Filter client-side data and re-render
        renderHackathons(searchTerm);
    });

    // Optional: Trigger search on Enter key press
    hackathonSearchInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent default form submission if inside one
            renderHackathons(hackathonSearchInput.value);
        }
    });
    // Optional: Trigger search as user types (with debounce)
     hackathonSearchInput.addEventListener('input', () => {
         clearTimeout(hackathonSearchInput.debounceTimer);
         hackathonSearchInput.debounceTimer = setTimeout(() => {
              renderHackathons(hackathonSearchInput.value);
         }, 300); // 300ms debounce
     });


    // --- Initial Load ---
    // updateNavbar(); // Call this ONLY if you need dynamic navbar updates on this page
    fetchAndRenderHackathons(); // Fetch and display hackathons on page load

}); // End DOMContentLoaded