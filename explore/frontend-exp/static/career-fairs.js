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

document.addEventListener('DOMContentLoaded', () => {
    console.log("Career Fairs & Jobs DOM Loaded.");

    // --- Element References ---
    // Trigger Buttons for Modals
    const showAddFairBtn = document.getElementById('show-add-fair-form-btn');
    const showAddJobBtn = document.getElementById('show-add-job-form-btn');

    // Modals
    const addFairModal = document.getElementById('add-fair-modal');
    const addJobModal = document.getElementById('add-job-modal');
    const allCloseModalBtns = document.querySelectorAll('.close-modal-btn'); // Get all close buttons

    // Forms (inside modals)
    const careerFairForm = document.getElementById('career-fair-form');
    const jobListingForm = document.getElementById('job-listing-form');

    // Career Fair List & Search
    const careerFairsListContainer = document.getElementById('career-fairs-list');
    const careerFairSearchInput = document.getElementById('search-career-fair-input');
    const careerFairSearchButton = document.getElementById('search-career-fair-button');

    // Job List & Search
    const jobListContainer = document.getElementById('current-jobs-list');
    const jobSearchInput = document.getElementById('search-job-input');
    const jobListingSearchButton = document.getElementById('search-job-button');

    // --- State Variables ---
    let allFairsData = [];
    let allJobsData = [];

    // --- Check Essential Elements ---
    if (!careerFairsListContainer || !jobListContainer || !careerFairForm || !jobListingForm || !addFairModal || !addJobModal || !showAddFairBtn || !showAddJobBtn ) {
         console.error("CRITICAL ERROR: One or more essential page elements not found in the HTML. Functionality may be broken.");
         // Provide feedback if possible
         if (careerFairsListContainer) careerFairsListContainer.innerHTML = '<li class="error-message">Page Error: UI elements missing.</li>';
         if (jobListContainer) jobListContainer.innerHTML = '<li class="error-message">Page Error: UI elements missing.</li>';
         // Don't necessarily return, some parts might still work
    }


    // --- Helper: Open/Close Modal ---
    function openModal(modalElement) {
        if (modalElement) {
            console.log(`Opening modal: #${modalElement.id}`);
            modalElement.style.display = 'block';
        } else { console.error("Attempted to open a null modal element."); }
    }
    function closeModal(modalElement) {
         if (modalElement) {
             console.log(`Closing modal: #${modalElement.id}`);
             modalElement.style.display = 'none';
             const form = modalElement.querySelector('form');
             if (form) form.reset(); // Reset form when closing
         } else { console.error("Attempted to close a null modal element."); }
    }

    // --- Fetching Functions ---
    async function fetchCareerFairs() {
        console.log("Fetching career fairs...");
        if (!careerFairsListContainer) { console.error("Career fairs list container not found!"); return; }
        careerFairsListContainer.innerHTML = '<li>Loading career fairs...</li>';
        try {
            const response = await fetch('/api/career_fairs?upcoming_only=false'); // Fetch verified fairs
            console.log("Career Fairs API Response Status:", response.status);
            if (!response.ok) {
                let errorDetail = `HTTP error! status: ${response.status}`;
                try { const errorData = await response.json(); errorDetail = errorData.detail || errorDetail; } catch (e) {}
                throw new Error(errorDetail);
            }
            const fairs = await response.json();
            console.log("Fetched career fairs data:", fairs);
            if (!Array.isArray(fairs)) { throw new Error("Invalid data format for fairs."); }
            allFairsData = fairs;
            displayCareerFairs(allFairsData);
        } catch (error) {
            console.error("Error fetching career fairs:", error);
            if(careerFairsListContainer) careerFairsListContainer.innerHTML = `<li class="error-message" style="color:red;">Could not load career fairs: ${escapeHtml(error.message)}</li>`;
        }
    }

    async function fetchJobs() {
        console.log("Fetching jobs...");
        if (!jobListContainer) { console.error("Job listings container not found!"); return; }
        jobListContainer.innerHTML = '<li>Loading job listings...</li>';
        try {
            const response = await fetch('/api/jobs'); // Fetch verified jobs
             console.log("Jobs API Response Status:", response.status);
            if (!response.ok) {
                let errorDetail = `HTTP error! status: ${response.status}`;
                try { const errorData = await response.json(); errorDetail = errorData.detail || errorDetail; } catch (e) {}
                throw new Error(errorDetail);
            }
            const jobs = await response.json();
            console.log("Fetched jobs data:", jobs);
            if (!Array.isArray(jobs)) { throw new Error("Invalid data format for jobs."); }
            allJobsData = jobs;
            displayJobs(allJobsData);
        } catch (error) {
            console.error("Error fetching jobs:", error);
             if(jobListContainer) jobListContainer.innerHTML = `<li class="error-message" style="color:red;">Could not load job listings: ${escapeHtml(error.message)}</li>`;
        }
    }

    // --- Display Functions ---
    function displayCareerFairs(fairs) {
        if (!careerFairsListContainer) return;
        careerFairsListContainer.innerHTML = ''; // Clear

        if (!fairs || fairs.length === 0) {
            careerFairsListContainer.innerHTML = '<li>No career fairs found matching criteria.</li>';
            return;
        }
        // Sort fairs by date (most recent first), nulls last
        fairs.sort((a, b) => {
            const dateA = a?.date ? new Date(a.date) : null;
            const dateB = b?.date ? new Date(b.date) : null;
            if (dateA === null && dateB === null) return 0;
            if (dateA === null) return 1;
            if (dateB === null) return -1;
            return dateB - dateA; // Descending
        });

        fairs.forEach(fair => {
             if (!fair || !fair.id) { console.warn("Skipping invalid fair item:", fair); return; } // Basic validation
            const listItem = document.createElement('li');
            const fairDate = fair.date ? new Date(fair.date + 'T00:00:00').toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Date TBD';
            listItem.innerHTML = `
                <div>
                    <strong>${escapeHtml(fair.name || 'Unnamed Fair')}</strong> - ${fairDate}
                    <div style="font-size: 0.85em; color: var(--text-secondary);">Location: ${escapeHtml(fair.location || 'N/A')}</div>
                    <p style="font-size: 0.9em; margin-top: 5px; white-space: pre-wrap;">${escapeHtml(fair.description || 'No description.')}</p>
                    ${fair.url ? `<a href="${escapeHtml(fair.url)}" target="_blank" rel="noopener noreferrer" style="font-size: 0.85em; color: var(--primary-color); text-decoration: none;">More Info</a>` : ''}
                </div>`;
            careerFairsListContainer.appendChild(listItem);
        });
    }

    function displayJobs(jobs) {
        if (!jobListContainer) { console.error("Job list container (#current-jobs-list) not found"); return; }
        jobListContainer.innerHTML = ''; // Clear

        if (!jobs || jobs.length === 0) {
            jobListContainer.innerHTML = '<li>No job listings found matching criteria.</li>';
            return;
        }
         // Sort jobs by date posted (most recent first), nulls last
         jobs.sort((a, b) => {
            const dateA = a?.date_posted ? new Date(a.date_posted) : null;
            const dateB = b?.date_posted ? new Date(b.date_posted) : null;
            if (dateA === null && dateB === null) return 0;
            if (dateA === null) return 1;
            if (dateB === null) return -1;
            return dateB - dateA; // Descending
         });

        jobs.forEach(job => {
             if (!job || !job.id) { console.warn("Skipping invalid job item:", job); return; } // Basic validation
            const listItem = document.createElement('li');
            const postDate = job.date_posted ? new Date(job.date_posted + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : '';
            listItem.innerHTML = `
                 <div>
                    <a href="${escapeHtml(job.url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(job.title || 'Untitled Job')}</a>
                    ${postDate ? `<span style="font-size: 0.8em; color: #777;"> (${postDate})</span>` : ''}
                    <div style="font-size: 0.9em;"><strong>Company:</strong> ${escapeHtml(job.company || 'N/A')}</div>
                    <div style="font-size: 0.9em;"><strong>Location:</strong> ${escapeHtml(job.location || 'N/A')}</div>
                    <p style="font-size: 0.85em; margin-top: 5px; white-space: pre-wrap;">${escapeHtml(job.description?.substring(0, 150) || 'No description.')}${job.description?.length > 150 ? '...' : ''}</p>
                 </div>`;
            jobListContainer.appendChild(listItem);
        });
    }

    // --- Search Functions ---
    function searchCareerFairs() {
        if (!careerFairSearchInput) { console.error("Career Fair search input not found"); return; }
        const searchTerm = careerFairSearchInput.value.toLowerCase().trim();
        console.log(`Searching career fairs for: "${searchTerm}"`);
        const filteredFairs = allFairsData.filter(fair => {
            if (!fair) return false;
            const searchableText = `${fair.name || ''} ${fair.location || ''} ${fair.description || ''}`.toLowerCase();
            return searchableText.includes(searchTerm);
        });
        displayCareerFairs(filteredFairs); // Display filtered results
    }

    function searchJobs() {
        if (!jobSearchInput) { console.error("Job search input not found"); return; }
        const searchTerm = jobSearchInput.value.toLowerCase().trim();
        console.log(`Searching jobs for: "${searchTerm}"`);
        const filteredJobs = allJobsData.filter(job => {
            if (!job) return false;
             const searchableText = `${job.title || ''} ${job.company || ''} ${job.location || ''} ${job.description || ''} ${job.type || ''} ${job.experience || ''}`.toLowerCase();
            return searchableText.includes(searchTerm);
        });
        displayJobs(filteredJobs); // Display filtered results
    }

    // --- Form Submission Handlers (Inside Modals) ---
    if (careerFairForm) {
        careerFairForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log("Submitting career fair form from modal...");
            const submitButton = careerFairForm.querySelector('button[type="submit"]');
            if(!submitButton) return;
            submitButton.disabled = true;
            submitButton.textContent = "Submitting...";

            const fairData = { // Matches CareerFairCreate model
                name: document.getElementById('cf-name')?.value.trim() || '',
                location: document.getElementById('cf-location')?.value.trim() || null,
                date: document.getElementById('cf-date')?.value || null,
                description: document.getElementById('cf-description')?.value.trim() || null,
                url: document.getElementById('cf-link')?.value.trim() || null
            };

            if (!fairData.name || !fairData.date) {
                 alert("Career Fair Name and Date are required.");
                 submitButton.disabled = false;
                 submitButton.textContent = "Submit for Review";
                 return;
            }

            try {
                // POSTs to endpoint saving to unverified table, requires cookie auth
                const response = await fetch('/api/career_fairs', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(fairData)
                });
                const responseData = await response.json();
                if (!response.ok) throw new Error(responseData.detail || `HTTP error ${response.status}`);

                console.log("Career fair submitted for verification:", responseData);
                alert('Career fair submitted for verification!');
                closeModal(addFairModal); // Close modal on success

            } catch (error) {
                console.error('Error submitting career fair:', error);
                alert(`Failed to submit career fair: ${error.message}`);
            } finally {
                 submitButton.disabled = false;
                 submitButton.textContent = "Submit for Review";
            }
        });
    } else { console.error("Career fair form (#career-fair-form) not found!"); }

    if (jobListingForm) {
        jobListingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log("Submitting job listing form from modal...");
            const submitButton = jobListingForm.querySelector('button[type="submit"]');
            if(!submitButton) return;
            submitButton.disabled = true;
            submitButton.textContent = "Submitting...";

            const jobData = { // Matches JobCreate model
                title: document.getElementById('job-title')?.value.trim() || '',
                company: document.getElementById('job-company')?.value.trim() || null,
                location: document.getElementById('job-location')?.value.trim() || null,
                date_posted: document.getElementById('job-post-date')?.value || null,
                description: document.getElementById('job-description')?.value.trim() || null,
                salary: document.getElementById('job-salary')?.value.trim() || null,
                type: document.getElementById('job-type')?.value.trim() || null,
                experience: document.getElementById('job-experience')?.value.trim() || null,
                imageUrl: document.getElementById('job-image-url')?.value.trim() || null,
                url: document.getElementById('job-link')?.value.trim() || null
            };

            if (!jobData.title) {
                 alert("Job Title is required.");
                 submitButton.disabled = false;
                 submitButton.textContent = "Submit for Review";
                 return;
            }

            try {
                 // POSTs to endpoint saving to unverified table, requires cookie auth
                const response = await fetch('/api/jobs', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(jobData)
                });
                const responseData = await response.json();
                if (!response.ok) throw new Error(responseData.detail || `HTTP error ${response.status}`);

                console.log("Job submitted for verification:", responseData);
                alert('Job listing submitted for verification!');
                closeModal(addJobModal); // Close modal on success

            } catch (error) {
                console.error('Error submitting job:', error);
                alert(`Failed to submit job listing: ${error.message}`);
            } finally {
                 submitButton.disabled = false;
                 submitButton.textContent = "Submit for Review";
            }
        });
    } else { console.error("Job listing form (#job-listing-form) not found!"); }

    // --- Attach Event Listeners ---

    // Modal Triggers
    if(showAddFairBtn) showAddFairBtn.addEventListener('click', () => openModal(addFairModal));
    else console.error("Button #show-add-fair-form-btn not found");

    if(showAddJobBtn) showAddJobBtn.addEventListener('click', () => openModal(addJobModal));
    else console.error("Button #show-add-job-form-btn not found");

    // Modal Close Buttons
    allCloseModalBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const modalToClose = this.closest('.modal'); // Find parent modal
            if (modalToClose) {
                closeModal(modalToClose);
            } else {
                console.error("Could not find parent modal for close button:", this);
            }
        });
    });

    // Close modal on overlay click
    if (addFairModal) addFairModal.addEventListener('click', (e) => { if(e.target === addFairModal) closeModal(addFairModal); });
    if (addJobModal) addJobModal.addEventListener('click', (e) => { if(e.target === addJobModal) closeModal(addJobModal); });


    // Search Buttons & Inputs
    if (careerFairSearchButton && careerFairSearchInput) {
        careerFairSearchButton.addEventListener('click', searchCareerFairs);
        careerFairSearchInput.addEventListener('input', () => {
             clearTimeout(careerFairSearchInput.debounceTimer);
             careerFairSearchInput.debounceTimer = setTimeout(searchCareerFairs, 300);
        });
        careerFairSearchInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') searchCareerFairs(); });
    } else { console.error("Career fair search elements (#search-career-fair-input or #search-career-fair-button) not found!"); }

    if (jobListingSearchButton && jobSearchInput) {
        jobListingSearchButton.addEventListener('click', searchJobs);
         jobSearchInput.addEventListener('input', () => {
             clearTimeout(jobSearchInput.debounceTimer);
             jobSearchInput.debounceTimer = setTimeout(searchJobs, 300);
         });
         jobSearchInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') searchJobs(); });
    } else { console.error("Job search elements (#search-job-input or #search-job-button) not found!"); }

    // --- Initial Data Load ---
    fetchCareerFairs(); // Fetch fairs
    fetchJobs(); // Fetch jobs

}); // End DOMContentLoaded