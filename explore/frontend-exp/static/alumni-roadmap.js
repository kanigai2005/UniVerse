document.addEventListener('DOMContentLoaded', () => {
    let allAlumniData = {};
    document.getElementById('resetButton').addEventListener('click', () => {
        document.getElementById('searchInput').value = ''; // Clear search input
        loadTopLikedAlumni(); // Reload original data
    });
    loadTopLikedAlumni();

    async function fetchTopLikedAlumni() {
        try {
            const response = await fetch("/api/alumni/top-liked");
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error("Error fetching top liked alumni:", error);
            return {};
        }
    }

    async function fetchAlumniDetails(alumniId) {
        try {
            const response = await fetch(`/api/alumni/${alumniId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error("Error fetching alumni details:", error);
            return null;
        }
    }

    async function likeAlumni(alumniId) {
        try {
            const response = await fetch(`/api/alumni/${alumniId}/like`, {
                method: 'GET',
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            loadTopLikedAlumni();
        } catch (error) {
            console.error("Error liking alumni:", error);
        }
    }

    function createRoadmapCard(alumni) {
        const card = document.createElement('div');
        card.classList.add('roadmap-card');
        const initials = alumni.name.substring(0, 2).toUpperCase();
        card.innerHTML = `
            <div class="avatar">${initials}</div>
            <div class="name">${alumni.name}</div>
            <div class="profession">${alumni.profession}</div>
            <button class="like-button" data-alumni-id="${alumni.id}">Like</button>
        `;
        card.addEventListener('click', (event) => {
            if (!event.target.classList.contains('like-button')) {
                openRoadmapModal(alumni.id);
            }
        });

        const likeButton = card.querySelector('.like-button');
        likeButton.addEventListener('click', (event) => {
            event.stopPropagation();
            likeAlumni(alumni.id);
        });

        return card;
    }

    function populateRoadmaps(groupedAlumni) {
        const container = document.getElementById("roadmaps-dynamic-container");
        if (!container) return;
        container.innerHTML = "";
        for (const department in groupedAlumni) {
            const section = document.createElement('section');
            section.classList.add('roadmap-section');
            section.innerHTML = `<h3 class="section-heading">${department} Roadmaps</h3><div class="roadmap-list ${department.toLowerCase().replace(' ', '-')}-roadmaps"></div>`;
            container.appendChild(section);
            const listContainer = section.querySelector(`.${department.toLowerCase().replace(' ', '-')}-roadmaps`);
            groupedAlumni[department].forEach(alumni => {
                listContainer.appendChild(createRoadmapCard(alumni));
            });
        }
        allAlumniData = groupedAlumni;
    }

    async function loadTopLikedAlumni() {
        const data = await fetchTopLikedAlumni();
        populateRoadmaps(data);
    }

    async function openRoadmapModal(alumniId) {
        const alumni = await fetchAlumniDetails(alumniId);
        if (!alumni) return;
        const modal = document.getElementById('roadmap-modal');
        if (!modal) return;
        document.getElementById('modal-name').textContent = alumni.name;
        document.getElementById('modal-profession').textContent = `Profession: ${alumni.profession}`;
        document.getElementById('modal-almaMater').textContent = `Alma Mater: ${alumni.alma_mater}`;
        document.getElementById('modal-interviews').textContent = `Interviews: ${alumni.interviews}`;
        document.getElementById('modal-internships').textContent = `Internships: ${alumni.internships}`;
        document.getElementById('modal-startups').textContent = `Startups: ${alumni.startups}`;
        document.getElementById('modal-currentCompany').textContent = `Current Company: ${alumni.current_company}`;
        document.getElementById('modal-milestones').textContent = `Milestones: ${alumni.milestones}`;
        document.getElementById('modal-advice').textContent = `Advice: ${alumni.advice}`;
        modal.style.display = 'block';
    }

    document.querySelector('.close-button').addEventListener('click', () => {
        const modal = document.getElementById('roadmap-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    });

    window.addEventListener('click', (event) => {
        const modal = document.getElementById('roadmap-modal');
        if (event.target === modal && modal) {
            modal.style.display = 'none';
        }
    });

    document.getElementById('searchInput').addEventListener('input', function() {
        filterAlumni(this.value);
    });

    function filterAlumni(searchTerm) {
        const filteredData = {};
        for (const department in allAlumniData) {
            filteredData[department] = allAlumniData[department].filter(alumni => {
                const searchStr = `${alumni.name} ${alumni.profession}`.toLowerCase();
                return searchStr.includes(searchTerm.toLowerCase());
            });
        }
        populateRoadmaps(filteredData);
    }
});