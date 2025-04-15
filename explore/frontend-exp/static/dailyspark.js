document.addEventListener('DOMContentLoaded', () => {
    const submitAnswerForm = document.getElementById('submit-answer-form');
    const pastQuestionListDiv = document.getElementById('past-question-list');
    const currentQuestionDiv = document.getElementById('current-question');

    // Fetch today's question
    fetch('/api/daily-spark/today')
        .then(response => response.json())
        .then(data => {
            currentQuestionDiv.innerHTML = `
                <p><strong>Company:</strong> ${data.company}, <strong>Role:</strong> ${data.role}</p>
                <p><strong>Question:</strong> ${data.question}</p>
            `;
        })
        .catch(error => console.error('Error fetching today\'s question:', error));

    // Fetch top 5 liked questions
    fetch('/api/daily-spark/top-liked')
        .then(response => response.json())
        .then(questions => {
            questions.forEach(question => {
                const questionDiv = document.createElement('div');
                questionDiv.classList.add('past-question-item');
                questionDiv.innerHTML = `
                    <div class="past-question-header">
                        <strong>Company:</strong> ${question.company}, <strong>Role:</strong> ${question.role}
                    </div>
                    <div class="past-question-text">${question.question}</div>
                    <div class="past-answers-container">
                        <h3>Answers:</h3>
                        <div id="past-answers-${question.id}">
                            ${question.answers.map(answer => `
                                <div class="past-answer-item">
                                    <span><strong>${answer.user}:</strong> ${answer.text}</span>
                                    <div class="vote-buttons">
                                        <button onclick="upvoteAnswer('${question.id}', '${answer.id}')">&#x1F44D;</button>
                                        <span class="vote-count" id="vote-count-${question.id}-${answer.id}">${answer.votes}</span>
                                        <button onclick="downvoteAnswer('${question.id}', '${answer.id}')">&#x1F44E;</button>
                                    </div>
                                </div>
                            `).join('')}
                            ${question.answers.length === 0 ? '<p>No answers yet.</p>' : ''}
                        </div>
                    </div>
                `;
                pastQuestionListDiv.appendChild(questionDiv);
            });
        })
        .catch(error => console.error('Error fetching top liked questions:', error));

    submitAnswerForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const answerText = document.getElementById('answer-text').value.trim();
        if (answerText) {
            // Send answer/question to the backend
            fetch('/api/daily-spark/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: answerText }),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Submission successful:', data);
                alert('Your submission has been recorded!');
                document.getElementById('answer-text').value = '';
            })
            .catch(error => console.error('Error submitting answer/question:', error));
        } else {
            alert('Please enter your answer or question.');
        }
    });
});

function upvoteAnswer(questionId, answerId) {
    fetch(`/api/daily-spark/upvote/${questionId}/${answerId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            document.getElementById(`vote-count-${questionId}-${answerId}`).textContent = data.votes;
        })
        .catch(error => console.error('Error upvoting answer:', error));
}

function downvoteAnswer(questionId, answerId) {
    fetch(`/api/daily-spark/downvote/${questionId}/${answerId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            document.getElementById(`vote-count-${questionId}-${answerId}`).textContent = data.votes;
        })
        .catch(error => console.error('Error downvoting answer:', error));
}
