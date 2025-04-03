document.addEventListener('DOMContentLoaded', () => {
    const internshipForm = document.getElementById('internship-form');
    const featuredInternships = document.getElementById('featured-internships');
    const overlay = document.getElementById('overlay');
    const popup = document.getElementById('popup');

    // Function to fetch and display internships from the backend
    async function loadInternships() {
        try {
            const response = await fetch("http://127.0.0.1:8000/internships");
            if (!response.ok) {
                throw new Error("Failed to fetch internships");
            }
            const internships = await response.json();

            featuredInternships.innerHTML = ''; // Clear existing content

            internships.forEach(internship => {
                const internshipBox = document.createElement('div');
                internshipBox.classList.add('internship-box');
                internshipBox.innerHTML = `
                    <img src="${internship.company_logo || 'default_logo.png'}" alt="${internship.company} Logo">
                    <h3>${internship.company}</h3>
                    <p><strong>Role:</strong> ${internship.role}</p>
                    <p><strong>Location:</strong> ${internship.location}</p>
                `;
                internshipBox.addEventListener('click', () => {
                    showPopup(
                        internship.company,
                        internship.role,
                        internship.location,
                        internship.link,
                        internship.requirements
                    );
                });
                featuredInternships.appendChild(internshipBox);
            });
        } catch (error) {
            console.error("Error loading internships:", error);
        }
    }

    // Function to add a new internship to the backend and update the UI
    async function addInternship(internshipData) {
        try {
            const response = await fetch("http://127.0.0.1:8000/internships", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(internshipData)
            });

            if (response.ok) {
                loadInternships(); // Refresh the list
                internshipForm.reset(); // Clear the form
            } else {
                alert('Failed to add internship.');
            }
        } catch (error) {
            console.error("Error adding internship:", error);
            alert('An error occurred while adding the internship.');
        }
    }

    // Event listener for the internship form submission
    internshipForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const company = document.getElementById('company').value;
        const role = document.getElementById('role').value;
        const location = document.getElementById('location').value;
        const link = document.getElementById('link').value;

        addInternship({ company, role, location, link });
    });

    // Popup functions (same as your original code)
    window.showPopup = function(company, role, location, link, requirements) {
        document.getElementById('popup-company').textContent = company;
        document.getElementById('popup-role').textContent = role;
        document.getElementById('popup-location').textContent = location;
        document.getElementById('popup-requirements').textContent = requirements;
        document.getElementById('popup-link').href = link;
        popup.style.display = 'block';
        overlay.style.display = 'block';
    };

    window.closePopup = function() {
        popup.style.display = 'none';
        overlay.style.display = 'none';
    };

    // Load internships on page load
    loadInternships();
});