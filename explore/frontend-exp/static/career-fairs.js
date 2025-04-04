async function loadCareerOffersAndJobs() {
    try {
        const careerFairsResponse = await fetch("/api/career-fairs");
        const jobListingsResponse = await fetch("/api/internship"); // Assuming "internships" for job listings

        if (!careerFairsResponse.ok || !jobListingsResponse.ok) {
            throw new Error("Failed to fetch data");
        }

        const careerFairs = await careerFairsResponse.json();
        const jobListings = await jobListingsResponse.json();
        const fairsList = document.getElementById("career-fairs-list");
        const jobsList = document.getElementById("job-listings-list");

        fairsList.innerHTML = ""; // Clear existing content
        jobsList.innerHTML = "";  // Clear existing content

        // Display Career Fairs
        careerFairs.forEach(fair => {
            const fairItem = document.createElement("li");
            fairItem.classList.add("fair-item");
            fairItem.innerHTML = `
                <h3>${fair.name}</h3>
                <p>Date: ${fair.date}</p>
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
                <p>Start Date: ${job.start_date}</p>
                <p>End Date: ${job.end_date}</p>
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

    fairsList.addEventListener('click', (event) => {
        const fairItem = event.target.closest('.fair-item');
        if (fairItem) {
            const fairData = JSON.parse(fairItem.getAttribute('data-fair'));
            showPopup(fairData.description);
        }
    });

    jobsList.addEventListener('click', (event) => {
        const jobItem = event.target.closest('.job-item');
        if (jobItem) {
            const jobData = JSON.parse(jobItem.getAttribute('data-job'));
            showPopup(jobData.description);
        }
    });
}

function showPopup(description) {
    const popup = document.getElementById('popup-description');
    popup.innerHTML = `<p>${description}</p>`;
    popup.style.display = 'block';

    popup.addEventListener('mouseleave', () => {
        popup.style.display = 'none';
    }, { once: true });
}

function addSearchAndFilter() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const upcomingButton = document.getElementById('upcoming-button');

    searchButton.addEventListener('click', () => {
        const searchTerm = searchInput.value.toLowerCase();
        filterItems(searchTerm);
    });

    upcomingButton.addEventListener('click', () => {
        filterUpcomingFairs();
    });
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

    fairItems.forEach(item => {
        const fairData = JSON.parse(item.getAttribute('data-fair'));
        const fairDate = new Date(fairData.date);
        item.style.display = fairDate >= today ? 'block' : 'none';
    });
}

document.addEventListener("DOMContentLoaded", loadCareerOffersAndJobs);