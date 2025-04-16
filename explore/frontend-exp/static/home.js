function navigateTo(url) {
    window.location.href = url;
}

const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const searchResultsList = searchResults.querySelector('ul');
let searchHistory = JSON.parse(localStorage.getItem('searchHistory')) || [];
let currentUser = 'user123'; // Replace with actual user ID.  You'd get this from your auth system.


searchInput.addEventListener('input', () => {
    const searchTerm = searchInput.value.toLowerCase();
    fetch(`/api/search?term=${searchTerm}`) // Assuming you have an API endpoint for search
        .then(response => response.json())
        .then(results => {
            displayResults(results);
            searchResults.style.display = results.length > 0 ? 'block' : 'none';
        })
        .catch(error => {
            console.error('Error fetching search results:', error);
            searchResults.style.display = 'none'; // Hide results on error as well
        });
});

function displayResults(results) {
    searchResultsList.innerHTML = '';
    if (results && Array.isArray(results)) { // Check if results is valid
        results.forEach(result => {
            const li = document.createElement('li');
            li.textContent = result.name; // Assuming your search results have a 'name' field
            li.addEventListener('click', () => {
                searchInput.value = result.name;
                searchResults.style.display = 'none';
                addToSearchHistory(currentUser, result.name); // Pass the user ID
            });
            searchResultsList.appendChild(li);
        });
    } else {
        searchResultsList.innerHTML = '<li>No results found</li>';
    }
}

function addToSearchHistory(userId, searchTerm) {
    // In this version, we're using a server-side database, so we send an API request.
    fetch('/api/search-history', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId, searchTerm }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to save search history');
        }
        return response.json();
    })
    .then(data => {
        console.log('Search term saved:', data);
        // Optionally, you could update the UI to show the saved term, but it's not strictly necessary here.
    })
    .catch(error => {
        console.error('Error saving search term:', error);
        alert('Failed to save search term.  Please try again.'); // Inform the user.
    });
}

document.addEventListener('click', (event) => {
    if (!event.target.closest('.search-bar-container')) {
        searchResults.style.display = 'none';
    }
});

function viewSearchHistory() {
    fetch(`/api/search-history/${currentUser}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to retrieve search history');
            }
            return response.json();
        })
        .then(history => {
            if (history && history.length > 0) {
                const historyItems = history.map(item => item.searchTerm).join('\n');
                alert("Search History:\n" + historyItems);
            } else {
                alert("Your search history is empty.");
            }
        })
        .catch(error => {
            console.error('Error retrieving search history:', error);
            alert("Failed to retrieve search history.");
        });
}


// Fetch Today's Feed
fetch('/api/todays-feed')
    .then(response => response.json())
    .then(data => {
        if (data && data.question) { // Check if data and data.question are valid
            document.getElementById('dailySparkContent').innerHTML = `<p><strong>Daily Spark Question:</strong> ${data.data.question}</p>`;
        } else {
            document.getElementById('dailySparkContent').innerHTML = `<p>No daily spark question available today.</p>`;
        }
    })
    .catch(error => {
        console.error('Error fetching today\'s feed:', error);
        document.getElementById('dailySparkContent').innerHTML = `<p>Failed to load daily spark question.</p>`;
    });

// Fetch Upcoming Events
fetch('/api/events')
    .then(response => response.json())
    .then(events => {
        const eventList = document.getElementById('eventList');
        eventList.innerHTML = ''; // Clear previous content
        if (events && Array.isArray(events)) { //check if events is valid
            events.forEach(event => {
                const eventCard = document.createElement('div');
                eventCard.className = 'event-card';
                eventCard.innerHTML = `<h3>${event.name}</h3><p>${event.data.description}</p>`;
                eventList.appendChild(eventCard);
            });
        } else {
            eventList.innerHTML = `<p>No upcoming events found.</p>`;
        }
    })
    .catch(error => {
        console.error('Error fetching events:', error);
        document.getElementById('eventList').innerHTML = `<p>Failed to load events.</p>`;
    });

// Fetch Features
fetch('/api/features')
    .then(response => response.json())
    .then(features => {
        const featuresContainer = document.getElementById('featuresContainer');
        featuresContainer.innerHTML = ''; // Clear previous content.
        if (features && Array.isArray(features)) { // Check if features is an array
            features.forEach(feature => {
                const featureElement = document.createElement('div');
                featureElement.className = 'feature';
                featureElement.onclick = () => navigateTo(feature.url); // Assuming each feature has a 'url'
                featureElement.innerHTML = `<i class="${feature.icon}"></i><h3>${feature.name}</h3><p>${feature.description}</p>`;
                featuresContainer.appendChild(featureElement);
            });
        } else {
            console.warn('/api/features did not return an array:', features);
            featuresContainer.innerHTML = `<p>Failed to load features.</p>`;
        }
    })
    .catch(error => {
        console.error('Error fetching features:', error);
        document.getElementById('featuresContainer').innerHTML = `<p>Failed to load features.</p>`;
    });
