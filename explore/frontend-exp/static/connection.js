document.addEventListener('DOMContentLoaded', () => {
const connectionsList = document.getElementById('connections-list');
const suggestionsList = document.getElementById('suggestions-list');
const userName = "John Doe"; // Replace with logic to get the logged-in user's name

async function fetchConnections() {
    try {
        const response = await fetch(`/api/users/${userName}/connections`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const connections = await response.json();
        connectionsList.innerHTML = connections.map(user => `
            <div>${user.name} - ${user.profession} <button onclick="viewProfile('${user.name}')">View Profile</button></div>
        `).join('');
    } catch (error) {
        console.error('Error fetching connections:', error);
    }
}

async function fetchSuggestions() {
    try {
        const response = await fetch(`/api/users/${userName}/suggestions`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const suggestions = await response.json();
        suggestionsList.innerHTML = suggestions.map(user => `
            <div>${user.name} - ${user.profession} <button onclick="followUser('${user.name}')">Follow</button> <button onclick="viewProfile('${user.name}')">View Profile</button></div>
        `).join('');
    } catch (error) {
        console.error('Error fetching suggestions:', error);
    }
}

window.followUser = async (suggestionUserName) => {
    try {
        const response = await fetch(`/api/users/${userName}/follow/${suggestionUserName}`, {
            method: 'POST',
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        alert(`Followed ${suggestionUserName}`);
        fetchConnections();
        fetchSuggestions();
    } catch (error) {
        console.error('Error following user:', error);
    }
};

window.viewProfile = (profileUserName) => {
    // Add logic to view other profiles
    alert(`Viewing profile of ${profileUserName}`);
}

fetchConnections();
fetchSuggestions();
});