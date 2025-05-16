// static/admin-eventmanagement.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin Event Management JS Loaded - V4: Integrated Search & Add New");

    const sections = {
        job: document.getElementById('unverified-jobs-grid'),
        internship: document.getElementById('unverified-internships-grid'),
        'career-fair': document.getElementById('unverified-career-fairs-grid'),
        hackathon: document.getElementById('unverified-hackathons-grid')
    };
    const allItemTypes = ['job', 'internship', 'career-fair', 'hackathon'];

    const detailsModalOverlay = document.getElementById('item-details-modal-overlay');
    const modalItemTitle = document.getElementById('modal-item-title');
    const modalItemDetailsBody = document.getElementById('modal-item-details-body');
    const modalSubmittedBy = document.getElementById('modal-submitted-by');
    const modalSubmissionDate = document.getElementById('modal-submission-date');
    const modalItemUrlLink = document.getElementById('modal-item-url');
    const modalItemUrlContainer = document.getElementById('modal-item-url-container');
    const modalCloseViewBtn = document.getElementById('modal-close-view-btn');
    const modalApproveBtn = document.getElementById('modal-approve-btn');
    const modalRejectBtn = document.getElementById('modal-reject-btn');
    const modalVisitSiteBtnAction = document.getElementById('modal-visit-site-btn-action');

    const addNewModalOverlay = document.getElementById('add-new-item-modal-overlay');
    const addNewModalTitle = document.getElementById('add-modal-title');
    const addNewItemForm = document.getElementById('add-new-item-form');
    const addModalCancelBtn = document.getElementById('add-modal-cancel-btn');
    // submit button is part of the form tag

    const submissionSearchInput = document.getElementById('submission-search-input');
    const submissionSearchButton = document.getElementById('submission-search-button');

    let currentDetailsModalItem = null;
    let currentAddItemType = null;
    let allUnverifiedItemsCache = {};

    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') { return unsafe === null || unsafe === undefined ? '' : String(unsafe); }
        return unsafe.replace(/&/g, "&").replace(/</g, "<").replace(/>/g, ">").replace(/"/g, "").replace(/'/g, "'");
    }
    function capitalizeFirstLetter(string) {
        if (!string) return '';
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    async function apiCall(url, method = 'GET', body = null) {
        const options = { method, headers: {}, credentials: 'include' };
        if (body && (method === 'POST' || method === 'PUT')) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
        try {
            const response = await fetch(url, options);
            const responseData = await response.json().catch(() => ({ detail: "Non-JSON response or empty response from server" }));
            if (!response.ok) {
                console.error(`API Error (${method} ${url}): Status ${response.status}`, responseData);
                throw new Error(responseData.detail || `Request failed: ${response.status}`);
            }
            return responseData;
        } catch (error) {
            console.error(`API Call Exception (${method} ${url}):`, error);
            alert(`An API error occurred: ${error.message}`);
            throw error;
        }
    }

    function renderSubmissionCard(item, type) {
        const card = document.createElement('div');
        card.classList.add('submission-card');
        card.dataset.itemId = item.id;
        card.dataset.itemType = type;
        const title = item.title || item.name || 'Untitled Submission';
        let detailsPreviewHtml = `<p><strong>ID:</strong> ${item.id}</p>`;
        if (item.company) detailsPreviewHtml += `<p><strong>Company:</strong> ${escapeHtml(item.company)}</p>`;
        if (item.location) detailsPreviewHtml += `<p><strong>Location:</strong> ${escapeHtml(item.location)}</p>`;
        let displayDate = null;
        if (item.start_date) displayDate = new Date(item.start_date).toLocaleDateString();
        else if (item.date_posted) displayDate = new Date(item.date_posted).toLocaleDateString();
        if (displayDate) detailsPreviewHtml += `<p><strong>Date:</strong> ${displayDate}</p>`;
        card.innerHTML = `
            <h3>${escapeHtml(title)}</h3>
            ${detailsPreviewHtml}
            <div class="actions">
                <button class="view-details-btn" title="View Full Details"><i class="fas fa-eye"></i> Details</button>
            </div>
        `;
        card.querySelector('.view-details-btn').addEventListener('click', () => openDetailsModal(item, type, card));
        return card;
    }

    async function loadUnverifiedItems(itemType, searchTerm = '') {
        const container = sections[itemType];
        if (!container) { console.error(`Container for type '${itemType}' not found.`); return; }
        container.innerHTML = '<p class="loading">Loading...</p>';
        try {
            let itemsToDisplay;
            if (!searchTerm && allUnverifiedItemsCache[itemType] && allUnverifiedItemsCache[itemType].length > 0) {
                itemsToDisplay = allUnverifiedItemsCache[itemType];
            } else {
                const fetchedItems = await apiCall(`/api/admin/unverified-items?type=${itemType}`);
                if (Array.isArray(fetchedItems)) {
                    allUnverifiedItemsCache[itemType] = fetchedItems;
                    itemsToDisplay = fetchedItems;
                } else { itemsToDisplay = []; console.error(`Invalid data for ${itemType}:`, fetchedItems); }
            }
            if (searchTerm) {
                const lowerSearchTerm = searchTerm.toLowerCase();
                itemsToDisplay = itemsToDisplay.filter(item => (item.title || item.name || '').toLowerCase().includes(lowerSearchTerm));
            }
            container.innerHTML = '';
            if (itemsToDisplay.length === 0) {
                const message = searchTerm ? `No pending '${itemType}' submissions match "${escapeHtml(searchTerm)}".` : `No pending submissions for ${itemType}.`;
                container.innerHTML = `<p class="no-data">${message}</p>`;
            } else {
                itemsToDisplay.forEach(item => container.appendChild(renderSubmissionCard(item, itemType)));
            }
        } catch (error) {
            container.innerHTML = `<p class="error-message">Could not load ${itemType} submissions: ${escapeHtml(error.message)}</p>`;
        }
    }
    
    function openDetailsModal(itemData, itemType, cardElement) {
        currentDetailsModalItem = { id: itemData.id, type: itemType, element: cardElement, data: itemData };
        modalItemTitle.textContent = `Review Submission: ${escapeHtml(itemData.title || itemData.name || 'N/A')}`;
        let detailsHtmlContent = '';
        const fieldsToExclude = ['id', 'title', 'name', 'submitted_by_user_id', 'submitted_at', 'status', 'url', 'imageUrl'];
        for (const key in itemData) {
            if (itemData.hasOwnProperty(key) && !fieldsToExclude.includes(key) && itemData[key] !== null && itemData[key] !== undefined && String(itemData[key]).trim() !== '') {
                let value = itemData[key];
                let displayKey = capitalizeFirstLetter(key.replace(/_/g, ' '));
                if (key.includes('date') || key.includes('at')) {
                    try { value = new Date(value).toLocaleString(); } catch(e) { value = escapeHtml(value); }
                } else { value = escapeHtml(value); }
                detailsHtmlContent += `<p><strong>${displayKey}:</strong> ${value}</p>`;
            }
        }
        if (itemData.imageUrl) {
            detailsHtmlContent += `<p><strong>Image URL:</strong> <a href="${itemData.imageUrl}" target="_blank" rel="noopener noreferrer">${escapeHtml(itemData.imageUrl)}</a></p>`;
        }
        modalItemDetailsBody.innerHTML = detailsHtmlContent || '<p>No additional details provided.</p>';
        modalSubmittedBy.textContent = itemData.submitted_by_user_id || 'N/A';
        modalSubmissionDate.textContent = itemData.submitted_at ? new Date(itemData.submitted_at).toLocaleString() : 'N/A';
        if (itemData.url && String(itemData.url).trim() !== '') {
            const validUrl = itemData.url.startsWith('http://') || itemData.url.startsWith('https://') ? itemData.url : `http://${itemData.url}`;
            if (modalItemUrlLink) { modalItemUrlLink.href = validUrl; modalItemUrlLink.textContent = itemData.url; }
            if (modalItemUrlContainer) modalItemUrlContainer.style.display = 'block';
            if (modalVisitSiteBtnAction) { modalVisitSiteBtnAction.href = validUrl; modalVisitSiteBtnAction.style.display = 'inline-flex'; }
        } else {
            if (modalItemUrlContainer) modalItemUrlContainer.style.display = 'none';
            if (modalVisitSiteBtnAction) modalVisitSiteBtnAction.style.display = 'none';
        }
        detailsModalOverlay.style.display = 'flex';
        setTimeout(() => detailsModalOverlay.classList.add('active'), 10);
    }

    function closeDetailsModal() {
        detailsModalOverlay.classList.remove('active');
        setTimeout(() => detailsModalOverlay.style.display = 'none', 300);
        currentDetailsModalItem = null;
    }

    if(modalCloseViewBtn) modalCloseViewBtn.addEventListener('click', closeDetailsModal);
    if(detailsModalOverlay) detailsModalOverlay.addEventListener('click', (e) => { if (e.target === detailsModalOverlay) closeDetailsModal(); });

    async function handleModeration(action) {
        if (!currentDetailsModalItem) return;
        const { id, type, element } = currentDetailsModalItem;
        const buttonToUpdate = action === 'approve' ? modalApproveBtn : modalRejectBtn;
        const originalButtonText = buttonToUpdate.innerHTML;
        buttonToUpdate.disabled = true; buttonToUpdate.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        const otherButton = action === 'approve' ? modalRejectBtn : modalApproveBtn;
        otherButton.disabled = true;
        try {
            const result = await apiCall(`/api/admin/unverified-items/${id}/${action}?type=${type}`, 'POST');
            alert(result.message || `${capitalizeFirstLetter(type)} ${action}d successfully!`);
            if (element) element.remove();
            if (allUnverifiedItemsCache[type]) {
                allUnverifiedItemsCache[type] = allUnverifiedItemsCache[type].filter(item => item.id !== id);
                // If list becomes empty after removal, show no-data message
                const container = sections[type];
                if (container && allUnverifiedItemsCache[type].length === 0 && !submissionSearchInput.value.trim()) {
                    container.innerHTML = `<p class="no-data">No pending submissions for ${type}.</p>`;
                }
            }
            closeDetailsModal();
        } catch (error) { console.error(`Failed to ${action} item:`, error); }
        finally { buttonToUpdate.disabled = false; buttonToUpdate.innerHTML = originalButtonText; otherButton.disabled = false; }
    }
    if(modalApproveBtn) modalApproveBtn.addEventListener('click', () => handleModeration('approve'));
    if(modalRejectBtn) modalRejectBtn.addEventListener('click', () => handleModeration('reject'));

    // --- "Add New Item" Modal Logic ---
    document.querySelectorAll('.add-new-btn').forEach(button => {
        button.addEventListener('click', () => {
            currentAddItemType = button.dataset.itemType;
            openAddNewModal(currentAddItemType);
        });
    });

    function createFormField(labelText, inputType, inputName, inputId, isRequired = false, placeholder = '') {
        const fieldDiv = document.createElement('div');
        fieldDiv.classList.add('modal-form-field');
        const label = document.createElement('label');
        label.setAttribute('for', inputId);
        label.textContent = labelText;
        let inputElement;
        if (inputType === 'textarea') {
            inputElement = document.createElement('textarea');
        } else {
            inputElement = document.createElement('input');
            inputElement.type = inputType;
        }
        inputElement.id = inputId;
        inputElement.name = inputName; // This name attribute is crucial for FormData
        if (placeholder) inputElement.placeholder = placeholder;
        if (isRequired) inputElement.required = true;
        fieldDiv.appendChild(label);
        fieldDiv.appendChild(inputElement);
        return fieldDiv;
    }

    function openAddNewModal(itemType) {
        addNewModalTitle.textContent = `Add New Verified ${capitalizeFirstLetter(itemType.replace('-', ' '))}`;
        addNewItemForm.innerHTML = ''; // Clear previous form fields
        addNewItemForm.dataset.itemType = itemType;

        // Common Fields (IDs are now unique per call due to itemType prefix)
        let titleLabel = "Title/Name:";
        let titleName = "title";
        if (itemType === 'career-fair' || itemType === 'hackathon') {
            titleName = "name";
        }
        addNewItemForm.appendChild(createFormField(titleLabel, 'text', titleName, `add-${itemType}-title`, true));
        addNewItemForm.appendChild(createFormField('Description:', 'textarea', 'description', `add-${itemType}-description`));
        addNewItemForm.appendChild(createFormField('Website URL:', 'url', 'url', `add-${itemType}-url`, false, 'https://example.com'));

        let dateLabel = "Start Date:";
        let dateName = "start_date";
        if (itemType === 'job') {
            dateLabel = "Date Posted:";
            dateName = "date_posted";
        }
        addNewItemForm.appendChild(createFormField(dateLabel, 'date', dateName, `add-${itemType}-date`));

        // Type-specific fields
        if (itemType === 'job') {
            addNewItemForm.appendChild(createFormField('Company:', 'text', 'company', `add-${itemType}-company`));
            addNewItemForm.appendChild(createFormField('Location:', 'text', 'location', `add-${itemType}-location`));
            addNewItemForm.appendChild(createFormField('Salary:', 'text', 'salary', `add-${itemType}-salary`));
            addNewItemForm.appendChild(createFormField('Type (e.g., Full-time):', 'text', 'type', `add-${itemType}-type`));
            addNewItemForm.appendChild(createFormField('Experience:', 'text', 'experience', `add-${itemType}-experience`));
            addNewItemForm.appendChild(createFormField('Image URL:', 'url', 'imageUrl', `add-${itemType}-imageUrl`, false, 'https://example.com/image.png'));
        } else if (itemType === 'internship') {
            addNewItemForm.appendChild(createFormField('Company:', 'text', 'company', `add-${itemType}-company`));
            addNewItemForm.appendChild(createFormField('Location:', 'text', 'location', `add-${itemType}-location`)); // Added location
            addNewItemForm.appendChild(createFormField('End Date:', 'date', 'end_date', `add-${itemType}-end-date`));
        } else if (itemType === 'career-fair') {
            addNewItemForm.appendChild(createFormField('Location:', 'text', 'location', `add-${itemType}-location`));
        } else if (itemType === 'hackathon') {
            addNewItemForm.appendChild(createFormField('Location:', 'text', 'location', `add-${itemType}-location`));
            addNewItemForm.appendChild(createFormField('Theme:', 'text', 'theme', `add-${itemType}-theme`));
            addNewItemForm.appendChild(createFormField('Prize Pool:', 'text', 'prize_pool', `add-${itemType}-prize`));
        }
        
        addNewModalOverlay.style.display = 'flex';
        setTimeout(() => addNewModalOverlay.classList.add('active'), 10);
    }

    function closeAddNewModal() {
        addNewModalOverlay.classList.remove('active');
        setTimeout(() => {
            addNewModalOverlay.style.display = 'none';
            if (addNewItemForm) addNewItemForm.reset();
        }, 300);
        currentAddItemType = null;
    }
    if(addModalCancelBtn) addModalCancelBtn.addEventListener('click', closeAddNewModal);
    if(addNewModalOverlay) addNewModalOverlay.addEventListener('click', (e) => { if (e.target === addNewModalOverlay) closeAddNewModal(); });

    if(addNewItemForm) {
        addNewItemForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const submitButton = document.getElementById('add-modal-submit-btn');
            if (!submitButton) { console.error("Add item submit button not found"); return; }
            const originalButtonText = submitButton.innerHTML;
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';

            const formData = new FormData(this);
            const itemData = {};
            formData.forEach((value, key) => { itemData[key] = value.trim() === '' ? null : value; });
            const itemType = this.dataset.itemType;

            try {
                const result = await apiCall(`/api/admin/${itemType}s`, 'POST', itemData); // e.g., /api/admin/jobs
                alert(result.message || `${capitalizeFirstLetter(itemType)} added successfully!`);
                closeAddNewModal();
            } catch (error) { alert(`Failed to add ${itemType}: ${escapeHtml(error.message)}`); }
            finally { submitButton.disabled = false; submitButton.innerHTML = originalButtonText; }
        });
    }

    // --- Search Logic ---
    function performSearch() {
        const searchTerm = submissionSearchInput.value.trim();
        allItemTypes.forEach(type => loadUnverifiedItems(type, searchTerm));
    }
    if(submissionSearchButton) submissionSearchButton.addEventListener('click', performSearch);
    if(submissionSearchInput) {
        submissionSearchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { e.preventDefault(); performSearch(); } });
        let searchDebounceTimer;
        submissionSearchInput.addEventListener('input', () => {
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                const searchTerm = submissionSearchInput.value.trim();
                if (searchTerm.length === 0 || searchTerm.length >= 2) performSearch();
            }, 500);
        });
    }

    // --- Initial Load ---
    console.log("Loading all unverified items on page load...");
    allItemTypes.forEach(type => loadUnverifiedItems(type));
});