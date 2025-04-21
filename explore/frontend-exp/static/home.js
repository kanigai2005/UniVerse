function navigateTo(url) {
    window.location.href = url;
}

const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const searchResultsList = searchResults.querySelector('ul');
let searchHistory = JSON.parse(localStorage.getItem('searchHistory')) || [];
let currentUser = 'user123'; // Replace with actual user ID. You'd get this from your auth system.

document.addEventListener('DOMContentLoaded', () => {
    const profileLink = document.querySelector('.top-nav a[href="profile.html"]');
    const loggedInUserName = localStorage.getItem('username');

    if (profileLink) {
        if (loggedInUserName) {
            profileLink.href = `/profile.html?username=${encodeURIComponent(loggedInUserName)}`;
        } else {
            // If no username, you might want to disable the link or redirect to login
            profileLink.href = '/login.html'; // Or your login page URL
        }
    } else {
        console.error('Profile link not found in the top navigation.');
    }
});

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
        alert('Failed to save search term. Please try again.'); // Inform the user.
    });
}

document.addEventListener('click', (event) => {
    if (!event.target.closest('.search-bar-container')) {
        searchResults.style.display = 'none';
    }
});

function viewSearchHistory() {
    const searchHistoryListContainer = document.getElementById('searchHistoryListContainer');
    if (!searchHistoryListContainer) {
        console.error('Search history container not found in HTML.');
        return;
    }
    searchHistoryListContainer.innerHTML = ''; // Clear previous history

    fetch(`/api/search-history/${currentUser}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to retrieve search history: ${response.status}`);
            }
            return response.json();
        })
        .then(history => {
            console.log('Search History Data:', history); // **Crucial: Inspect the data**
            if (history && Array.isArray(history)) {
                const ul = document.createElement('ul');
                history.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = item.searchTerm; // **Assuming 'searchTerm' is the correct property**
                    ul.appendChild(li);
                });
                searchHistoryListContainer.appendChild(ul);
                searchHistoryListContainer.style.display = 'block'; // Show the container
            } else {
                searchHistoryListContainer.innerHTML = '<p>Your search history is empty.</p>';
                searchHistoryListContainer.style.display = 'block'; // Show the container
            }
        })
        .catch(error => {
            console.error('Error retrieving search history:', error);
            searchHistoryListContainer.innerHTML = `<p>Failed to retrieve search history: ${error.message}</p>`;
            searchHistoryListContainer.style.display = 'block'; // Show the container
        });
}

// Fetch Upcoming Events
fetch('/api/events')
    .then(response => response.json())
    .then(events => {
        console.log('Events Data:', events); // For debugging
        const eventList = document.getElementById('eventList');
        if (eventList) {
            eventList.innerHTML = ''; // Clear previous content
            if (events && Array.isArray(events)) {
                events.forEach(event => {
                    const eventCard = document.createElement('div');
                    eventCard.className = 'event-card';
                    let eventName = 'Upcoming Event'; // Default title
                    if (event && typeof event === 'object') {
                        if (event.hasOwnProperty('name')) {
                            eventName = event.name;
                        } else if (event.hasOwnProperty('title')) { // Check for 'title' as an alternative
                            eventName = event.title;
                        } else if (event.data && typeof event.data === 'object' && event.data.hasOwnProperty('name')) { // Check nested 'data.name'
                            eventName = event.data.name;
                        } else if (event.data && typeof event.data === 'object' && event.data.hasOwnProperty('title')) { // Check nested 'data.title'
                            eventName = event.data.title;
                        } else {
                            console.warn('Event object is missing a recognizable title property:', event);
                        }
                    } else {
                        console.warn('Invalid event object:', event);
                    }
                    const eventDescription = event.data && event.data.description ? event.data.description : 'No description available.';
                    eventCard.innerHTML = `<h3>${eventName}</h3><p>${eventDescription}</p>`;
                    eventList.appendChild(eventCard);
                });
            } else {
                eventList.innerHTML = `<p>No upcoming events found.</p>`;
            }
        } else {
            console.error('Element with ID "eventList" not found.');
        }
    })
    .catch(error => {
        console.error('Error fetching events:', error);
        const eventList = document.getElementById('eventList');
        if (eventList) {
            eventList.innerHTML = `<p>Failed to load events.</p>`;
        }
    });

// Fetch Today's Feed
fetch('/api/todays-feed')
    .then(response => response.json())
    .then(data => {
        console.log('Daily Spark Data:', data); // For debugging
        const dailySparkContent = document.getElementById('dailySparkContent');
        if (dailySparkContent) {
            if (data && typeof data === 'object' && data.hasOwnProperty('question')) {
                dailySparkContent.innerHTML = `<p><strong>Daily Spark Question:</strong> ${data.question}</p>`;
            } else {
                console.warn('Today\'s feed data is missing the "question" property or is not an object:', data);
                dailySparkContent.innerHTML = `<p>No daily spark question available today.</p>`;
            }
        } else {
            console.error('Element with ID "dailySparkContent" not found.');
        }
    })
    .catch(error => {
        console.error('Error fetching today\'s feed:', error);
        const dailySparkContent = document.getElementById('dailySparkContent');
        if (dailySparkContent) {
            dailySparkContent.innerHTML = `<p>Failed to load daily spark question.</p>`;
        }
    });

// Fetch Upcoming Events (Redundant fetch removed)

// Fetch Features (No changes needed based on previous code)
fetch('/api/features')
    .then(response => response.json())
    .then(features => {
        console.log('Features Data:', features); // For debugging
        const featuresContainer = document.getElementById('featuresContainer');
        if (featuresContainer) {
            featuresContainer.innerHTML = ''; // Clear previous content.
            if (features && Array.isArray(features)) {
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
        } else {
            console.error('Element with ID "featuresContainer" not found.');
        }
    })
    .catch(error => {
        console.error('Error fetching features:', error);
        const featuresContainer = document.getElementById('featuresContainer');
        if (featuresContainer) {
            featuresContainer.innerHTML = `<p>Failed to load features.</p>`;
        }
    });

// Example of how you might trigger viewSearchHistory (you'll need a button in your HTML)
// document.addEventListener('DOMContentLoaded', () => {
//     const viewHistoryButton = document.getElementById('viewSearchHistoryButton');
//     if (viewHistoryButton) {
//         viewHistoryButton.addEventListener('click', viewSearchHistory);
//     }
// });