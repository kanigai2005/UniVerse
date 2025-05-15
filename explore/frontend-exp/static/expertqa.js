// --- Utility: Simple HTML Escaping ---
function escapeHtml(unsafe) {
    // Handles null/undefined/non-strings gracefully and performs correct escaping
    if (typeof unsafe !== 'string') { return unsafe === null || unsafe === undefined ? '' : unsafe; }
    return unsafe
         .replace(/&/g, "&")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "")
         .replace(/'/g, "'");
}

// --- Global State ---
let currentUser = null; // Store logged-in user info (id, username, is_alumni)
let myLikedQuestionIds = new Set(); // Store IDs of questions liked by current user
// let myLikedAnswerIds = new Set(); // Add this if implementing answer like-once

// --- Navbar Update / Fetch Current User ---
async function fetchCurrentUserAndUpdateNav() {
    console.log("Fetching current user data...");
    const navProfileLink = document.getElementById('nav-profile-link');
    try {
        const response = await fetch('/api/users/me'); // Uses cookie auth
        if (!response.ok) {
            if (response.status === 401 || response.status === 307) { console.log("User not authenticated."); }
            else { console.error(`Error fetching user: ${response.status}`); }
            if (navProfileLink) navProfileLink.href = "/login.html";
            localStorage.removeItem('username');
            return null;
        }
        const userData = await response.json();
        console.log("Current user data:", userData);
        if (userData && userData.username) {
            if (navProfileLink) navProfileLink.href = `/profile.html?username=${encodeURIComponent(userData.username)}`;
            localStorage.setItem('username', userData.username);
            currentUser = userData; // Store user data globally
            return userData;
        } else {
             if (navProfileLink) navProfileLink.href = "/login.html";
             localStorage.removeItem('username');
             return null;
         }
    } catch (error) {
        console.error("Error fetching current user:", error);
        if (navProfileLink) navProfileLink.href = "/login.html";
        localStorage.removeItem('username');
        return null;
    }
}

// --- Fetch Liked Question IDs ---
async function fetchMyLikedQuestionIds() {
    if (!currentUser) { console.log("Cannot fetch liked IDs, user not logged in."); return; }
    console.log("Fetching liked question IDs...");
    try {
        const response = await fetch("/api/questions/me/liked"); // Calls new backend endpoint
        if (!response.ok) { console.warn(`Failed to fetch liked question IDs: ${response.status}`); return; }
        const likedIdsArray = await response.json();
        if (!Array.isArray(likedIdsArray)) { console.warn("Invalid format for liked question IDs."); return; }
        myLikedQuestionIds = new Set(likedIdsArray); // Store in the Set
        console.log("Stored liked question IDs:", myLikedQuestionIds);
    } catch (error) {
        console.error("Error fetching liked question IDs:", error);
        myLikedQuestionIds = new Set(); // Reset on error
    }
}


