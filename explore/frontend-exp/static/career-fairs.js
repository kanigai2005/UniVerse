document.addEventListener("DOMContentLoaded", async () => {
    await loadCareerFairs();
    await loadHackathons();
    await loadInternships();
    await loadLeaderboard();
});

// Function to fetch and display career fairs
async function loadCareerFairs() {
    try {
        const response = await fetch("/career_fairs");
        const fairs = await response.json();
        const container = document.getElementById("career-fairs-list");
        container.innerHTML = ""; // Clear existing content

        fairs.forEach(fair => {
            const fairItem = document.createElement("div");
            fairItem.className = "fair-item";
            fairItem.innerHTML = `
                <h3>${fair.name}</h3>
                <p>Location: ${fair.location}</p>
                <p>Date: ${fair.date}</p>
                <p>${fair.description}</p>
            `;
            container.appendChild(fairItem);
        });
    } catch (error) {
        console.error("Error loading career fairs:", error);
    }
}

// Function to fetch and display hackathons
async function loadHackathons() {
    try {
        const response = await fetch("/hackathons");
        const hackathons = await response.json();
        const container = document.getElementById("hackathons-list");
        container.innerHTML = ""; // Clear existing content

        hackathons.forEach(hackathon => {
            const hackathonItem = document.createElement("div");
            hackathonItem.className = "hackathon-item";
            hackathonItem.innerHTML = `
                <h3>${hackathon.name}</h3>
                <p>Location: ${hackathon.location}</p>
                <p>Date: ${hackathon.date}</p>
                <p>${hackathon.description}</p>
            `;
            container.appendChild(hackathonItem);
        });
    } catch (error) {
        console.error("Error loading hackathons:", error);
    }
}

// Function to fetch and display internships
async function loadInternships() {
    try {
        const response = await fetch("/internships");
        const internships = await response.json();
        const container = document.getElementById("internships-list");
        container.innerHTML = ""; // Clear existing content

        internships.forEach(internship => {
            const internshipItem = document.createElement("div");
            internshipItem.className = "internship-item";
            internshipItem.innerHTML = `
                <h3>${internship.title}</h3>
                <p>Company: ${internship.company}</p>
                <p>Start Date: ${internship.start_date}</p>
                <p>End Date: ${internship.end_date}</p>
                <p>${internship.description}</p>
            `;
            container.appendChild(internshipItem);
        });
    } catch (error) {
        console.error("Error loading internships:", error);
    }
}

// Function to fetch and display leaderboard
async function loadLeaderboard() {
    try {
        const response = await fetch("/leaderboard");
        const users = await response.json();
        const container = document.getElementById("leaderboard-list");
        container.innerHTML = ""; // Clear existing content

        users.forEach(user => {
            const userItem = document.createElement("div");
            userItem.className = "user-item";
            userItem.innerHTML = `
                <h3>${user.name}</h3>
                <p>Activity Score: ${user.activity_score}</p>
                <p>Achievements: ${user.achievements.join(", ")}</p>
                <p>Alumni Gems: ${user.alumni_gems}</p>
            `;
            container.appendChild(userItem);
        });
    } catch (error) {
        console.error("Error loading leaderboard:", error);
    }
}