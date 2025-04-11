async function loadInternships() {
    try {
        const response = await fetch("/api/internships");
        console.log("Response from /api/internships:", response);
        if (!response.ok) {
            throw new Error(`Failed to fetch internships: ${response.status}`);
        }
        const internships = await response.json();
        console.log("Internships data:", internships);
        const container = document.getElementById("internships-list");

        container.innerHTML = ""; // Clear existing content

        internships.forEach(internship => {
            const internshipItem = document.createElement("li");
            internshipItem.classList.add("internship-item");
            internshipItem.setAttribute("data-internship", JSON.stringify(internship));
            internshipItem.innerHTML = `
                <h3>${internship.title}</h3>
                <p>Company: ${internship.company}</p>
                <p>Start Date: ${new Date(internship.start_date).toLocaleDateString()}</p>
                <p>End Date: ${new Date(internship.end_date).toLocaleDateString()}</p>
            `;
            container.appendChild(internshipItem);
        });

        console.log("Calling addInternshipClickListeners");
        addInternshipClickListeners();
        addSearchAndFilter();

    } catch (error) {
        console.error("Error loading internships:", error);
        document.getElementById("internships-list").innerHTML = "<p>Error loading internships. Please try again later.</p>";
    }
}

function addInternshipClickListeners() {
    const popupDescription = document.getElementById('popup-description');
    console.log("popupDescription element:", popupDescription);
    if (!popupDescription) {
        console.error("popup-description element not found!");
        return; // Ensure popup exists
    }

    document.querySelectorAll('.internship-item').forEach(item => {
        item.addEventListener('click', () => {
            console.log("Internship item clicked:", item);
            const internshipData = JSON.parse(item.getAttribute('data-internship'));
            console.log("Clicked internship data:", internshipData);
            popupDescription.innerHTML = `
                <h3>${internshipData.title} - Details</h3>
                <p>Company: ${internshipData.company}</p>
                <p>Start Date: ${new Date(internshipData.start_date).toLocaleDateString()}</p>
                <p>End Date: ${new Date(internshipData.end_date).toLocaleDateString()}</p>
                <p>Description: ${internshipData.description || 'No description available.'}</p>
                <button id="apply-button">Apply Now</button>
                <div id="application-form" style="display:none;">
                    <input type="text" id="name" placeholder="Your Name">
                    <input type="email" id="email" placeholder="Your Email">
                    <textarea id="resume" placeholder="Link to your Resume"></textarea>
                    <button id="submit-application">Submit Application</button>
                </div>
            `;
            popupDescription.style.display = 'block';
            document.getElementById('overlay').style.display = 'block'; // Show overlay

            // Close popup on overlay click
            document.getElementById('overlay').onclick = () => {
                popupDescription.style.display = 'none';
                document.getElementById('overlay').style.display = 'none';
            };

            const applyButton = document.getElementById('apply-button');
            if (applyButton) {
                applyButton.addEventListener('click', () => {
                    const applicationForm = document.getElementById('application-form');
                    if (applicationForm) {
                        applicationForm.style.display = 'block';
                    }
                });
            }

            const submitApplicationButton = document.getElementById('submit-application');
            if (submitApplicationButton) {
                submitApplicationButton.addEventListener('click', () => {
                    const name = document.getElementById('name').value;
                    const email = document.getElementById('email').value;
                    const resume = document.getElementById('resume').value;
                    alert(`Application submitted for ${internshipData.title}!\nName: ${name}\nEmail: ${email}\nResume: ${resume}`);
                    const applicationForm = document.getElementById('application-form');
                    if (applicationForm) {
                        applicationForm.style.display = 'none';
                    }
                });
            }
        });
    });
}

function addSearchAndFilter() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');

    if (searchButton) {
        searchButton.addEventListener('click', () => {
            const searchTerm = searchInput.value.toLowerCase();
            filterItems(searchTerm);
        });
    }
}

function filterItems(searchTerm) {
    const internshipItems = document.querySelectorAll('#internships-list .internship-item');

    internshipItems.forEach(item => {
        const itemText = item.textContent.toLowerCase();
        item.style.display = itemText.includes(searchTerm) ? 'block' : 'none';
    });
}

document.addEventListener('DOMContentLoaded', loadInternships);