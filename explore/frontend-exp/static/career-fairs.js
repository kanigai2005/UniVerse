// Get references to the search input and button for career fairs
const careerFairSearchInput = document.getElementById('search-input');
const careerFairSearchButton = document.getElementById('search-button');
// Get a reference to the career fair list
const careerFairsList = document.getElementById('career-fairs-list');

// Handle job submission
document.getElementById('job-listing-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const job = {
        title: document.getElementById('job-title').value,
        company: document.getElementById('job-company').value,
        location: document.getElementById('job-location').value,
        datePosted: document.getElementById('job-post-date').value,
        description: document.getElementById('job-description').value,
        salary: document.getElementById('job-salary').value,
        type: document.getElementById('job-type').value,
        experience: document.getElementById('job-experience').value,
        imageUrl: document.getElementById('job-image-url').value,
        link: document.getElementById('job-link').value
    };

    try {
        const response = await fetch('/add-job', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(job)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const responseData = await response.json();
        //job.id = responseData.id;  //  no longer needed, handled on backend
        //job.created_at = responseData.created_at;
        //job.updated_at = responseData.updated_at;

    } catch (error) {
        console.error('Error submitting job:', error);
        alert('Failed to submit job listing. Please check the console for details.');
        return; // Stop execution on error
    }

    // Reset form after submission
    document.getElementById('job-listing-form').reset();
    alert('Job listing submitted for review.');
});

// Handle career fair submission
document.getElementById('career-fair-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const fair = {
        name: document.getElementById('cf-name').value,
        location: document.getElementById('cf-location').value,
        date: document.getElementById('cf-date').value,
        description: document.getElementById('cf-description').value,
        link: document.getElementById('cf-link').value
    };

    try {
        const response = await fetch('/add-careerfair', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(fair)
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const responseData = await response.json();
        // fair.id = responseData.id;  // no longer needed, handled on backend
        // fair.created_at = responseData.created_at;
        // fair.updated_at = responseData.updated_at;

    } catch (error) {
        console.error('Error submitting career fair:', error);
        alert('Failed to submit career fair. Please check the console for details.');
        return;
    }

    // Reset form after submission
    document.getElementById('career-fair-form').reset();
    alert('Career fair submitted for review.');
});

// Career fair search functionality
careerFairSearchButton.addEventListener('click', () => {
    const searchTerm = careerFairSearchInput.value.toLowerCase();

    // Get all career fair list items
    const careerFairItems = careerFairsList.getElementsByTagName('li');

    // Loop through the list items and hide/show based on the search term
    for (let i = 0; i < careerFairItems.length; i++) {
        const listItemText = careerFairItems[i].textContent.toLowerCase();
        if (listItemText.includes(searchTerm)) {
            careerFairItems[i].style.display = ''; // Show the item
        } else {
            careerFairItems[i].style.display = 'none'; // Hide the item
        }
    }
});