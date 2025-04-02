async function fetchData(url, elementId) {
    try {
        const response = await fetch(url.replace("3000","5000"));
        const data = await response.json();
        const element = document.getElementById(elementId);
        element.innerHTML = data.content;
    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById(elementId).innerHTML = "<p>Error loading data.</p>";
    }
}

function loadData() {
    fetchData('/api/alumni', 'alumni-stories');
    fetchData('/api/leaderboard', 'leaderboard');
    fetchData('/api/daily-spark', 'daily-spark');
    fetchData('/api/feed', 'feed');
    fetchData('/api/events', 'trending-events');
    //loadSearchHistory(); // Load search history on page load - Removed to load on tab click
}

async function postData(){
  const postText = document.getElementById("postText").value;
  try{
    const response = await fetch('/api/posts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({text: postText})
    });
    if(response.ok){
      loadData();
      document.getElementById("postText").value = "";
    }
  }catch(error){
    console.error("error posting data", error);
  }
}

async function searchData() {
    const query = document.querySelector('.search-bar input').value;
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        });
        const data = await response.json();
        displaySearchResults(data.results);
        //loadSearchHistory(); //update search history - Removed to load on tab click
    } catch (error) {
        console.error('Error searching:', error);
        alert('Search failed.');
    }
}

function displaySearchResults(results) {
    const suggestionsList = document.getElementById('suggestions-list');
    suggestionsList.innerHTML = ''; // Clear previous results
    suggestionsList.style.display = 'none';

    if (results.length > 0) {
        results.forEach(item => {
            const li = document.createElement('li');
            if (item.event_name) {
                li.textContent = item.event_name + (item.description ? ': ' + item.description : '');
            } else if (item.name) {
                li.textContent = item.name + (item.career_path ? ': ' + item.career_path : '') + (item.achievements ? ': ' + item.achievements : '');
            } else {
                li.textContent = JSON.stringify(item);
            }
            li.addEventListener('click', () => {
                document.getElementById('search-input').value = li.textContent;
                suggestionsList.style.display = 'none';
            });
            suggestionsList.appendChild(li);
        });
        suggestionsList.style.display = 'block';
    } else {
        const li = document.createElement('li');
        li.textContent = 'No results found.';
        li.className = 'no-results';
        suggestionsList.appendChild(li);
        suggestionsList.style.display = 'block';
    }
}

async function loadSearchHistory() {
    try {
        const response = await fetch('/api/search_history');
        const data = await response.json();
        const historyList = document.querySelector('#search-history ul');
        historyList.innerHTML = '';
        data.history.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.query;
            historyList.appendChild(li);
        });
    } catch (error) {
        console.error('Error loading search history:', error);
    }
}

async function fetchSuggestions(query) {
    try {
        const response = await fetch(`/api/suggestions?query=${query}`);
        const data = await response.json();
        return data.suggestions;
    } catch (error) {
        console.error("Error fetching suggestions:", error);
        return [];
    }
}

function displaySuggestions(suggestions) {
    const suggestionsList = document.getElementById('suggestions-list');
    suggestionsList.innerHTML = '';
    if (suggestions.length > 0) {
        suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            li.innerHTML = highlightMatch(suggestion, document.getElementById('search-input').value);
            li.addEventListener('click', () => {
                document.getElementById('search-input').value = suggestion;
                suggestionsList.style.display = 'none';
                searchData();
            });
            suggestionsList.appendChild(li);
        });
        suggestionsList.style.display = 'block';
    } else {
        suggestionsList.style.display = 'none';
    }
}

function highlightMatch(text, match) {
    if (!match) return text;
    const regex = new RegExp(`(${match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<b>$1</b>');
}

let suggestionTimeout;
document.getElementById('search-input').addEventListener('input', (event) => {
    const query = event.target.value;
    clearTimeout(suggestionTimeout);
    suggestionTimeout = setTimeout(async () => {
        const suggestions = await fetchSuggestions(query);
        displaySuggestions(suggestions);
    }, 300);
});

document.addEventListener('click', (event) => {
    const suggestionsList = document.getElementById('suggestions-list');
    const searchInput = document.getElementById('search-input');
    const searchHistoryDiv = document.getElementById('search-history');
    if (!suggestionsList.contains(event.target) && event.target !== searchInput && event.target !== searchHistoryDiv) {
        suggestionsList.style.display = 'none';
    }
});

function toggleSearchHistory() {
    const searchHistoryDiv = document.getElementById('search-history');
    if (searchHistoryDiv.style.display === 'none') {
        searchHistoryDiv.style.display = 'block';
        loadSearchHistory();
    } else {
        searchHistoryDiv.style.display = 'none';
    }
}


window.onload = function() {
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
    }
    document.querySelector('.search-bar input').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            searchData();
        }
    });
    loadData();
};

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    if (document.body.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark');
    } else {
        localStorage.setItem('theme', 'light');
    }
}
