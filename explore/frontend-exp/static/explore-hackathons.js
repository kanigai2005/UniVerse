const hackathonSearchInput = document.getElementById('hackathon-search-input');
const hackathonSearchButton = document.getElementById('hackathon-search-button');
const hackathonForm = document.getElementById('hackathon-form');
const currentHackathonsList = document.getElementById('current-hackathons-list');
const hackathonDetailsModal = document.getElementById('hackathon-details-modal');
const modalCloseBtn = document.querySelector('.close-modal');
const modalTitle = document.querySelector('.modal-header h2');
const modalBody = document.querySelector('.modal-body p');
const modalRegisterBtn = document.querySelector('.hackathon-register-btn');


let hackathons = []; // Store fetched hackathons


// Function to fetch hackathons from the API
async function fetchHackathons() {
    try {
        const response = await fetch('/api/hackathons'); // Use the correct API endpoint
        if (!response.ok) {
            throw new Error(`Failed to fetch hackathons: ${response.status}`);
        }
        const data = await response.json();
        hackathons = data; // Store fetched data
        renderHackathons(); // Render the list
    } catch (error) {
        console.error('Error fetching hackathons:', error);
        alert('Failed to load hackathons. Please check console for errors.');
    }
}

// Function to render hackathons list
function renderHackathons() {
    currentHackathonsList.innerHTML = ''; // Clear previous content
    hackathons.forEach(hackathon => {
        const listItem = document.createElement('li');
        listItem.classList.add('hackathon-card');
        listItem.innerHTML = `
            <h2 class="hackathon-name">${hackathon.name}</h2>
            <p class="hackathon-date">Date: ${new Date(hackathon.date).toLocaleDateString()}</p>
            <p class="hackathon-location">Location: ${hackathon.location}</p>
            <p class="hackathon-description">${hackathon.description}</p>
            <a href="${hackathon.url}" class="hackathon-register-btn" target="_blank" rel="noopener noreferrer">Register Now</a>
        `;
        listItem.addEventListener('click', () => showHackathonDetails(hackathon.id));
        currentHackathonsList.appendChild(listItem);
    });
}

// Function to show hackathon details in modal
function showHackathonDetails(hackathonId) {
    const hackathon = hackathons.find(h => h.id === hackathonId);
    if (hackathon) {
        modalTitle.textContent = hackathon.name;
        modalBody.textContent = hackathon.description;
        modalRegisterBtn.href = hackathon.url;
        hackathonDetailsModal.style.display = 'flex';
    }
}

// Event listener for closing the modal
modalCloseBtn.addEventListener('click', () => {
    hackathonDetailsModal.style.display = 'none';
});

// Event listener for clicking outside the modal
window.addEventListener('click', (event) => {
    if (event.target === hackathonDetailsModal) {
        hackathonDetailsModal.style.display = 'none';
    }
});



// Handle hackathon submission
hackathonForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const hackathon = {
        name: document.getElementById('hackathon-name').value,
        location: document.getElementById('hackathon-location').value,
        date: document.getElementById('hackathon-date').value,
        link: document.getElementById('hackathon-link').value,
        description: document.getElementById('hackathon-description').value,
        theme: document.getElementById('hackathon-theme').value,
        prize_pool: document.getElementById('hackathon-prize_pool').value,
        url: document.getElementById('hackathon-link').value,
    };

    try {
        const response = await fetch('/api/hackathons/unverified', { // Use the correct API endpoint
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(hackathon)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to add hackathon: ${response.status} - ${errorText}`);
        }

        // Reset form after submission
        hackathonForm.reset();
        alert('Hackathon submitted for review.');
        await fetchHackathons(); //refresh the list

    } catch (error) {
        console.error('Error adding hackathon:', error);
        alert('Failed to submit hackathon. Please check console for errors.');
    }
});

hackathonSearchButton.addEventListener('click', () => {
    const searchTerm = hackathonSearchInput.value.toLowerCase();
    const filteredHackathons = hackathons.filter(hackathon =>
        hackathon.name.toLowerCase().includes(searchTerm) ||
        hackathon.location.toLowerCase().includes(searchTerm)
    );
    hackathons = filteredHackathons;
    renderHackathons();
});

// Fetch hackathons on page load
fetchHackathons();
