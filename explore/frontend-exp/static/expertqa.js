document.addEventListener('DOMContentLoaded', () => {
    // ... (rest of the code)

    window.postAnswer = function(questionId) {
        const answerInput = document.getElementById(`answer-input-${questionId}`);
        const answerText = answerInput.value.trim();

        if (answerText === '') return;

        fetch(`http://127.0.0.1:8000/questions/${questionId}/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answer: answerText })
        })
        .then(response => {
            if (response.ok) {
                fetchQuestions();
                answerInput.value = '';
            } else {
                alert('Failed to post answer.');
            }
        });
    };

    function fetchQuestions() {
        fetch('http://127.0.0.1:8000/questions')
            .then(response => response.json())
            .then(questions => {
                questionsList.innerHTML = '';
                questions.forEach(question => {
                    const questionBox = document.createElement('div');
                    questionBox.classList.add('question-box');
                    questionBox.innerHTML = `
                        <p><strong>Q:</strong> ${question.question}</p>
                        <div class="answer">${question.answer ? question.answer : '<em>Waiting for community answers...</em>'}</div>
                        <div class="vote-buttons">
                            <button onclick="vote(this, 1, ${question.id})">👍 <span>${question.likes}</span></button>
                            <button onclick="vote(this, -1, ${question.id})">👎 <span>${question.dislikes}</span></button>
                        </div>
                        <textarea id="answer-input-${question.id}" placeholder="Type your answer here..."></textarea>
                        <button onclick="postAnswer(${question.id})">Post Answer</button>
                    `;
                    questionsList.appendChild(questionBox);
                });
                displayUserQuestions();
            });
    }

    // ... (rest of the code)
});