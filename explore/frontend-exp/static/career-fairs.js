// static/career-fairs.js

// Handle card clicks for career fairs
document.querySelectorAll('.fair-item').forEach(item => {
    item.addEventListener('click', () => {
        const fairData = JSON.parse(item.getAttribute('data-fair'));
        const popupDescription = document.getElementById('popup-description');
        popupDescription.innerHTML = `
            <h3>${fairData.name} - Description</h3>
            <p>${fairData.description}</p>
        `;
        popupDescription.style.display = 'block';

        // Hide pop-up when mouse leaves the pop-up
        popupDescription.addEventListener('mouseleave', () => {
            popupDescription.style.display = 'none';
        });
    });
});

// Handle card clicks for job listings
document.querySelectorAll('.job-item').forEach(item => {
    item.addEventListener('click', () => {
        const jobData = JSON.parse(item.getAttribute('data-job'));
        const popupDescription = document.getElementById('popup-description');
        popupDescription.innerHTML = `
            <h3>${jobData.posting} - Details</h3>
            <p>Company: ${jobData.company}</p>
            <p>Location: ${jobData.location}</p>
            <p>Interview/Hackathon: ${jobData.interviewDate || jobData.hackathonDate}</p>
            <p>Responsibilities: ${jobData.responsibilities}</p>
            <p>Prerequisites: ${jobData.prerequisites}</p>
        `;
        popupDescription.style.display = 'block';

        // Hide pop-up when mouse leaves the pop-up
        popupDescription.addEventListener('mouseleave', () => {
            popupDescription.style.display = 'none';
        });
    });
});

// Search functionality (dummy for now)
document.getElementById('search-button').addEventListener('click', () => {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    // In a real scenario, you would filter the data here
    alert(`Search for: ${searchTerm}`);
});

// Upcoming fairs filter (dummy for now)
document.getElementById('upcoming-button').addEventListener('click', () => {
    // In a real scenario, you would filter the data here
    alert('Displaying upcoming fairs...');
});