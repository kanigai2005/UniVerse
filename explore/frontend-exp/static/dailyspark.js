function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') { return unsafe; }
    return unsafe
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
 }

// --- Navbar Update Logic ---
async function updateNavbar() {
    const navProfileLink = document.getElementById('nav-profile-link');
    if (!navProfileLink) { console.warn("Navbar profile link element not found."); return null; }

    try {
        const response = await fetch('/api/users/me'); // Uses cookie auth
        if (!response.ok) {
            if (response.status === 401 || response.status === 307) {
                console.log("User not logged in for navbar update.");
                navProfileLink.href = "/login.html"; // Link to login
                localStorage.removeItem('username');
            } else {
                console.error(`Error fetching user for navbar: ${response.status}`);
                navProfileLink.href = "/login.html";
                localStorage.removeItem('username');
            }
            return null; // Indicate user not fetched or error
        }
        const userData = await response.json();
        if (userData && userData.username) {
            navProfileLink.href = `/profile.html?username=${encodeURIComponent(userData.username)}`;
            localStorage.setItem('username', userData.username); // Store for potential use
            return userData; // Return fetched user data
        } else {
            console.warn("User data fetched but username missing.");
            navProfileLink.href = "/login.html";
            localStorage.removeItem('username');
            return null;
        }
    } catch (error) {
        console.error("Network or JS error fetching user for navbar:", error);
        navProfileLink.href = "/login.html";
        localStorage.removeItem('username');
        return null;
    }
}