// --- Expert Q&A Page Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log("Expert Q&A DOM Loaded.");

    // --- Element References ---
    const questionForm = document.getElementById('question-form');
    const questionInput = document.getElementById('question-input');
    const postFeedback = document.querySelector('#question-form .post-feedback');
    const communityQuestionsContainer = document.getElementById("questions-list");
    const myQuestionsContainer = document.getElementById("user-questions-list");
    const selectedQuestionsContainer = document.getElementById("selected-questions-list");
    const alumniAnswerSection = document.getElementById("alumni-answer-section");

     // --- Check core elements ---
     if (!questionForm || !communityQuestionsContainer || !myQuestionsContainer || !selectedQuestionsContainer || !alumniAnswerSection) {
         console.error("CRITICAL ERROR: One or more essential section containers not found in HTML.");
         document.body.insertAdjacentHTML('afterbegin', '<p style="background:red; color:white; padding:10px; text-align:center;">Page Error: Could not initialize Q&A sections.</p>');
         return;
     }

    // --- Initial Load Function ---
    async function initializePage() {
        console.log("Initializing Expert Q&A page...");
        currentUser = await fetchCurrentUserAndUpdateNav(); // Fetch user & update nav
        if (!currentUser) {
            console.warn("User not logged in, showing limited content.");
             myQuestionsContainer.innerHTML = `<p class="no-data"><a href="/login.html">Log in</a> to ask or see your questions.</p>`;
             alumniAnswerSection.style.display = 'none';
             questionForm?.querySelector('button[type="submit"]')?.setAttribute('disabled', 'true'); // Disable posting if not logged in
             questionForm?.querySelector('textarea')?.setAttribute('placeholder', 'Please log in to ask a question.');
        } else {
            // User is logged in
            questionForm?.querySelector('button[type="submit"]')?.removeAttribute('disabled'); // Ensure posting is enabled
             questionForm?.querySelector('textarea')?.setAttribute('placeholder', 'Type your question here...');
            await fetchMyLikedQuestionIds(); // Fetch liked status *after* getting user
            await loadMyQuestions();
            if(currentUser.is_alumni) {
                alumniAnswerSection.style.display = 'block';
                await loadSelectedQuestions();
            } else {
                alumniAnswerSection.style.display = 'none';
            }
        }
        // Load popular questions for everyone, regardless of login status
        await loadPopularQuestions();
         console.log("Expert Q&A page initialization complete.");
    }


    // --- Fetch and Display Functions ---

     async function loadSelectedQuestions() {
        console.log("Loading selected questions for alumni...");
        selectedQuestionsContainer.innerHTML = `<p class="loading">Loading selected questions...</p>`;
        try {
            const response = await fetch("/api/expertqa/selected-questions");
            if (!response.ok) throw new Error(`HTTP error ${response.status}`);
            const questions = await response.json();
             if (!Array.isArray(questions)) throw new Error("Invalid data format for selected questions.");
            displayQuestions(questions, selectedQuestionsContainer, false, true); // Display in alumni section, mark as answerable
        } catch (error) {
            console.error("Error loading selected questions:", error);
            selectedQuestionsContainer.innerHTML = `<p class="error">Error loading selected questions: ${escapeHtml(error.message)}</p>`;
        }
    }

    async function loadPopularQuestions() {
        console.log("Loading popular community questions...");
        communityQuestionsContainer.innerHTML = `<p class="loading">Loading community questions...</p>`;
        try {
            const response = await fetch("/api/questions/popular");
            if (!response.ok) throw new Error(`HTTP error ${response.status}`);
            const questions = await response.json();
            if (!Array.isArray(questions)) throw new Error("Invalid data format for popular questions.");
            displayQuestions(questions, communityQuestionsContainer, false, false); // Display in community section
        } catch (error) {
            console.error("Error loading popular questions:", error);
            communityQuestionsContainer.innerHTML = `<p class="error">Error loading community questions: ${escapeHtml(error.message)}</p>`;
        }
    }

    async function loadMyQuestions() {
         if (!currentUser?.username) {
             console.log("Cannot load 'My Questions', user info not available.");
             myQuestionsContainer.innerHTML = `<p class="no-data">Could not retrieve user information.</p>`;
             return;
         }
         console.log(`Loading questions for user: ${currentUser.username}`);
         myQuestionsContainer.innerHTML = `<p class="loading">Loading your questions...</p>`;
         try {
            const response = await fetch(`/api/users/${encodeURIComponent(currentUser.username)}/questions`);
            if (!response.ok) throw new Error(`HTTP error ${response.status}`);
            const myQuestions = await response.json();
            if (!Array.isArray(myQuestions)) throw new Error("Invalid data format for user questions.");
            displayQuestions(myQuestions, myQuestionsContainer, true, false); // Display in user's section
         } catch (error) {
            console.error("Error loading your questions:", error);
            myQuestionsContainer.innerHTML = `<p class="error">Error loading your questions: ${escapeHtml(error.message)}</p>`;
         }
    }

    // Reusable function to display questions in a given container
    function displayQuestions(questions, container, isMyQuestionsList, showAnswerButtonForAlumni) {
        container.innerHTML = ""; // Clear
        if (!Array.isArray(questions) || questions.length === 0) {
            const msg = container.id === 'selected-questions-list' ? 'No questions selected for answering today.'
                      : isMyQuestionsList ? 'You haven\'t asked any questions yet.'
                      : 'No questions found.';
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

        // Attach listeners AFTER elements are in the DOM
        attachAnswerButtonListeners(container);
        attachAnswerFormSubmitListeners(container);
        attachLikeQuestionButtonListeners(container);
        attachLikeAnswerButtonListeners(container);
    }

    // Helper function to create a single question element
    function createQuestionElement(question, isMyQuestion, showAnswerButtonForAlumni) {
        const questionDiv = document.createElement("div");
        questionDiv.classList.add("question-box");
        questionDiv.dataset.questionId = question.id;

        const formattedDate = new Date(question.created_at).toLocaleDateString();
        const isLikedByMe = myLikedQuestionIds.has(question.id); // Use the fetched set
        const likeButtonClass = isLikedByMe ? 'liked' : '';
        const likeButtonText = isLikedByMe ? '❤️ Liked' : '👍 Like';
        const likeButtonTitle = isLikedByMe ? 'Unlike Question' : 'Like Question';

        // Build answers HTML
        let answersHtml = '<p class="no-data">No answers yet.</p>';
        if (question.expert_answers && question.expert_answers.length > 0) {
            answersHtml = question.expert_answers.map(answer => {
                if (!answer || !answer.id) return '';
                return `
                <div class="answer-item">
                    <div>
                        <strong>${escapeHtml(answer.username || 'Unknown')}</strong>
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

        // Show answer button only if allowed for this section AND user is alumni
        const displayAnswerBtn = showAnswerButtonForAlumni && currentUser?.is_alumni;

        questionDiv.innerHTML = `
            <p class="question-text">${escapeHtml(question.question_text)}</p>
            <p class="question-meta">
                Asked by ${escapeHtml(question.username || 'Anonymous')} on ${formattedDate}
                 • <span class="like-count" id="question-likes-${question.id}">${question.likes ?? 0}</span> Likes
            </p>
            <div class="question-actions">
                <span class="like-section">
                    <button class="like-button ${likeButtonClass}" data-question-id="${question.id}" title="${likeButtonTitle}">${likeButtonText}</button>
                    <span class="like-feedback" id="like-feedback-${question.id}"></span>
                </span>
                <!-- Conditionally display answer button -->
                ${displayAnswerBtn ? `<button class="answer-button" data-question-id="${question.id}">Answer</button>` : ''}
            </div>
            <div class="answers-section">
                <h3>Answers</h3>
                <div class="answers-list">${answersHtml}</div>
                <!-- Answer form for alumni -->
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

    // --- Event Handlers ---

    // Post New Question Form
    if (questionForm) {
        questionForm.addEventListener("submit", async function(event) {
            event.preventDefault();
            if (!currentUser) { alert("Please log in to ask a question."); return; }

            const postButton = this.querySelector('button[type="submit"]');
            const questionText = questionInput?.value.trim();
            if(!postButton || !questionInput || !postFeedback) return; // Element check

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
                const response = await fetch("/api/questions", {
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
                await loadMyQuestions(); // Refresh user's list
            } catch (error) {
                console.error("Error posting question:", error);
                postFeedback.textContent = `Error: ${error.message}`;
                postFeedback.className = 'post-feedback status-message error';
            } finally {
                setTimeout(() => {
                    postButton.disabled = false;
                    postFeedback.textContent = "";
                    postFeedback.className = 'post-feedback status-message';
                }, 3000); // Clear feedback after 3s
            }
        });
    } else { console.error("Question form not found!"); }


    // --- Attach Event Listeners for Dynamic Content ---
    // These functions find buttons within a container and attach listeners

    function attachAnswerButtonListeners(container) {
         container.querySelectorAll('.answer-button').forEach(button => {
             const newButton = button.cloneNode(true); // Clone to remove old listeners
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

     // --- Find this function in your expertqa.js ---
function attachAnswerFormSubmitListeners(container) {
    container.querySelectorAll('.answer-form').forEach(form => {
        const newForm = form.cloneNode(true); // Clone to remove old listeners
        form.parentNode.replaceChild(newForm, form);
        newForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const questionId = this.id.split('-').pop(); // Get question ID from form ID
            const textarea = this.querySelector('textarea');
            const feedbackDiv = this.querySelector('.post-feedback');
            const submitBtn = this.querySelector('button[type="submit"]'); // More specific selector
            const answerText = textarea?.value.trim();

            if (!textarea || !feedbackDiv || !submitBtn) { console.error("Answer form elements missing"); return; }
            if (!answerText) {
                feedbackDiv.textContent = 'Please enter your answer.';
                feedbackDiv.className = 'post-feedback status-message error';
                setTimeout(() => { feedbackDiv.textContent = ''; }, 3000);
                return;
            }
            if (!currentUser) { // Double check user is logged in before submitting
                alert("Error: You seem to be logged out. Please refresh and log in again.");
                feedbackDiv.textContent = 'Authentication error.';
                feedbackDiv.className = 'post-feedback status-message error';
                return;
            }

            feedbackDiv.textContent = 'Submitting...'; feedbackDiv.className = 'post-feedback status-message'; submitBtn.disabled = true;

            try {
                // ***** THIS IS THE CORRECTED FETCH CALL *****
                const response = await fetch(`/api/expertqa/answers/${questionId}`, {
                    method: 'POST', // Explicitly set method to POST
                    headers: {
                        'Content-Type': 'application/json',
                        // Add other headers like CSRF token if your backend requires them
                    },
                    body: JSON.stringify({ answer_text: answerText }) // Send the data as JSON in the body
                });
                // ***** END OF CORRECTION *****

                const responseData = await response.json(); // Try to parse JSON even on error for details
                if (!response.ok) {
                    // Use error detail from backend if available, otherwise status text
                    throw new Error(responseData.detail || `Failed to submit: ${response.statusText} (Status: ${response.status})`);
                }

                // --- Success ---
                feedbackDiv.textContent = 'Answer submitted!'; feedbackDiv.className = 'post-feedback status-message success';
                textarea.value = ''; // Clear the textarea
                // newForm.style.display = 'none'; // Optionally hide form after success

                // Find the specific answers list for this question and append the new answer
                const answersListDiv = document.querySelector(`.question-box[data-question-id="${questionId}"] .answers-list`);
                if (answersListDiv) {
                    appendAnswer(responseData, answersListDiv); // Append new answer dynamically
                } else {
                    console.warn("Could not find answers list container to append new answer for question:", questionId);
                    // As a fallback, maybe just reload the section or page if dynamic append fails
                    // await loadSelectedQuestions(); // Example: reload selected questions
                }

                setTimeout(() => { feedbackDiv.textContent = '';}, 3000);

            } catch (error) {
                console.error("Error submitting answer:", error);
                feedbackDiv.textContent = `Error: ${error.message}`;
                feedbackDiv.className = 'post-feedback status-message error';
                // Don't clear textarea on error so user doesn't lose input
            } finally {
                submitBtn.disabled = false; // Re-enable button in both success and error cases
                // Optionally clear error message after a delay
                 if (feedbackDiv.textContent.startsWith('Error:')) {
                     setTimeout(() => { feedbackDiv.textContent = ''; }, 5000); // Longer delay for errors
                 }
            }
        });
    });
}
// --- Keep the rest of your expertqa.js file as is ---
     function attachLikeQuestionButtonListeners(container) {
         container.querySelectorAll('.like-section .like-button').forEach(button => { // More specific selector
             const newButton = button.cloneNode(true); // Clone
             button.parentNode.replaceChild(newButton, button);
             newButton.addEventListener('click', function() {
                 const questionId = parseInt(this.dataset.questionId, 10);
                 if (!isNaN(questionId)) toggleLikeQuestion(questionId, this); // Call toggle function
                 else console.error("Invalid question ID on like button:", this.dataset.questionId);
             });
         });
     }

      function attachLikeAnswerButtonListeners(container) {
          container.querySelectorAll('.like-answer-button').forEach(button => {
              const newButton = button.cloneNode(true); // Clone
              button.parentNode.replaceChild(newButton, button);
              newButton.addEventListener('click', function() {
                  const answerId = parseInt(this.dataset.answerId, 10);
                  if (!isNaN(answerId)) likeAnswer(answerId, this); // Call like function
                  else console.error("Invalid answer ID on like button:", this.dataset.answerId);
              });
          });
      }

     // Helper to append a single answer dynamically
     function appendAnswer(answer, container) {
          if (!answer || !container) return;
          const noAnswerMsg = container.querySelector('.no-data');
          if (noAnswerMsg) noAnswerMsg.remove();

          const answerDiv = document.createElement('div');
          answerDiv.classList.add('answer-item');
          // const isAnswerLikedByMe = myLikedAnswerIds.has(answer.id); // Check if needed

          answerDiv.innerHTML = `
              <div><strong>${escapeHtml(answer.username || 'Unknown')}</strong> ${answer.is_alumni_answer ? '<span class="alumni-badge">Alumni</span>' : ''}: <span style="white-space: pre-wrap;">${escapeHtml(answer.answer_text || '')}</span></div>
              <div class="answer-meta">
                  <span>${new Date(answer.created_at).toLocaleDateString()}</span>
                  <span class="answer-like-section">
                      <button class="like-answer-button upvote" data-answer-id="${answer.id}" title="Like Answer">👍</button>
                      <span class="answer-likes-count" id="answer-likes-${answer.id}">${answer.likes ?? 0}</span>
                  </span>
              </div>`;
          container.appendChild(answerDiv);
          // Re-attach listener only for the new like button
          const newLikeButton = answerDiv.querySelector('.like-answer-button');
          if(newLikeButton) {
              newLikeButton.addEventListener('click', function() {
                  const answerId = parseInt(this.dataset.answerId, 10);
                  if (!isNaN(answerId)) likeAnswer(answerId, this);
              });
          }
     }

    // --- Global Like/Unlike Functions ---

    async function toggleLikeQuestion(questionId, buttonElement) {
        if (!currentUser) { alert("Please log in to like questions."); return; }
        if (!buttonElement) return;

        const isCurrentlyLiked = myLikedQuestionIds.has(questionId);
        const action = isCurrentlyLiked ? 'Unlike' : 'Like';
        const originalText = buttonElement.innerHTML; // Store original button content

        buttonElement.disabled = true;
        buttonElement.innerHTML = `${action}ing...`; // Simple text feedback on button
        const feedbackSpan = document.getElementById(`like-feedback-${questionId}`);
        if (feedbackSpan) feedbackSpan.textContent = ''; // Clear previous feedback

        try {
            const response = await fetch(`/api/questions/${questionId}/like`, { method: 'POST' });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || `Failed to ${action.toLowerCase()}`);

            // Update UI and State based on backend response 'liked' status
            const countSpan = document.getElementById(`question-likes-${questionId}`);
            if (countSpan) countSpan.textContent = data.likes; // Update count display

            if (data.liked) { // Liked successfully
                myLikedQuestionIds.add(questionId);
                buttonElement.classList.add('liked');
                buttonElement.innerHTML = '❤️ Liked';
                buttonElement.title = 'Unlike Question';
            } else { // Unliked successfully
                myLikedQuestionIds.delete(questionId);
                buttonElement.classList.remove('liked');
                buttonElement.innerHTML = '👍 Like';
                buttonElement.title = 'Like Question';
            }
            // Success feedback can be just the button state change

        } catch (error) {
             console.error(`Error ${action.toLowerCase()}ing question:`, error);
             if (feedbackSpan) { feedbackSpan.textContent = `Error!`; feedbackSpan.className = 'like-feedback status-message error'; }
             else { alert(`Error: ${error.message}`); }
             // Revert button text on error
             buttonElement.innerHTML = originalText;
        } finally {
             // Re-enable button (allows retry on error, does nothing if already liked/unliked)
             buttonElement.disabled = false;
             // Clear error feedback after a delay
             if (feedbackSpan?.textContent.includes('Error')) {
                 setTimeout(() => { if(feedbackSpan) feedbackSpan.textContent = ""; }, 2000);
             }
         }
    }

    async function likeAnswer(answerId, buttonElement) {
        if (!currentUser) { alert("Please log in to like answers."); return; }
        if (!buttonElement) return;

        // Prevent immediate re-click, but re-enable later
        buttonElement.disabled = true;
        const originalColor = buttonElement.style.color; // Store original color
        buttonElement.style.color = '#ccc'; // Indicate processing

        console.log(`Liking answer ${answerId}`);

        try {
            const response = await fetch(`/api/expertqa/answers/${answerId}/like`, { method: 'POST' });
            const data = await response.json();
            if (!response.ok) { throw new Error(data.detail || `Failed to like answer`); }

            const countSpan = document.getElementById(`answer-likes-${answerId}`);
            if (countSpan) countSpan.textContent = data.likes;
            // Add visual feedback - maybe change icon or color permanently for session if no unlike
            buttonElement.style.color = 'var(--success-color)'; // Turn green on success
            // You might disable it permanently for the session here if no unlike feature
            // buttonElement.disabled = true;

        } catch (error) {
            console.error("Error liking answer:", error);
            alert(`Like Error: ${error.message}`);
            buttonElement.style.color = originalColor; // Revert color on error
            buttonElement.disabled = false; // Re-enable on error
        } finally {
             // Re-enable after a short delay unless you want it permanently disabled after 1 like
              setTimeout(() => {
                 if (buttonElement.style.color !== 'var(--success-color)') { // Only re-enable if it wasn't a success
                      buttonElement.disabled = false;
                      buttonElement.style.color = originalColor;
                 }
             }, 1000);
        }
    }


    // --- Initial Page Load ---
    initializePage();

}); // End DOMContentLoaded