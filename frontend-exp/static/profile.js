// --- Utility: Simple HTML Escaping ---
function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) { return ''; } // Handle null/undefined
    const str = String(unsafe); // Ensure it's a string
    return str
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "") // Corrected to "
         .replace(/'/g, "'"); // Corrected to '
}

// --- Global State ---
let currentUser = null;
let myLikedQuestionIds = new Set();

// --- Navbar Update / Fetch Current User ---
async function fetchCurrentUserAndUpdateNav() {
    console.log("Fetching current user data...");
    const navProfileLink = document.getElementById('nav-profile-link');
    try {
        const response = await fetch('/api/users/me');
        if (!response.ok) {
            if (response.status === 401 || response.status === 307) { console.log("User not authenticated."); }
            else { console.error(`Error fetching user: ${response.status}`); }
            if (navProfileLink) navProfileLink.href = "/login.html";
            localStorage.removeItem('username');
            currentUser = null; // Ensure currentUser is null on error/logout
            return null;
        }
        const userData = await response.json();
        console.log("Current user data:", userData);
        if (userData && userData.username) {
            if (navProfileLink) navProfileLink.href = `/profile.html?username=${encodeURIComponent(userData.username)}`;
            localStorage.setItem('username', userData.username);
            currentUser = userData;
            return userData;
        } else {
             if (navProfileLink) navProfileLink.href = "/login.html";
             localStorage.removeItem('username');
             currentUser = null;
             return null;
         }
    } catch (error) {
        console.error("Error fetching current user:", error);
        if (navProfileLink) navProfileLink.href = "/login.html";
        localStorage.removeItem('username');
        currentUser = null;
        return null;
    }
}

// --- Fetch Liked Question IDs ---
async function fetchMyLikedQuestionIds() {
    if (!currentUser) { console.log("Cannot fetch liked IDs, user not logged in."); return; }
    console.log("Fetching liked question IDs...");
    try {
        // Ensure this path matches your Python API endpoint
        const response = await fetch("/api/questions/me/liked");
        if (!response.ok) { console.warn(`Failed to fetch liked question IDs: ${response.status}`); return; }
        const likedIdsArray = await response.json();
        if (!Array.isArray(likedIdsArray)) { console.warn("Invalid format for liked question IDs."); return; }
        myLikedQuestionIds = new Set(likedIdsArray);
        console.log("Stored liked question IDs:", myLikedQuestionIds);
    } catch (error) {
        console.error("Error fetching liked question IDs:", error);
        myLikedQuestionIds = new Set();
    }
}


