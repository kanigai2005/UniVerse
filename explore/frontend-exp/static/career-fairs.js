// static/career-fairs.js
async function loadCareerOffersAndJobs() {
    try {
        const careerFairsResponse = await fetch("/api/career_fairs");
        const jobListingsResponse = await fetch("/api/internships");

        if (!careerFairsResponse.ok || !jobListingsResponse.ok) {
            throw new Error("Failed to fetch data");
        }

        const careerFairs = await careerFairsResponse.json();
        const jobListings = await jobListingsResponse.json();

        console.log("Career Fairs Response:", careerFairs); // Debug log
        console.log("Job Listings Response:", jobListings); // Debug log

        const fairsList = document.getElementById("career-fairs-list");
        const jobsList = document.getElementById("job-listings-list");

        fairsList.innerHTML = ""; // Clear existing content
        jobsList.innerHTML = "";   // Clear existing content

        // Display Career Fairs
        careerFairs.forEach(fair => {
            const fairItem = document.createElement("li");
            fairItem.classList.add("fair-item");
            fairItem.innerHTML = `
                <h3>${fair.name}</h3>
                <p>Date: ${new Date(fair.date).toLocaleDateString()}</p>
                <p>Location: ${fair.location}</p>
            `;
            fairItem.setAttribute('data-fair', JSON.stringify(fair)); // Store fair data for popup
            fairsList.appendChild(fairItem);
        });

        // Display Job Listings
        jobListings.forEach(job => {
            const jobItem = document.createElement("li");
            jobItem.classList.add("job-item");
            jobItem.innerHTML = `
                <h3>${job.title}</h3>
                <p>Company: ${job.company}</p>
                <p>Start Date: ${new Date(job.start_date).toLocaleDateString()}</p>
                <p>End Date: ${new Date(job.end_date).toLocaleDateString()}</p>
            `;
            jobItem.setAttribute('data-job', JSON.stringify(job)); // Store job data for popup
            jobsList.appendChild(jobItem);
        });

        addClickListeners();
        addSearchAndFilter();

    } catch (error) {
        console.error("Error loading data:", error);
        document.getElementById("career-fairs-list").innerHTML = "<p>Error loading data. Please try again later.</p>";
        document.getElementById("job-listings-list").innerHTML = "<p>Error loading data. Please try again later.</p>";
    }
}

function addClickListeners() {
    const fairsList = document.getElementById("career-fairs-list");
    const jobsList = document.getElementById("job-listings-list");
    const popupDescription = document.getElementById('popup-description');

    if (fairsList && popupDescription) {
        fairsList.addEventListener('click', (event) => {
            const fairItem = event.target.closest('.fair-item');
            if (fairItem) {
                const fairData = JSON.parse(fairItem.getAttribute('data-fair'));
                popupDescription.innerHTML = `
                    <h3>${fairData.name} - Details</h3>
                    <p>Date: ${new Date(fairData.date).toLocaleDateString()}</p>
                    <p>Location: ${fairData.location}</p>
                    <p>Description: ${fairData.description || 'No description available.'}</p>
                `;
                popupDescription.style.display = 'block';
            }
        });
    }

    if (jobsList && popupDescription) {
        jobsList.addEventListener('click', (event) => {
            const jobItem = event.target.closest('.job-item');
            if (jobItem) {
                const jobData = JSON.parse(jobItem.getAttribute('data-job'));
                popupDescription.innerHTML = `
                    <h3>${jobData.title} - Details</h3>
                    <p>Company: ${jobData.company}</p>
                    <p>Start Date: ${new Date(jobData.start_date).toLocaleDateString()}</p>
                    <p>End Date: ${new Date(jobData.end_date).toLocaleDateString()}</p>
                    <p>Description: ${jobData.description || 'No description available.'}</p>
                `;
                popupDescription.style.display = 'block';
            }
        });
    }

    if (popupDescription) {
        popupDescription.addEventListener('mouseleave', () => {
            popupDescription.style.display = 'none';
        }, { once: true });
    }
}

function addSearchAndFilter() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const upcomingButton = document.getElementById('upcoming-button');

    if (searchButton) {
        searchButton.addEventListener('click', () => {
            const searchTerm = searchInput.value.toLowerCase();
            filterItems(searchTerm);
        });
    }

    if (upcomingButton) {
        upcomingButton.addEventListener('click', () => {
            filterUpcomingFairs();
        });
    }
}

function filterItems(searchTerm) {
    const fairItems = document.querySelectorAll('#career-fairs-list .fair-item');
    const jobItems = document.querySelectorAll('#job-listings-list .job-item');

    fairItems.forEach(item => {
        const itemText = item.textContent.toLowerCase();
        item.style.display = itemText.includes(searchTerm) ? 'block' : 'none';
    });

    jobItems.forEach(item => {
        const itemText = item.textContent.toLowerCase();
        item.style.display = itemText.includes(searchTerm) ? 'block' : 'none';
    });
}

function filterUpcomingFairs() {
    const fairItems = document.querySelectorAll('#career-fairs-list .fair-item');
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Normalize today's date

    fairItems.forEach(item => {
        const fairData = JSON.parse(item.getAttribute('data-fair'));
        const fairDate = new Date(fairData.date);
        fairDate.setHours(0, 0, 0, 0); // Normalize fair date
        item.style.display = fairDate >= today ? 'block' : 'none';
    });
}

document.addEventListener("DOMContentLoaded", loadCareerOffersAndJobs);