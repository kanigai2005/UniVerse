// static/career-fairs.js

// Function to fetch and display career fairs
async function loadCareerFairs() {
    try {
        const response = await fetch("http://127.0.0.1:8000/career_fairs");
        if (!response.ok) {
            throw new Error("Failed to fetch career fairs");
        }
        const fairs = await response.json();
        const container = document.getElementById("career-fairs-list");

        container.innerHTML = ""; // Clear existing content

        fairs.forEach(fair => {
            const fairItem = document.createElement("li");
            fairItem.classList.add("fair-item");
            fairItem.setAttribute("data-fair", JSON.stringify(fair));
            fairItem.innerHTML = `
                <h3>${fair.name}</h3>
                <p>Venue: ${fair.location}</p>
                <p>Date: ${fair.date}</p>
            `;
            container.appendChild(fairItem);
        });
        addCareerFairClickListeners();

    } catch (error) {
        console.error("Error loading career fairs:", error);
    }
}

// Function to fetch and display job listings
async function loadJobs() {
    try {
        const response = await fetch("http://127.0.0.1:8000/internships");
        if (!response.ok) {
            throw new Error("Failed to fetch jobs");
        }
        const jobs = await response.json();
        const container = document.getElementById("job-listings-list");

        container.innerHTML = ""; // Clear existing content

        jobs.forEach(job => {
            const jobItem = document.createElement("li");
            jobItem.classList.add("job-item");
            jobItem.setAttribute("data-job", JSON.stringify(job));
            jobItem.innerHTML = `
                <h3>${job.role}</h3>
                <p>Company: ${job.company}</p>
                <p>Location: ${job.location}</p>
            `;
            container.appendChild(jobItem);
        });
        addJobClickListeners();

    } catch (error) {
        console.error("Error loading jobs:", error);
    }
}

// Function to add click listeners to career fair items
function addCareerFairClickListeners() {
    document.querySelectorAll('.fair-item').forEach(item => {
        item.addEventListener('click', () => {
            const fairData = JSON.parse(item.getAttribute('data-fair'));
            const popupDescription = document.getElementById('popup-description');
            popupDescription.innerHTML = `
                <h3>${fairData.name} - Description</h3>
                <p>${fairData.description}</p>
            `;
            popupDescription.style.display = 'block';

            popupDescription.addEventListener('mouseleave', () => {
                popupDescription.style.display = 'none';
            });
        });
    });
}

// Function to add click listeners to job items
function addJobClickListeners() {
    document.querySelectorAll('.job-item').forEach(item => {
        item.addEventListener('click', () => {
            const jobData = JSON.parse(item.getAttribute('data-job'));
            const popupDescription = document.getElementById('popup-description');
            popupDescription.innerHTML = `
                <h3>${jobData.role} - Details</h3>
                <p>Company: ${jobData.company}</p>
                <p>Location: ${jobData.location}</p>
                <p>Link: <a href="${jobData.link}" target="_blank">Apply Here</a></p>
                <p>Requirements: ${jobData.requirements}</p>
            `;
            popupDescription.style.display = 'block';

            popupDescription.addEventListener('mouseleave', () => {
                popupDescription.style.display = 'none';
            });
        });
    });
}

// Search functionality (dummy for now)
document.getElementById('search-button').addEventListener('click', () => {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    alert(`Search for: ${searchTerm}`);
});

// Upcoming fairs filter (dummy for now)
document.getElementById('upcoming-button').addEventListener('click', () => {
    alert('Displaying upcoming fairs...');
});

document.addEventListener('DOMContentLoaded', ()=>{
    loadCareerFairs();
    loadJobs();
});