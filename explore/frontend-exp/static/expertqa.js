document.addEventListener('DOMContentLoaded', () => {
    const questionsList = document.getElementById('questions-list');
    const userQuestionsList = document.getElementById('user-questions-list');

    let userQuestions = []; // Store user's questions

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
                    `;
                    questionsList.appendChild(questionBox);
                });
                 displayUserQuestions();
            });
    }

    function displayUserQuestions() {
        userQuestionsList.innerHTML = '';
        userQuestions.forEach(question => {
            const questionBox = document.createElement('div');
            questionBox.classList.add('question-box');
            questionBox.innerHTML = `
                <p><strong>Q:</strong> ${question.question}</p>
                <div class="answer">${question.answer ? question.answer : '<em>Waiting for community answers...</em>'}</div>
                <div class="vote-buttons">
                    👍 <span>${question.likes}</span>
                </div>
            `;
            userQuestionsList.appendChild(questionBox);
        });
    }

    fetchQuestions();

    document.getElementById('question-form').addEventListener('submit', (event) => {
        event.preventDefault();
        const questionText = document.getElementById('question-input').value;
        if (questionText.trim() === '') return;

        fetch('http://127.0.0.1:8000/questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: questionText })
        })
        .then(response => {
            if (response.ok) {
                userQuestions.push({ question: questionText, likes: 0, dislikes: 0});
                fetchQuestions();
                document.getElementById('question-input').value = '';
            } else {
                alert('Failed to post question.');
            }
        });
    });

    window.vote = function(button, change, questionId) {
        fetch(`http://127.0.0.1:8000/questions/${questionId}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vote: change })
        })
        .then(response => {
            if (response.ok) {
                fetchQuestions();
            } else {
                alert('Failed to update vote.');
            }
        });
    };
});