// --- Expert Q&A Page Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log("Expert Q&A DOM Loaded.");

    const questionForm = document.getElementById('question-form');
    const questionInput = document.getElementById('question-input');
    const postFeedback = document.querySelector('#question-form .post-feedback');
    const communityQuestionsContainer = document.getElementById("questions-list");
    const myQuestionsContainer = document.getElementById("user-questions-list");
    const selectedQuestionsContainer = document.getElementById("selected-questions-list");
    const alumniAnswerSection = document.getElementById("alumni-answer-section");

     if (!questionForm || !communityQuestionsContainer || !myQuestionsContainer || !selectedQuestionsContainer || !alumniAnswerSection) {
         console.error("CRITICAL ERROR: One or more essential section containers not found in HTML.");
         document.body.insertAdjacentHTML('afterbegin', '<p style="background:red; color:white; padding:10px; text-align:center;">Page Error: Could not initialize Q&A sections.</p>');
         return;
     }

    async function initializePage() {
        console.log("Initializing Expert Q&A page...");
        await fetchCurrentUserAndUpdateNav(); // Fetches and sets global currentUser
        if (!currentUser) {
            console.warn("User not logged in, showing limited content.");
             myQuestionsContainer.innerHTML = `<p class="no-data"><a href="/login.html">Log in</a> to ask or see your questions.</p>`;
             alumniAnswerSection.style.display = 'none';
             questionForm?.querySelector('button[type="submit"]')?.setAttribute('disabled', 'true');
             questionForm?.querySelector('textarea')?.setAttribute('placeholder', 'Please log in to ask a question.');
        } else {
            questionForm?.querySelector('button[type="submit"]')?.removeAttribute('disabled');
            questionForm?.querySelector('textarea')?.setAttribute('placeholder', 'Type your question here...');
            await fetchMyLikedQuestionIds();
            await loadMyQuestions();
            if(currentUser.is_alumni) { // Check the flag from the fetched currentUser object
                alumniAnswerSection.style.display = 'block';
                await loadSelectedQuestions(); // This is the one that was failing with 404
            } else {
                alumniAnswerSection.style.display = 'none';
            }
        }
        await loadPopularQuestions();
        console.log("Expert Q&A page initialization complete.");
    }

    // --- Fetch and Display Functions ---
    async function loadSelectedQuestions() { // For "Answer Today's Selected Questions"
        console.log("Loading selected/answerable questions for alumni...");
        if (!selectedQuestionsContainer) return;
        selectedQuestionsContainer.innerHTML = `<p class="loading">Loading selected questions...</p>`;
        try {
            // THIS IS THE CORRECTED ENDPOINT BASED ON YOUR PYTHON CODE
            const response = await fetch("/api/expertqa/answerable-questions");
            if (!response.ok) {
                let errorDetail = `HTTP error ${response.status}`;
                if (response.status === 404) {
                    errorDetail = "Selected questions endpoint not found (404). Please check API routes.";
                } else {
                    try { const errorData = await response.json(); errorDetail = errorData.detail || errorDetail; } catch (e) { /* ignore */ }
                }
                throw new Error(errorDetail);
            }
            const questions = await response.json();
            if (!Array.isArray(questions)) throw new Error("Invalid data format for selected questions.");
            console.log("Answerable/Selected questions fetched:", questions);
            displayQuestions(questions, selectedQuestionsContainer, false, true);
        } catch (error) {
            console.error("Error loading selected questions:", error);
            selectedQuestionsContainer.innerHTML = `<p class="error">Error loading selected questions: ${escapeHtml(error.message)}</p>`;
        }
    }

    async function loadPopularQuestions() {
        console.log("Loading popular community questions...");
        if (!communityQuestionsContainer) return;
        communityQuestionsContainer.innerHTML = `<p class="loading">Loading community questions...</p>`;
        try {
            // Ensure this path matches your Python API endpoint for popular questions
            const response = await fetch("/api/questions/popular");
            if (!response.ok) throw new Error(`HTTP error ${response.status}`);
            const questions = await response.json();
            if (!Array.isArray(questions)) throw new Error("Invalid data format for popular questions.");
            displayQuestions(questions, communityQuestionsContainer, false, false);
        } catch (error) {
            console.error("Error loading popular questions:", error);
            communityQuestionsContainer.innerHTML = `<p class="error">Error loading community questions: ${escapeHtml(error.message)}</p>`;
        }
    }

    async function loadMyQuestions() {
         if (!currentUser?.username) {
             console.log("Cannot load 'My Questions', user info not available.");
             if (myQuestionsContainer) myQuestionsContainer.innerHTML = `<p class="no-data">Could not retrieve user information.</p>`;
             return;
         }
         console.log(`Loading questions for user: ${currentUser.username}`);
         if (!myQuestionsContainer) return;
         myQuestionsContainer.innerHTML = `<p class="loading">Loading your questions...</p>`;
         try {
            // Ensure this path matches your Python API endpoint
            const response = await fetch(`/api/users/${encodeURIComponent(currentUser.username)}/questions`);
            if (!response.ok) throw new Error(`HTTP error ${response.status}`);
            const myQuestions = await response.json();
            if (!Array.isArray(myQuestions)) throw new Error("Invalid data format for user questions.");
            displayQuestions(myQuestions, myQuestionsContainer, true, false);
         } catch (error) {
            console.error("Error loading your questions:", error);
            myQuestionsContainer.innerHTML = `<p class="error">Error loading your questions: ${escapeHtml(error.message)}</p>`;
         }
    }

    function displayQuestions(questions, container, isMyQuestionsList, showAnswerButtonForAlumni) {
        container.innerHTML = "";
        if (!Array.isArray(questions) || questions.length === 0) {
            const msg = container.id === 'selected-questions-list' ? 'No questions currently selected for answering by alumni.'
                      : isMyQuestionsList ? 'You haven\'t asked any questions yet.'
                      : 'No questions found in this category.';
            container.innerHTML = `<p class="no-data">${msg}</p>`;
            return;
        }
        console.log(`Displaying ${questions.length} questions in container #${container.id}`);
        questions.forEach(question => {
            if (!question || typeof question !== 'object' || !question.id) {
                 console.warn("Skipping invalid question object:", question); return;
            }
            container.appendChild(createQuestionElement(question, isMyQuestionsList, showAnswerButtonForAlumni));
        });
        attachAnswerButtonListeners(container);
        attachAnswerFormSubmitListeners(container);
        attachLikeQuestionButtonListeners(container);
        attachLikeAnswerButtonListeners(container);
    }

    function createQuestionElement(question, isMyQuestion, showAnswerButtonForAlumni) {
        const questionDiv = document.createElement("div");
        questionDiv.classList.add("question-box");
        questionDiv.dataset.questionId = question.id;

        const formattedDate = new Date(question.created_at).toLocaleDateString();
        const isLikedByMe = myLikedQuestionIds.has(question.id);
        const likeButtonClass = isLikedByMe ? 'liked' : '';
        const likeButtonText = isLikedByMe ? '❤️ Liked' : '👍 Like';
        const likeButtonTitle = isLikedByMe ? 'Unlike Question' : 'Like Question';

        let answersHtml = '<p class="no-data">No answers yet.</p>';
        if (question.expert_answers && Array.isArray(question.expert_answers) && question.expert_answers.length > 0) {
            answersHtml = question.expert_answers.map(answer => {
                if (!answer || !answer.id) return '';
                // Use answer.user.username if available, otherwise answer.username
                const answererUsername = answer.user?.username || answer.username || 'Unknown Expert';
                return `
                <div class="answer-item">
                    <div>
                        <strong>${escapeHtml(answererUsername)}</strong>
                        ${answer.is_alumni_answer ? '<span class="alumni-badge">Alumni</span>' : ''}:
                        <span style="white-space: pre-wrap;">${escapeHtml(answer.answer_text || '')}</span>
                    </div>
                    <div class="answer-meta">
                        <span>${new Date(answer.created_at).toLocaleDateString()}</span>
                        <span class="answer-like-section">
                            <button class="like-answer-button upvote" data-answer-id="${answer.id}" title="Like Answer">👍</button>
                            <span class="answer-likes-count" id="answer-likes-${answer.id}">${answer.likes ?? 0}</span>
                        </span>
                    </div>
                </div>`;
            }).join('');
        }

        // Answer button shows if it's the "selected questions" section AND current user is alumni
        const displayAnswerBtn = showAnswerButtonForAlumni && currentUser?.is_alumni;
        // For 'Your Questions' or 'Community Questions', this button won't show by default (showAnswerButtonForAlumni is false)

        questionDiv.innerHTML = `
            <p class="question-text">${escapeHtml(question.question_text)}</p>
            <p class="question-meta">
                Asked by ${escapeHtml(question.user?.username || question.username || 'Anonymous')} on ${formattedDate}
                 • <span class="like-count" id="question-likes-${question.id}">${question.likes ?? 0}</span> Likes
            </p>
            <div class="question-actions">
                <span class="like-section">
                    <button class="like-button ${likeButtonClass}" data-question-id="${question.id}" title="${likeButtonTitle}" ${!currentUser ? 'disabled' : ''}>${likeButtonText}</button>
                    <span class="like-feedback" id="like-feedback-${question.id}"></span>
                </span>
                ${displayAnswerBtn ? `<button class="answer-button" data-question-id="${question.id}">Answer This Question</button>` : ''}
            </div>
            <div class="answers-section">
                <h3>Answers</h3>
                <div class="answers-list">${answersHtml}</div>
                ${displayAnswerBtn ? `
                <form class="answer-form" id="answer-form-${question.id}" style="display: none;">
                    <label for="answer-input-${question.id}">Your Alumni Answer:</label>
                    <textarea id="answer-input-${question.id}" rows="3" required></textarea>
                    <button type="submit">Submit Answer</button>
                    <div class="post-feedback status-message"></div>
                </form>
                ` : ''}
            </div>
        `;
        return questionDiv;
    }

    if (questionForm) {
        questionForm.addEventListener("submit", async function(event) {
            event.preventDefault();
            if (!currentUser) { alert("Please log in to ask a question."); return; }

            const postButton = this.querySelector('button[type="submit"]');
            const questionText = questionInput?.value.trim();
            if(!postButton || !questionInput || !postFeedback) return;

            postButton.disabled = true;
            postFeedback.textContent = "Posting...";
            postFeedback.className = 'post-feedback status-message';

            if (!questionText) {
                 postFeedback.textContent = "Please enter your question.";
                 postFeedback.className = 'post-feedback status-message error';
                 postButton.disabled = false;
                 setTimeout(() => postFeedback.textContent = "", 3000);
                 return;
             }
            try {
                const response = await fetch("/api/questions", { // Ensure this path matches your Python API
                     method: "POST", headers: {'Content-Type': 'application/json'},
                     body: JSON.stringify({ question_text: questionText }),
                 });
                const responseData = await response.json();
                if (!response.ok) {
                    throw new Error(responseData.detail || `Failed to post: ${response.statusText}`);
                }
                console.log("Question posted:", responseData);
                questionInput.value = "";
                postFeedback.textContent = "Question posted successfully!";
                postFeedback.className = 'post-feedback status-message success';
                await loadMyQuestions();
            } catch (error) {
                console.error("Error posting question:", error);
                postFeedback.textContent = `Error: ${error.message}`;
                postFeedback.className = 'post-feedback status-message error';
            } finally {
                setTimeout(() => {
                    postButton.disabled = false;
                    postFeedback.textContent = "";
                    postFeedback.className = 'post-feedback status-message';
                }, 3000);
            }
        });
    } else { console.error("Question form not found!"); }

    function attachAnswerButtonListeners(container) {
         container.querySelectorAll('.answer-button').forEach(button => {
             const newButton = button.cloneNode(true);
             button.parentNode.replaceChild(newButton, button);
             newButton.addEventListener('click', function() {
                 const questionId = this.dataset.questionId;
                 const answerForm = document.getElementById(`answer-form-${questionId}`);
                 if (answerForm) {
                      answerForm.style.display = answerForm.style.display === 'none' ? 'block' : 'none';
                      if(answerForm.style.display === 'block') answerForm.querySelector('textarea')?.focus();
                 } else console.error(`Answer form not found for question ID: ${questionId}`);
             });
         });
     }

    // ***** CORRECTED FUNCTION *****
    function attachAnswerFormSubmitListeners(container) {
        container.querySelectorAll('.answer-form').forEach(form => {
            const newForm = form.cloneNode(true); // Clone to remove old listeners and prevent multiple bindings
            form.parentNode.replaceChild(newForm, form);

            newForm.addEventListener('submit', async function(event) {
                event.preventDefault();
                const questionId = this.id.split('-').pop();
                const textarea = this.querySelector('textarea');
                const feedbackDiv = this.querySelector('.post-feedback');
                const submitBtn = this.querySelector('button[type="submit"]');
                const answerText = textarea?.value.trim();

                if (!textarea || !feedbackDiv || !submitBtn) {
                    console.error("Answer form elements missing for question ID:", questionId);
                    return;
                }
                if (!answerText) {
                    feedbackDiv.textContent = 'Please enter your answer.';
                    feedbackDiv.className = 'post-feedback status-message error';
                    setTimeout(() => { feedbackDiv.textContent = ''; }, 3000);
                    return;
                }
                if (!currentUser || !currentUser.is_alumni) { // Ensure user is alumni
                    alert("Error: Only alumni can submit answers here. Please refresh if you are an alumnus.");
                    feedbackDiv.textContent = 'Permission denied.';
                    feedbackDiv.className = 'post-feedback status-message error';
                    return;
                }

                feedbackDiv.textContent = 'Submitting...';
                feedbackDiv.className = 'post-feedback status-message';
                submitBtn.disabled = true;

                try {
                    // CORRECTED API CALL:
                    const response = await fetch(`/api/expertqa/answers/${questionId}`, { // Path from your Python code
                        method: 'POST', // Explicitly set method
                        headers: {
                            'Content-Type': 'application/json',
                            // Add CSRF token header if your backend requires it for POST requests
                        },
                        body: JSON.stringify({ answer_text: answerText }) // Send data as JSON
                    });

                    const responseData = await response.json();
                    if (!response.ok) {
                        throw new Error(responseData.detail || `Failed to submit answer (Status: ${response.status})`);
                    }

                    feedbackDiv.textContent = 'Answer submitted successfully!';
                    feedbackDiv.className = 'post-feedback status-message success';
                    textarea.value = '';
                    // newForm.style.display = 'none'; // Optionally hide form

                    // Dynamically append the new answer to the UI
                    const answersListDiv = document.querySelector(`.question-box[data-question-id="${questionId}"] .answers-list`);
                    if (answersListDiv) {
                        appendAnswer(responseData, answersListDiv); // Assuming responseData is the new answer object
                    } else {
                        // Fallback: reload the relevant questions section if append fails
                        console.warn("Could not find answers list to append new answer for question:", questionId, ". Reloading section.");
                        await loadSelectedQuestions(); // Or the section where this answer belongs
                    }

                } catch (error) {
                    console.error("Error submitting answer:", error);
                    feedbackDiv.textContent = `Error: ${escapeHtml(error.message)}`;
                    feedbackDiv.className = 'post-feedback status-message error';
                } finally {
                    submitBtn.disabled = false;
                    setTimeout(() => {
                        if (feedbackDiv.className.includes('status-message')) { // Only clear if it's a status message
                            feedbackDiv.textContent = '';
                            feedbackDiv.className = 'post-feedback status-message';
                        }
                    }, 4000); // Slightly longer for success/error messages
                }
            });
        });
    }
    // ***** END OF CORRECTED FUNCTION *****


    function attachLikeQuestionButtonListeners(container) {
         container.querySelectorAll('.like-section .like-button').forEach(button => {
             const newButton = button.cloneNode(true);
             button.parentNode.replaceChild(newButton, button);
             newButton.addEventListener('click', function() {
                 const questionId = parseInt(this.dataset.questionId, 10);
                 if (!isNaN(questionId)) toggleLikeQuestion(questionId, this);
                 else console.error("Invalid question ID on like button:", this.dataset.questionId);
             });
         });
     }

    function attachLikeAnswerButtonListeners(container) {
        container.querySelectorAll('.answer-like-section .like-answer-button').forEach(button => {
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            newButton.addEventListener('click', function() {
                const answerId = parseInt(this.dataset.answerId, 10);
                if (!isNaN(answerId)) likeAnswer(answerId, this);
                else console.error("Invalid answer ID on like button:", this.dataset.answerId);
            });
        });
    }


     function appendAnswer(answer, container) {
          if (!answer || !container) return;
          const noAnswerMsg = container.querySelector('.no-data');
          if (noAnswerMsg) noAnswerMsg.remove();
          const answerDiv = document.createElement('div');
          answerDiv.classList.add('answer-item');
          const answererUsername = answer.user?.username || answer.username || 'Unknown Expert';
          answerDiv.innerHTML = `
              <div><strong>${escapeHtml(answererUsername)}</strong> ${answer.is_alumni_answer ? '<span class="alumni-badge">Alumni</span>' : ''}: <span style="white-space: pre-wrap;">${escapeHtml(answer.answer_text || '')}</span></div>
              <div class="answer-meta">
                  <span>${new Date(answer.created_at).toLocaleDateString()}</span>
                  <span class="answer-like-section">
                      <button class="like-answer-button upvote" data-answer-id="${answer.id}" title="Like Answer">👍</button>
                      <span class="answer-likes-count" id="answer-likes-${answer.id}">${answer.likes ?? 0}</span>
                  </span>
              </div>`;
          container.appendChild(answerDiv);
          const newLikeButton = answerDiv.querySelector('.like-answer-button');
          if(newLikeButton) {
              newLikeButton.addEventListener('click', function() {
                  const answerId = parseInt(this.dataset.answerId, 10);
                  if (!isNaN(answerId)) likeAnswer(answerId, this);
              });
          }
     }

    async function toggleLikeQuestion(questionId, buttonElement) {
        if (!currentUser) { alert("Please log in to like questions."); return; }
        if (!buttonElement) return;
        const isCurrentlyLiked = myLikedQuestionIds.has(questionId);
        const action = isCurrentlyLiked ? 'Unlike' : 'Like';
        const originalText = buttonElement.innerHTML;
        buttonElement.disabled = true;
        buttonElement.innerHTML = `${action}ing...`;
        const feedbackSpan = document.getElementById(`like-feedback-${questionId}`);
        if (feedbackSpan) feedbackSpan.textContent = '';
        try {
            // Ensure this path matches your Python API
            const response = await fetch(`/api/questions/${questionId}/like`, { method: 'POST' });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || `Failed to ${action.toLowerCase()}`);
            const countSpan = document.getElementById(`question-likes-${questionId}`);
            if (countSpan) countSpan.textContent = data.likes;
            if (data.liked) {
                myLikedQuestionIds.add(questionId);
                buttonElement.classList.add('liked');
                buttonElement.innerHTML = '❤️ Liked';
                buttonElement.title = 'Unlike Question';
            } else {
                myLikedQuestionIds.delete(questionId);
                buttonElement.classList.remove('liked');
                buttonElement.innerHTML = '👍 Like';
                buttonElement.title = 'Like Question';
            }
        } catch (error) {
             console.error(`Error ${action.toLowerCase()}ing question:`, error);
             if (feedbackSpan) { feedbackSpan.textContent = `Error!`; feedbackSpan.className = 'like-feedback status-message error'; }
             else { alert(`Error: ${error.message}`); }
             buttonElement.innerHTML = originalText;
        } finally {
             buttonElement.disabled = false;
             if (feedbackSpan?.textContent.includes('Error')) {
                 setTimeout(() => { if(feedbackSpan) feedbackSpan.textContent = ""; }, 2000);
             }
         }
    }

    async function likeAnswer(answerId, buttonElement) {
        if (!currentUser) { alert("Please log in to like answers."); return; }
        if (!buttonElement) return;
        buttonElement.disabled = true;
        const originalColor = buttonElement.style.color;
        buttonElement.style.color = '#ccc';
        console.log(`Liking answer ${answerId}`);
        try {
            // Ensure this path matches your Python API
            const response = await fetch(`/api/expertqa/answers/${answerId}/like`, { method: 'POST' });
            const data = await response.json();
            if (!response.ok) { throw new Error(data.detail || `Failed to like answer`); }
            const countSpan = document.getElementById(`answer-likes-${answerId}`);
            if (countSpan) countSpan.textContent = data.likes;
            buttonElement.style.color = '#28a745'; // Green for success
            // buttonElement.disabled = true; // Optionally disable after one like
        } catch (error) {
            console.error("Error liking answer:", error);
            alert(`Like Error: ${error.message}`);
            buttonElement.style.color = originalColor;
            buttonElement.disabled = false;
        } finally {
              setTimeout(() => {
                 if (buttonElement.style.color !== '#28a745') {
                      buttonElement.disabled = false;
                      buttonElement.style.color = originalColor;
                 }
             }, 1000);
        }
    }

    initializePage();
});