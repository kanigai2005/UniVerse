// Function to fetch and display Career Fair data
async function displayCareerFairs(url, elementId) {
    try {
        const response = await fetch(url);
        const careerFairs = await response.json();
        const element = document.getElementById(elementId);

        if (element) {
            element.innerHTML = ""; // Clear previous data
            careerFairs.forEach(fair => {
                element.innerHTML += `
                    <div>
                        <h2>${fair.name}</h2>
                        <p>Date: ${fair.date}</p>
                        <p>Location: ${fair.location}</p>
                        <p>Description: ${fair.description}</p>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error("Error fetching Career Fairs:", error);
    }
}

// Function to fetch and display Internships data
async function displayInternships(url, elementId) {
    try {
        const response = await fetch(url);
        const internships = await response.json();
        const element = document.getElementById(elementId);

        if (element) {
            element.innerHTML = ""; // Clear previous data
            internships.forEach(internship => {
                element.innerHTML += `
                    <div>
                        <h2>${internship.title}</h2>
                        <p>Company: ${internship.company}</p>
                        <p>Start Date: ${internship.start_date}</p>
                        <p>End Date: ${internship.end_date}</p>
                        <p>Description: ${internship.description}</p>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error("Error fetching Internships:", error);
    }
}

// Function to fetch and display Hackathons data
async function displayHackathons(url, elementId) {
    try {
        const response = await fetch(url);
        const hackathons = await response.json();
        const element = document.getElementById(elementId);

        if (element) {
            element.innerHTML = ""; // Clear previous data
            hackathons.forEach(hackathon => {
                element.innerHTML += `
                    <div>
                        <h2>${hackathon.name}</h2>
                        <p>Date: ${hackathon.date}</p>
                        <p>Location: ${hackathon.location}</p>
                        <p>Description: ${hackathon.description}</p>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error("Error fetching Hackathons:", error);
    }
}

// Function to fetch and display Leaderboard data
async function displayLeaderboard(url, elementId) {
    try {
        const response = await fetch(url);
        const users = await response.json();
        const element = document.getElementById(elementId);

        if (element) {
            element.innerHTML = ""; // Clear previous data
            users.forEach(user => {
                element.innerHTML += `
                    <div>
                        <h2>${user.name}</h2>
                        <p>Activity Score: ${user.activity_score}</p>
                        <p>Alumni Gems: ${user.alumni_gems}</p>
                        <p>Achievements: ${user.achievements.join(", ")}</p>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error("Error fetching Leaderboard:", error);
    }
}

// Function to fetch and display User data
async function displayUser(url, elementId) {
    try {
        const response = await fetch(url);
        const user = await response.json();
        const element = document.getElementById(elementId);

        if (element) {
            element.innerHTML = `
                <div>
                    <h2>${user.name}</h2>
                    <p>Email: ${user.email}</p>
                    <p>Activity Score: ${user.activity_score}</p>
                    <p>Alumni Gems: ${user.alumni_gems}</p>
                    <p>Achievements: ${user.achievements.join(", ")}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error("Error fetching User:", error);
    }
}

// Example usage (replace with your actual element IDs and URLs):
document.addEventListener("DOMContentLoaded", function() {
  if (document.getElementById("careerFairs")) {
    displayCareerFairs("/api/career_fairs", "careerFairs");
  }

  if (document.getElementById("internships")) {
    displayInternships("/api/internships", "internships");
  }

  if (document.getElementById("hackathons")) {
    displayHackathons("/api/hackathons", "hackathons");
  }

  if (document.getElementById("leaderboard")) {
    displayLeaderboard("/api/leaderboard", "leaderboard");
  }

    if (document.getElementById("userData")) {
        const username = window.location.pathname.split("/").pop(); //get username from url.
        displayUser(`/api/user/${username}`, "userData");
    }

});