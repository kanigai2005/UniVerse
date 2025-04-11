// static/explore-hackathons.js
async function loadHackathons() {
    try {
        const response = await fetch("/api/hackathons");
        if (!response.ok) {
            throw new Error(`Failed to fetch hackathons: ${response.status}`);
        }
        const hackathons = await response.json();
        const container = document.getElementById("hackathons-list");

        container.innerHTML = ""; // Clear existing content

        hackathons.forEach(hackathon => {
            const hackathonItem = document.createElement("li");
            hackathonItem.classList.add("hackathon-item");
            hackathonItem.setAttribute("data-hackathon", JSON.stringify(hackathon));
            hackathonItem.innerHTML = `
                <h3>${hackathon.name}</h3>
                <p>Date: ${hackathon.date}</p>
                <p>Location: ${hackathon.location}</p>
            `;
            container.appendChild(hackathonItem);
        });

        addHackathonClickListeners();

    } catch (error) {
        console.error("Error loading hackathons:", error);
        document.getElementById("hackathons-list").innerHTML = "<p>Error loading hackathons. Please try again later.</p>";
    }
}

function addHackathonClickListeners() {
    const popupDescription = document.getElementById('popup-description');
    if (!popupDescription) return; // Ensure popup exists

    document.querySelectorAll('.hackathon-item').forEach(item => {
        item.addEventListener('click', () => {
            const hackathonData = JSON.parse(item.getAttribute('data-hackathon'));
            popupDescription.innerHTML = `
                <h3>${hackathonData.name} - Description</h3>
                <p>${hackathonData.description}</p>
                <button id="register-button">Register</button>
                <div id="registration-form" style="display:none;">
                    <input type="text" id="name" placeholder="Your Name">
                    <input type="email" id="email" placeholder="Your Email">
                    <button id="submit-registration">Submit</button>
                </div>
            `;
            popupDescription.style.display = 'block';

            popupDescription.addEventListener('mouseleave', () => {
                popupDescription.style.display = 'none';
            }, { once: true });

            const registerButton = document.getElementById('register-button');
            if (registerButton) {
                registerButton.addEventListener('click', () => {
                    const registrationForm = document.getElementById('registration-form');
                    if (registrationForm) {
                        registrationForm.style.display = 'block';
                    }
                });
            }

            const submitRegistrationButton = document.getElementById('submit-registration');
            if (submitRegistrationButton) {
                submitRegistrationButton.addEventListener('click', () => {
                    const name = document.getElementById('name').value;
                    const email = document.getElementById('email').value;
                    alert(`Registration submitted for ${hackathonData.name}!\nName: ${name}\nEmail: ${email}`);
                    const registrationForm = document.getElementById('registration-form');
                    if (registrationForm) {
                        registrationForm.style.display = 'none';
                    }
                });
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', loadHackathons);

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