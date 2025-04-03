// static/explore-hackathons.js

let allHackathons = Array.from(document.querySelectorAll('.hackathon-item')).map(item => {
    return {
        element: item,
        data: JSON.parse(item.getAttribute('data-hackathon'))
    };
});

// Handle card clicks for hackathons
document.querySelectorAll('.hackathon-item').forEach(item => {
    item.addEventListener('click', () => {
        const hackathonData = JSON.parse(item.getAttribute('data-hackathon'));
        const popupDescription = document.getElementById('popup-description');
        popupDescription.innerHTML = `
            <h3>${hackathonData.name} - Description</h3>
            <p>${hackathonData.description}</p>
        `;
        popupDescription.style.display = 'block';

        // Hide pop-up when mouse leaves the pop-up
        popupDescription.addEventListener('mouseleave', () => {
            popupDescription.style.display = 'none';
        });
    });
});

// Search functionality
document.getElementById('search-button').addEventListener('click', () => {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    allHackathons.forEach(hackathon => {
        const name = hackathon.data.name.toLowerCase();
        const location = hackathon.data.location.toLowerCase();
        if (name.includes(searchTerm) || location.includes(searchTerm)) {
            hackathon.element.style.display = 'block';
        } else {
            hackathon.element.style.display = 'none';
        }
    });
});