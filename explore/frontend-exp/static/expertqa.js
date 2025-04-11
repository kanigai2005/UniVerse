console.log('JavaScript file loaded!'); // Confirm script is loading

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');
    loadPopularQuestions();
    loadMyQuestions();
});

async function loadPopularQuestions() {
    console.log('loadPopularQuestions called'); // Debugging
    try {
        const response = await fetch("/api/questions/popular");
        console.log('Popular questions response:', response); // Debugging
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Failed to fetch popular questions: ${response.status} - ${errorData?.detail || 'Unknown error'}`);
        }
        const questions = await response.json();
        console.log('Popular questions data:', questions); // Debugging
        const questionsContainer = document.getElementById("questions-list");
        questionsContainer.innerHTML = "";

        questions.forEach(question => {
            const questionDiv = document.createElement("div");
            questionDiv.classList.add("question-box");
            questionDiv.innerHTML = `
                <p>${question.question_text} (Likes: ${question.likes})</p>
                <div class="vote-buttons">
                    <button class="like-button" data-question-id="${question.id}">Like</button>
                    <span class="like-feedback" id="like-feedback-${question.id}"></span>
                </div>
            `;
            questionsContainer.appendChild(questionDiv);
        });

        attachLikeButtonListeners();

    } catch (error) {
        console.error("Error loading popular questions:", error);
        document.getElementById("questions-list").innerHTML = `<p class="error-message">Error loading questions: ${error.message}</p>`;
    }
}

function attachLikeButtonListeners() {
    const likeButtons = document.querySelectorAll("#questions-list .like-button");
    likeButtons.forEach(button => {
        button.addEventListener("click", async function() {
            const questionId = this.getAttribute("data-question-id");
            const likeButton = this;
            const feedbackSpan = document.getElementById(`like-feedback-${questionId}`);

            likeButton.disabled = true; // Disable button to prevent multiple clicks
            feedbackSpan.textContent = "Liking...";
            feedbackSpan.classList.remove("error-message", "success-message");

            try {
                const response = await fetch(`/api/questions/${questionId}/like`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        // Include authorization headers if needed
                    },
                });
                if (response.ok) {
                    const data = await response.json();
                    console.log("Like successful:", data);
                    feedbackSpan.textContent = "Liked!";
                    feedbackSpan.classList.add("success-message");
                    // Optionally update the like count without reloading:
                    const questionParagraph = likeButton.closest('.question-box').querySelector('p');
                    if (questionParagraph) {
                        const currentLikes = parseInt(questionParagraph.textContent.match(/Likes: (\\d+)/)[1]);
                        questionParagraph.textContent = questionParagraph.textContent.replace(`Likes: ${currentLikes}`, `Likes: ${currentLikes + 1}`);
                    }
                } else {
                    const errorData = await response.json();
                    console.error("Failed to like question:", response.status, errorData);
                    feedbackSpan.textContent = `Failed: ${errorData?.detail || 'Error liking'}`;
                    feedbackSpan.classList.add("error-message");
                }
            } catch (error) {
                console.error("Error liking question:", error);
                feedbackSpan.textContent = `Error: ${error.message}`;
                feedbackSpan.classList.add("error-message");
            } finally {
                setTimeout(() => {
                    likeButton.disabled = false;
                    feedbackSpan.textContent = "";
                    feedbackSpan.classList.remove("success-message", "error-message");
                }, 1500); // Re-enable after a short delay
            }
        });
    });
}

async function postNewQuestion() {
    const questionInput = document.getElementById("question-input");
    const questionText = questionInput.value.trim();
    const postButton = document.querySelector('#question-form button[type="submit"]');
    const postFeedback = document.querySelector('.post-feedback');
    postButton.disabled = true;
    postFeedback.textContent = "Posting...";
    postFeedback.classList.remove("error-message", "success-message");

    if (questionText) {
        try {
            const response = await fetch("/api/questions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ question_text: questionText }),
            });

            if (response.ok) {
                const newQuestion = await response.json();
                console.log("Question posted:", newQuestion);
                questionInput.value = "";
                postFeedback.textContent = "Question posted successfully!";
                postFeedback.classList.add("success-message");
                loadMyQuestions();
                loadPopularQuestions();
            } else {
                const errorData = await response.json();
                console.error("Failed to post question:", response.status, errorData);
                postFeedback.textContent = `Failed to post: ${errorData?.detail || 'Error posting'}`;
                postFeedback.classList.add("error-message");
            }
        } catch (error) {
            console.error("Error posting question:", error);
            postFeedback.textContent = `Error: ${error.message}`;
            postFeedback.classList.add("error-message");
        } finally {
            setTimeout(() => {
                postButton.disabled = false;
                postFeedback.textContent = "";
                postFeedback.classList.remove("success-message", "error-message");
            }, 2000);
        }
    } else {
        postFeedback.textContent = "Please enter your question.";
        postFeedback.classList.add("error-message");
        postButton.disabled = false;
        setTimeout(() => postFeedback.textContent = "", 2000);
    }
}

async function loadMyQuestions() {
    console.log('loadMyQuestions called'); // Debugging
    const userId = getLoggedInUserId(); // Ensure this function correctly retrieves the user ID
    if (!userId) {
        console.warn("User ID not found. Cannot load user's questions.");
        document.getElementById("user-questions-list").innerHTML = "<p class='error-message'>Please log in to see your questions.</p>";
        return;
    }

    try {
        const response = await fetch(`/api/users/${userId}/questions`);
        console.log('My questions response:', response); // Debugging
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Failed to fetch your questions: ${response.status} - ${errorData?.detail || 'Unknown error'}`);
        }
        const myQuestions = await response.json();
        console.log('My questions data:', myQuestions); // Debugging
        const myQuestionsContainer = document.getElementById("user-questions-list");
        myQuestionsContainer.innerHTML = "";

        myQuestions.forEach(question => {
            const questionDiv = document.createElement("div");
            questionDiv.classList.add("question-box");
            const formattedDate = new Date(question.created_at).toLocaleDateString();
            questionDiv.innerHTML = `
                <p>${question.question_text} (Posted on: ${formattedDate})</p>
            `;
            myQuestionsContainer.appendChild(questionDiv);
        });

    } catch (error) {
        console.error("Error loading your questions:", error);
        document.getElementById("user-questions-list").innerHTML = `<p class="error-message">Error loading your questions: ${error.message}</p>`;
    }
}

// **Crucially, ensure this function correctly retrieves the logged-in user's ID.**
// Replace this with your actual authentication logic.
function getLoggedInUserId() {
    // Example using localStorage (you might use cookies, etc.)
    return localStorage.getItem('userId');
    // Or a hardcoded value for testing ONLY:
    // return 1;
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');
    loadPopularQuestions();
    loadMyQuestions();
});

document.getElementById("question-form").addEventListener("submit", function(event) {
    event.preventDefault();
    postNewQuestion();
});