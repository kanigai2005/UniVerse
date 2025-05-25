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
    console.log("Career Fairs & Jobs DOM Loaded.");

    const showAddFairBtn = document.getElementById('show-add-fair-form-btn');
    const showAddJobBtn = document.getElementById('show-add-job-form-btn');
    const addFairModal = document.getElementById('add-fair-modal');
    const addJobModal = document.getElementById('add-job-modal');
    const allCloseModalBtns = document.querySelectorAll('.close-modal-btn');
    const careerFairForm = document.getElementById('career-fair-form');
    const jobListingForm = document.getElementById('job-listing-form');

    const careerFairsListContainer = document.getElementById('career-fairs-list');
    const careerFairSearchInput = document.getElementById('search-career-fair-input');
    const careerFairSearchButton = document.getElementById('search-career-fair-button');
    const toggleFairsBtn = document.getElementById('toggle-fairs-visibility-btn');

    const jobListContainer = document.getElementById('current-jobs-list');
    const jobSearchInput = document.getElementById('search-job-input');
    const jobListingSearchButton = document.getElementById('search-job-button');
    const toggleJobsBtn = document.getElementById('toggle-jobs-visibility-btn');

    let allFairsData = [];
    let allJobsData = [];
    const ITEMS_DISPLAY_LIMIT = 5; // Number of items in one view (e.g., 5 rows, meaning 10 items if 2 per row)
    let showAllFairs = false;
    let showAllJobs = false;
    let currentFilteredFairs = [];
    let currentFilteredJobs = [];

    if (!careerFairsListContainer || !jobListContainer || !careerFairForm || !jobListingForm ||
        !addFairModal || !addJobModal || !showAddFairBtn || !showAddJobBtn ||
        !toggleFairsBtn || !toggleJobsBtn ) {
         console.error("CRITICAL ERROR: One or more essential page elements not found.");
         // Display error messages in the respective list containers if they exist
         if (careerFairsListContainer) careerFairsListContainer.innerHTML = '<div class="error-message">Page Error: UI elements missing.</div>';
         if (jobListContainer) jobListContainer.innerHTML = '<div class="error-message">Page Error: UI elements missing.</div>';
         return; // Stop further execution if critical elements are missing
    }


    function openModal(modalElement) { if (modalElement) modalElement.style.display = 'block'; }
    function closeModal(modalElement) {
         if (modalElement) {
             modalElement.style.display = 'none';
             const form = modalElement.querySelector('form');
             if (form) form.reset();
         }
    }

    async function fetchCareerFairs() {
        careerFairsListContainer.innerHTML = '<div class="loading-message">Loading career fairs...</div>';
        try {
            const response = await fetch('/api/career_fairs?upcoming_only=false');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            allFairsData = await response.json();
            if (!Array.isArray(allFairsData)) throw new Error("Invalid data format for fairs.");
            showAllFairs = false;
            displayCareerFairs(allFairsData);
        } catch (error) {
            console.error("Error fetching career fairs:", error);
            careerFairsListContainer.innerHTML = `<div class="error-message">Could not load career fairs: ${escapeHtml(error.message)}</div>`;
            toggleFairsBtn.style.display = 'none';
        }
    }

    async function fetchJobs() {
        jobListContainer.innerHTML = '<div class="loading-message">Loading job listings...</div>';
        try {
            const response = await fetch('/api/jobs');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            allJobsData = await response.json();
            if (!Array.isArray(allJobsData)) throw new Error("Invalid data format for jobs.");
            showAllJobs = false;
            displayJobs(allJobsData);
        } catch (error) {
            console.error("Error fetching jobs:", error);
            jobListContainer.innerHTML = `<div class="error-message">Could not load job listings: ${escapeHtml(error.message)}</div>`;
            toggleJobsBtn.style.display = 'none';
        }
    }

    function displayCareerFairs(fairsToProcess) {
        currentFilteredFairs = fairsToProcess;
        careerFairsListContainer.innerHTML = '';

        // Determine how many individual items to show based on ITEMS_DISPLAY_LIMIT (which refers to rows)
        const itemsToShowCount = showAllFairs ? currentFilteredFairs.length : ITEMS_DISPLAY_LIMIT * 2;
        const itemsToRender = currentFilteredFairs.slice(0, itemsToShowCount);


        if (itemsToRender.length === 0) {
            careerFairsListContainer.innerHTML = '<div class="no-items-message">No career fairs found matching criteria.</div>';
            toggleFairsBtn.style.display = 'none';
            return;
        }

        itemsToRender.sort((a, b) => new Date(b.date) - new Date(a.date)); // Sort by date desc

        let currentRow = null;
        itemsToRender.forEach((fair, index) => {
            if (!fair || !fair.id) return;
            if (index % 2 === 0) {
                currentRow = document.createElement('li');
                currentRow.classList.add('item-row'); // Use generic item-row
                careerFairsListContainer.appendChild(currentRow);
            }
            const card = document.createElement('div');
            card.classList.add('item-card'); // Use generic item-card
            const fairDate = fair.date ? new Date(fair.date + 'T00:00:00').toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Date TBD';
            card.innerHTML = `
                <strong>${escapeHtml(fair.name || 'Unnamed Fair')}</strong>
                <div>${fairDate}</div>
                <div style="font-size: 0.85em;">Location: ${escapeHtml(fair.location || 'N/A')}</div>
                <p style="white-space: pre-wrap;">${escapeHtml(fair.description || 'No description.')}</p>
                ${fair.url ? `<a href="${escapeHtml(fair.url)}" target="_blank" rel="noopener noreferrer" class="more-info-link">More Info</a>` : ''}
            `;
            currentRow.appendChild(card);
        });

        if (currentFilteredFairs.length > itemsToShowCount) {
            toggleFairsBtn.style.display = 'block';
            const remainingItems = currentFilteredFairs.length - itemsToShowCount;
            toggleFairsBtn.textContent = `Show More Fairs (${remainingItems} more)`;
        } else if (currentFilteredFairs.length > ITEMS_DISPLAY_LIMIT * 2 && showAllFairs) {
            toggleFairsBtn.style.display = 'block';
            toggleFairsBtn.textContent = 'Show Less Fairs';
        } else {
            toggleFairsBtn.style.display = 'none';
        }
    }

    function displayJobs(jobsToProcess) {
        currentFilteredJobs = jobsToProcess;
        jobListContainer.innerHTML = '';

        const itemsToShowCount = showAllJobs ? currentFilteredJobs.length : ITEMS_DISPLAY_LIMIT * 2;
        const itemsToRender = currentFilteredJobs.slice(0, itemsToShowCount);

        if (itemsToRender.length === 0) {
            jobListContainer.innerHTML = '<div class="no-items-message">No job listings found matching criteria.</div>';
            toggleJobsBtn.style.display = 'none';
            return;
        }

        itemsToRender.sort((a, b) => { // Sort by date_posted desc, nulls last
            const dateA = a?.date_posted ? new Date(a.date_posted) : null;
            const dateB = b?.date_posted ? new Date(b.date_posted) : null;
            if (dateA === null && dateB === null) return 0;
            if (dateA === null) return 1;
            if (dateB === null) return -1;
            return dateB - dateA;
        });

        let currentRow = null;
        itemsToRender.forEach((job, index) => {
            if (!job || !job.id) return;
            if (index % 2 === 0) {
                currentRow = document.createElement('li');
                currentRow.classList.add('item-row'); // Use generic item-row
                jobListContainer.appendChild(currentRow);
            }
            const card = document.createElement('div');
            card.classList.add('item-card'); // Use generic item-card
            const postDate = job.date_posted ? new Date(job.date_posted + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : '';
            card.innerHTML = `
                <a href="${escapeHtml(job.url || '#')}" target="_blank" rel="noopener noreferrer" class="item-title">${escapeHtml(job.title || 'Untitled Job')}</a>
                ${postDate ? `<div style="font-size: 0.8em; color: #777;">Posted: ${postDate}</div>` : ''}
                <div><strong>Company:</strong> ${escapeHtml(job.company || 'N/A')}</div>
                <div><strong>Location:</strong> ${escapeHtml(job.location || 'N/A')}</div>
                <p style="white-space: pre-wrap;">${escapeHtml(job.description?.substring(0, 120) || 'No description.')}${job.description?.length > 120 ? '...' : ''}</p>
            `;
            // The job URL is already the title link, so no separate "More Info" unless desired.
            if (job.url && job.title !== job.url) { // Add a more info if URL is different and not just title
                 // card.innerHTML += `<a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer" class="more-info-link">Details / Apply</a>`;
            }
            currentRow.appendChild(card);
        });

        if (currentFilteredJobs.length > itemsToShowCount) {
            toggleJobsBtn.style.display = 'block';
            const remainingItems = currentFilteredJobs.length - itemsToShowCount;
            toggleJobsBtn.textContent = `Show More Jobs (${remainingItems} more)`;
        } else if (currentFilteredJobs.length > ITEMS_DISPLAY_LIMIT * 2 && showAllJobs) {
            toggleJobsBtn.style.display = 'block';
            toggleJobsBtn.textContent = 'Show Less Jobs';
        } else {
            toggleJobsBtn.style.display = 'none';
        }
    }


    function searchCareerFairs() {
        const searchTerm = careerFairSearchInput.value.toLowerCase().trim();
        const filtered = allFairsData.filter(fair => {
            if (!fair) return false;
            return `${fair.name || ''} ${fair.location || ''} ${fair.description || ''}`.toLowerCase().includes(searchTerm);
        });
        showAllFairs = false;
        displayCareerFairs(filtered);
    }

    function searchJobs() {
        const searchTerm = jobSearchInput.value.toLowerCase().trim();
        const filtered = allJobsData.filter(job => {
            if (!job) return false;
            return `${job.title || ''} ${job.company || ''} ${job.location || ''} ${job.description || ''} ${job.type || ''} ${job.experience || ''}`.toLowerCase().includes(searchTerm);
        });
        showAllJobs = false;
        displayJobs(filtered);
    }

    // Form Submissions (condensed for brevity, no change in logic)
    careerFairForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]'); btn.disabled = true; btn.textContent="Submitting...";
        const data = { name: document.getElementById('cf-name').value, location: document.getElementById('cf-location').value, date: document.getElementById('cf-date').value, description: document.getElementById('cf-description').value, url: document.getElementById('cf-link').value };
        if (!data.name || !data.date) { alert("Name and Date required."); btn.disabled = false; btn.textContent="Submit for Review"; return; }
        try {
            const res = await fetch('/api/career_fairs', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
            if (!res.ok) { const err = await res.json(); throw new Error(err.detail || res.statusText); }
            alert('Career fair submitted!'); closeModal(addFairModal);
        } catch (err) { alert(`Error: ${err.message}`); } finally { btn.disabled = false; btn.textContent="Submit for Review"; }
    });

    jobListingForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]'); btn.disabled = true; btn.textContent="Submitting...";
        const data = { title: document.getElementById('job-title').value, company: document.getElementById('job-company').value, location: document.getElementById('job-location').value, date_posted: document.getElementById('job-post-date').value, description: document.getElementById('job-description').value, salary: document.getElementById('job-salary').value, type: document.getElementById('job-type').value, experience: document.getElementById('job-experience').value, imageUrl: document.getElementById('job-image-url').value, url: document.getElementById('job-link').value };
        if (!data.title) { alert("Title required."); btn.disabled = false; btn.textContent="Submit for Review"; return; }
        try {
            const res = await fetch('/api/jobs', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) });
            if (!res.ok) { const err = await res.json(); throw new Error(err.detail || res.statusText); }
            alert('Job listing submitted!'); closeModal(addJobModal);
        } catch (err) { alert(`Error: ${err.message}`); } finally { btn.disabled = false; btn.textContent="Submit for Review"; }
    });


    // Event Listeners
    showAddFairBtn.addEventListener('click', () => openModal(addFairModal));
    showAddJobBtn.addEventListener('click', () => openModal(addJobModal));
    allCloseModalBtns.forEach(btn => btn.addEventListener('click', function() { closeModal(this.closest('.modal')); }));
    if (addFairModal) addFairModal.addEventListener('click', (e) => { if(e.target === addFairModal) closeModal(addFairModal); });
    if (addJobModal) addJobModal.addEventListener('click', (e) => { if(e.target === addJobModal) closeModal(addJobModal); });

    toggleFairsBtn.addEventListener('click', () => {
        showAllFairs = !showAllFairs;
        displayCareerFairs(currentFilteredFairs);
    });
    toggleJobsBtn.addEventListener('click', () => {
        showAllJobs = !showAllJobs;
        displayJobs(currentFilteredJobs);
    });

    let fairDebounce, jobDebounce;
    careerFairSearchButton.addEventListener('click', searchCareerFairs);
    careerFairSearchInput.addEventListener('input', () => { clearTimeout(fairDebounce); fairDebounce = setTimeout(searchCareerFairs, 300); });
    careerFairSearchInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') searchCareerFairs(); });

    jobListingSearchButton.addEventListener('click', searchJobs);
    jobSearchInput.addEventListener('input', () => { clearTimeout(jobDebounce); jobDebounce = setTimeout(searchJobs, 300); });
    jobSearchInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') searchJobs(); });

    fetchCareerFairs();
    fetchJobs();
});