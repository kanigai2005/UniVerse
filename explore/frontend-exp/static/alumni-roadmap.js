document.addEventListener('DOMContentLoaded', () => {
            let allAlumniData = {};
            const searchInput = document.getElementById('searchInput');
            const resetButton = document.getElementById('resetButton');
            const roadmapModal = document.getElementById('roadmap-modal');
            const closeButton = document.querySelector('.close-button');


            resetButton.addEventListener('click', () => {
                searchInput.value = '';
                loadTopLikedAlumni();
            });

            closeButton.addEventListener('click', () => {
                roadmapModal.style.display = 'none';
            });

            window.addEventListener('click', (event) => {
                if (event.target === roadmapModal) {
                    roadmapModal.style.display = 'none';
                }
            });
            searchInput.addEventListener('input', function () {
                filterAlumni(this.value);
            });

            loadTopLikedAlumni();

            async function fetchTopLikedAlumni() {
                try {
                    const response = await fetch("/api/alumni/top-liked");
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    return data;
                } catch (error) {
                    console.error("Error fetching top liked alumni:", error);
                    // Consider displaying an error message to the user
                    return {}; // Or an empty object, to avoid breaking the app
                }
            }

            async function fetchAlumniDetails(alumniId) {
                try {
                    const response = await fetch(`/api/alumni/${alumniId}`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    return data;
                } catch (error) {
                    console.error("Error fetching alumni details:", error);
                    return null;
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
                const alumniData = await fetchAlumniDetails(alumniId);
                if (!alumniData) return;

                document.getElementById('modal-name').textContent = alumniData.name;
                document.getElementById('modal-profession').textContent = `Profession: ${alumniData.profession}`;
                document.getElementById('modal-almaMater').textContent = `Alma Mater: ${alumniData.alma_mater}`;
                document.getElementById('modal-interviews').textContent = `Interviews: ${alumniData.interviews}`;
                document.getElementById('modal-internships').textContent = `Internships: ${alumniData.internships}`;
                document.getElementById('modal-startups').textContent = `Startups: ${alumniData.startups}`;
                document.getElementById('modal-currentCompany').textContent = `Current Company: ${alumniData.current_company}`;
                document.getElementById('modal-milestones').textContent = `Milestones: ${alumniData.milestones}`;
                document.getElementById('modal-advice').textContent = `Advice: ${alumniData.advice}`;
                roadmapModal.style.display = 'block';
            }



            async function likeAlumni(alumniId) {
                try {
                    const response = await fetch(`/api/alumni/${alumniId}/like`, {
                        method: 'GET', // Or POST, depending on your backend
                    });
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    //  No need to call loadTopLikedAlumni() here.  The like count should update automatically.
                    //  The server should return the updated like count, and you can update the specific card.
                    const updatedAlumni = await response.json(); // Assuming the server returns the updated alumni data.

                    // Find the card and update the like count.
                    const card = document.querySelector(`[data-alumni-id="${alumniId}"]`).closest('.roadmap-card');
                    if (card) {
                         // card.querySelector('.likes-count').textContent = updatedAlumni.likes; //if you have likes count in frontend
                    }

                } catch (error) {
                    console.error("Error liking alumni:", error);
                }
            }


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