// --- Daily Spark Page Logic ---
document.addEventListener('DOMContentLoaded', () => {
    // --- Get Elements ---
    const postQuestionPanel = document.getElementById('post-question-panel');
    const postQuestionForm = document.getElementById('post-question-form');
    const postQuestionStatus = document.getElementById('post-question-status');

    const currentQuestionDiv = document.getElementById('current-question');

    const submitAnswerForm = document.getElementById('submit-answer-form');
    const answerTextArea = document.getElementById('answer-text');
    const submitAnswerStatus = document.getElementById('submit-answer-status');
    const submitAnswerButton = submitAnswerForm.querySelector('button');

    const pastQuestionListDiv = document.getElementById('past-question-list');

    let currentUserData = null; // To store user info

    // --- Fetch Initial Data ---

    // 1. Fetch Current User Data (to check if alumni & update navbar)
    async function fetchCurrentUserAndUpdateNav() {
        currentUserData = await updateNavbar(); // Call the navbar update function
        if (currentUserData && currentUserData.is_alumni) {
            postQuestionPanel.style.display = 'block'; // Show posting panel for alumni
        } else {
            postQuestionPanel.style.display = 'none';
        }
    }

    // 2. Fetch Today's Question
    async function fetchTodaysQuestion() {
        currentQuestionDiv.innerHTML = `<p class="loading">Loading today's question...</p>`;
        answerTextArea.disabled = true; submitAnswerButton.disabled = true; // Disable form initially
        try {
            const response = await fetch('/api/daily-spark/today');
            if (!response.ok) {
                if (response.status === 404) {
                     currentQuestionDiv.innerHTML = `<p class="no-data">No Daily Spark question posted yet today.</p>`;
                } else { throw new Error(`HTTP error ${response.status}`); }
                return null; // No question found or error
            }
            const data = await response.json();
            displayTodaysQuestion(data);
            return data; // Return question data
        } catch (error) {
            console.error("Error fetching today's question:", error);
            currentQuestionDiv.innerHTML = `<p class="error">Error loading question.</p>`;
            return null;
        }
    }

    // 3. Fetch Top Liked Questions
    async function fetchTopLikedQuestions() {
        pastQuestionListDiv.innerHTML = `<p class="loading">Loading top questions...</p>`;
        try {
            const response = await fetch('/api/daily-spark/top-liked?limit=5'); // Add limit param
            if (!response.ok) { throw new Error(`HTTP error ${response.status}`); }
            const questions = await response.json();
            displayTopQuestions(questions);
        } catch (error) {
            console.error('Error fetching top liked questions:', error);
            pastQuestionListDiv.innerHTML = `<p class="error">Error loading questions.</p>`;
        }
    }

    // --- Display Functions ---

    function displayTodaysQuestion(question) {
         if (!question || !question.question) {
             currentQuestionDiv.innerHTML = `<p class="no-data">No Daily Spark question available.</p>`;
             answerTextArea.disabled = true; submitAnswerButton.disabled = true;
             return;
         }
         currentQuestionDiv.innerHTML = `
             <div class="question-info">
                 ${question.company ? `<span><strong>Company:</strong> ${escapeHtml(question.company)}</span>` : ''}
                 ${question.role ? `<span style="margin-left: 10px;"><strong>Role:</strong> ${escapeHtml(question.role)}</span>` : ''}
             </div>
             <p><strong>${escapeHtml(question.question)}</strong></p>
             `;
          // Enable the answer form ONLY if a question is displayed
          answerTextArea.disabled = false;
          submitAnswerButton.disabled = false;
     }

    function displayTopQuestions(questions) {
        pastQuestionListDiv.innerHTML = ''; // Clear loading/error
        if (!Array.isArray(questions) || questions.length === 0) {
            pastQuestionListDiv.innerHTML = `<p class="no-data">No past questions found.</p>`;
            return;
        }

        questions.forEach(question => {
            const questionDiv = document.createElement('div');
            questionDiv.classList.add('past-question-item');
            // Display question details
            questionDiv.innerHTML = `
                <div class="past-question-header">
                    ${question.company ? `<strong>Company:</strong> ${escapeHtml(question.company)}, ` : ''}
                    ${question.role ? `<strong>Role:</strong> ${escapeHtml(question.role)}` : ''}
                </div>
                <div class="past-question-text">${escapeHtml(question.question)}</div>
                <div class="past-answers-container">
                    <h3>Answers:</h3>
                    <div id="past-answers-${question.id}">
                        ${question.answers && question.answers.length > 0 ? question.answers.map(answer => `
                            <div class="past-answer-item">
                                <span><strong>${escapeHtml(answer.user)}:</strong> ${escapeHtml(answer.text)}</span>
                                <div class="vote-buttons">
                                    <button class="upvote" onclick="voteAnswer(${answer.id}, 'upvote')" title="Upvote">👍</button>
                                    <span class="vote-count" id="vote-count-${answer.id}">${answer.votes}</span>
                                    <button class="downvote" onclick="voteAnswer(${answer.id}, 'downvote')" title="Downvote">👎</button>
                                </div>
                            </div>
                        `).join('') : '<p>No answers yet.</p>'}
                    </div>
                </div>
            `;
            pastQuestionListDiv.appendChild(questionDiv);
        });
    }

     // --- Event Handlers ---

    // Handle Submitting an Answer to Today's Question
    submitAnswerForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        submitAnswerStatus.textContent = 'Submitting...';
        submitAnswerStatus.style.color = '#555';
        submitAnswerButton.disabled = true;

        const answerText = answerTextArea.value.trim();
        if (!answerText) {
            submitAnswerStatus.textContent = 'Please enter an answer.';
            submitAnswerStatus.style.color = 'red';
            submitAnswerButton.disabled = false;
            return;
        }

        try {
            const response = await fetch('/api/daily-spark/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text: answerText }),
            });

            if (!response.ok) {
                 if (response.status === 401 || response.status === 307) throw new Error("Auth required.");
                 const errorData = await response.json().catch(() => ({detail: `HTTP Error ${response.status}`}));
                 throw new Error(errorData.detail || 'Failed to submit answer.');
            }

            const data = await response.json();
            console.log('Answer submission successful:', data);
            submitAnswerStatus.textContent = 'Answer submitted!';
            submitAnswerStatus.style.color = 'green';
            answerTextArea.value = ''; // Clear textarea
            setTimeout(() => { submitAnswerStatus.textContent = ''; }, 3000);
             // Optionally refresh top questions if the answer might affect votes significantly
             // fetchTopLikedQuestions();

        } catch (error) {
            console.error('Error submitting answer:', error);
            submitAnswerStatus.textContent = `Error: ${error.message}`;
            submitAnswerStatus.style.color = 'red';
        } finally {
             submitAnswerButton.disabled = false; // Re-enable button
        }
    });

    // Handle Alumni Posting a New Question
    if (postQuestionForm) {
         postQuestionForm.addEventListener('submit', async (event) => {
             event.preventDefault();
             postQuestionStatus.textContent = 'Posting...';
             postQuestionStatus.style.color = '#555';
             postQuestionForm.querySelector('button').disabled = true;

             const questionText = document.getElementById('new-question-text').value.trim();
             const company = document.getElementById('new-question-company').value.trim();
             const role = document.getElementById('new-question-role').value.trim();

             if (!questionText) {
                 postQuestionStatus.textContent = 'Please enter the question text.';
                 postQuestionStatus.style.color = 'red';
                 postQuestionForm.querySelector('button').disabled = false;
                 return;
             }

             try {
                const response = await fetch('/api/daily-spark/questions', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        question_text: questionText,
                        company: company || null,
                        role: role || null
                    }),
                });

                 if (!response.ok) {
                     if (response.status === 401 || response.status === 307) throw new Error("Auth required.");
                     if (response.status === 403) throw new Error("Only alumni can post.");
                     const errorData = await response.json().catch(() => ({detail: `HTTP Error ${response.status}`}));
                     throw new Error(errorData.detail || 'Failed to post question.');
                }

                 const newQuestion = await response.json();
                 console.log("Question posted:", newQuestion);
                 postQuestionStatus.textContent = 'Question posted successfully for today!';
                 postQuestionStatus.style.color = 'green';
                 postQuestionForm.reset();
                 // Disable form for the rest of the day (client-side indication)
                 postQuestionForm.querySelectorAll('input, textarea, button').forEach(el => el.disabled = true);
                 // Refresh today's question display immediately
                 await fetchTodaysQuestion(); // Use await here
                 setTimeout(() => { postQuestionStatus.textContent = ''; }, 5000);


             } catch(error) {
                  console.error("Error posting question:", error);
                  postQuestionStatus.textContent = `Error: ${error.message}`;
                  postQuestionStatus.style.color = 'red';
                  postQuestionForm.querySelector('button').disabled = false; // Re-enable on error
             }
        });
    }


    // --- Initial Load Function ---
    async function initializePage() {
        await fetchCurrentUserAndUpdateNav(); // Fetch user & update nav first
        await fetchTodaysQuestion();
        await fetchTopLikedQuestions();
    }

    initializePage();

}); // End DOMContentLoaded

