
function navigateTo(url) {
    window.location.href = url;
}

const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const searchResultsList = searchResults.querySelector('ul');
let searchHistory = JSON.parse(localStorage.getItem('searchHistory')) || [];

searchInput.addEventListener('input', () => {
    const searchTerm = searchInput.value.toLowerCase();
    fetch(`/api/search?term=${searchTerm}`) // Assuming you have an API endpoint for search
        .then(response => response.json())
        .then(results => {
            displayResults(results);
            searchResults.style.display = results.length > 0 ? 'block' : 'none';
        })
        .catch(error => console.error('Error fetching search results:', error));
});

function displayResults(results) {
    searchResultsList.innerHTML = '';
    results.forEach(result => {
        const li = document.createElement('li');
        li.textContent = result.name; // Assuming your search results have a 'name' field
        li.addEventListener('click', () => {
            searchInput.value = result.name;
            searchResults.style.display = 'none';
            addToSearchHistory(result.name);
        });
        searchResultsList.appendChild(li);
    });
}

function addToSearchHistory(item) {
    if (!searchHistory.includes(item)) {
        searchHistory.push(item);
        if (searchHistory.length > 5) {
            searchHistory.shift();
        }
        localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    }
}

document.addEventListener('click', (event) => {
    if (!event.target.closest('.search-bar-container')) {
        searchResults.style.display = 'none';
    }
});

function viewSearchHistory() {
    const storedHistory = localStorage.getItem('searchHistory');
    let historyArray = storedHistory ? JSON.parse(storedHistory) : [];
    if (historyArray.length > 0) {
        alert("Search History:\n" + historyArray.join('\n'));
    } else {
        alert("Your search history is empty.");
    }
}

// Fetch Today's Feed
fetch('/api/todays-feed')
    .then(response => response.json())
    .then(data => {
        document.getElementById('dailySparkContent').innerHTML = `<p><strong>Daily Spark Question:</strong> ${data.question}</p>`;
    })
    .catch(error => console.error('Error fetching today\'s feed:', error));

// Fetch Upcoming Events
fetch('/api/events')
    .then(response => response.json())
    .then(events => {
        const eventList = document.getElementById('eventList');
        events.forEach(event => {
            const eventCard = document.createElement('div');
            eventCard.className = 'event-card';
            eventCard.innerHTML = `<h3>${event.name}</h3><p>${event.description}</p>`;
            eventList.appendChild(eventCard);
        });
    })
    .catch(error => console.error('Error fetching events:', error));

// Fetch Features
fetch('/api/features')
    .then(response => response.json())
    .then(features => {
        const featuresContainer = document.getElementById('featuresContainer');
        features.forEach(feature => {
            const featureElement = document.createElement('div');
            featureElement.className = 'feature';
            featureElement.onclick = () => navigateTo(feature.url); // Assuming each feature has a 'url'
            featureElement.innerHTML = `<i class="${feature.icon}"></i><h3>${feature.name}</h3><p>${feature.description}</p>`;
            featuresContainer.appendChild(featureElement);
        });
    })
    .catch(error => console.error('Error fetching features:', error));
    