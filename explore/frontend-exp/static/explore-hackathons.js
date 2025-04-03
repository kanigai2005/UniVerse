// static/explore-hackathons.js

async function loadHackathons() {
    try {
        const response = await fetch("http://127.0.0.1:8000/hackathons");
        if (!response.ok) {
            throw new Error("Failed to fetch hackathons");
        }
        const hackathons = await response.json();
        const container = document.getElementById("hackathons-list");

        container.innerHTML = ""; // Clear existing content

        hackathons.forEach(hackathon => {
            // Check if the hackathon date is today or in the future
            if (new Date(hackathon.date) >= new Date(new Date().setHours(0, 0, 0, 0))) {
                const hackathonItem = document.createElement("li");
                hackathonItem.classList.add("hackathon-item");
                hackathonItem.setAttribute("data-hackathon", JSON.stringify(hackathon));
                hackathonItem.innerHTML = `
                    <h3>${hackathon.name}</h3>
                    <p>Date: ${hackathon.date}</p>
                    <p>Location: ${hackathon.location}</p>
                `;
                container.appendChild(hackathonItem);
            }
        });

        addHackathonClickListeners();

    } catch (error) {
        console.error("Error loading hackathons:", error);
    }
}

function addHackathonClickListeners() {
    document.querySelectorAll('.hackathon-item').forEach(item => {
        item.addEventListener('click', () => {
            const hackathonData = JSON.parse(item.getAttribute('data-hackathon'));
            const popupDescription = document.getElementById('popup-description');
            popupDescription.innerHTML = `
                <h3>${hackathonData.name} - Description</h3>
                <p>${hackathonData.description}</p>
                <button id="register-button">Register</button>
                <div id="registration-form">
                    <input type="text" id="name" placeholder="Your Name">
                    <input type="email" id="email" placeholder="Your Email">
                    <button id="submit-registration">Submit</button>
                </div>
            `;
            popupDescription.style.display = 'block';

            popupDescription.addEventListener('mouseleave', () => {
                popupDescription.style.display = 'none';
            });

            document.getElementById('register-button').addEventListener('click', () => {
                document.getElementById('registration-form').style.display = 'block';
            });

            document.getElementById('submit-registration').addEventListener('click', () => {
                const name = document.getElementById('name').value;
                const email = document.getElementById('email').value;
                alert(`Registration submitted for ${hackathonData.name}!\nName: ${name}\nEmail: ${email}`);
                document.getElementById('registration-form').style.display = 'none';
            });
        });
    });
}

document.getElementById('search-button').addEventListener('click', () => {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const hackathonItems = Array.from(document.querySelectorAll('.hackathon-item'));

    hackathonItems.forEach(item => {
        const hackathonData = JSON.parse(item.getAttribute('data-hackathon'));
        const name = hackathonData.name.toLowerCase();
        const location = hackathonData.location.toLowerCase();

        if (name.includes(searchTerm) || location.includes(searchTerm)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
});

document.addEventListener('DOMContentLoaded', loadHackathons);