// --- Global Vote Functions --- (Attached to window)

async function voteAnswer(answerId, voteType) {
    // Construct the CORRECT API endpoint: /api/daily-spark/answers/{answer_id}/{upvote|downvote}
    const endpoint = `/api/daily-spark/answers/${answerId}/${voteType}`;
    const voteCountElement = document.getElementById(`vote-count-${answerId}`);

    // Basic check if element exists
    if (!voteCountElement) {
         console.error(`Vote count element not found for answer ${answerId}`);
         return;
    }

    try {
        const response = await fetch(endpoint, { method: 'POST' });

        if (!response.ok) {
            // Handle specific errors based on status code
            if (response.status === 401 || response.status === 307) throw new Error("Please log in to vote.");
            const errorData = await response.json().catch(() => ({detail: `Vote failed with status ${response.status}`}));
            if (response.status === 400) throw new Error(errorData.detail || "Cannot vote on your own answer."); // Handle specific backend error message
            throw new Error(errorData.detail || 'Failed to record vote.');
        }

        const data = await response.json();
        // Update vote count in the UI
        voteCountElement.textContent = data.votes;

    } catch (error) {
        console.error(`Error ${voteType}ing answer ${answerId}:`, error);
        alert(`Vote Error: ${error.message}`); // Display specific error message to user
    }
}