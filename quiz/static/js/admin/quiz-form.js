// quiz/static/js/admin/quiz-form.js

document.addEventListener('DOMContentLoaded', function() {
    const quizForm = document.getElementById('quizForm');
    const questionsContainer = document.getElementById('questions-container');
    const addQuestionBtn = document.getElementById('add-question');
    let questionCounter = document.querySelectorAll('.question-block').length;

    // Initialize Sortable
    if (questionsContainer) {
        new Sortable(questionsContainer, {
            animation: 150,
            handle: '.drag-handle',
            onEnd: updateQuestionOrder
        });
    }

    // Form validation
    function validateForm() {
        let isValid = true;
        const errors = [];

        // Clear previous errors
        document.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
            const feedback = el.parentNode.querySelector('.invalid-feedback');
            if (feedback) feedback.remove();
        });

        // Quiz Details Validation
        const titleInput = document.querySelector('input[name="title"]');
        const categorySelect = document.querySelector('select[name="category"]');
        const timeLimitInput = document.querySelector('input[name="time_limit"]');

        if (!titleInput?.value?.trim()) {
            markInvalid(titleInput, 'Quiz title is required');
            isValid = false;
        }

        if (!categorySelect?.value) {
            markInvalid(categorySelect, 'Please select a category');
            isValid = false;
        }

        if (!timeLimitInput?.value || timeLimitInput.value < 1) {
            markInvalid(timeLimitInput, 'Time limit must be at least 1 minute');
            isValid = false;
        }

        // Questions Validation
        const questionBlocks = document.querySelectorAll('.question-block');
        if (questionBlocks.length === 0) {
            errors.push('At least one question is required');
            isValid = false;
        }

        questionBlocks.forEach((block, index) => {
            const questionText = block.querySelector('input[name^="question_text"], input[name^="new_question_text"]');
            const answers = block.querySelectorAll('input[type="text"][name*="answer_text"]');
            const correctAnswer = block.querySelector('input[type="radio"]:checked');

            if (!questionText?.value?.trim()) {
                markInvalid(questionText, `Question ${index + 1} text is required`);
                isValid = false;
            }

            let validAnswers = 0;
            answers.forEach(answer => {
                if (answer.value.trim()) validAnswers++;
            });

            if (validAnswers < 2) {
                errors.push(`Question ${index + 1} must have at least 2 answers`);
                isValid = false;
            }

            if (!correctAnswer) {
                errors.push(`Question ${index + 1} must have a correct answer selected`);
                isValid = false;
            }
        });

        if (!isValid) {
            showErrors(errors);
        }

        return isValid;
    }

    // Form submission
    if (quizForm) {
        quizForm.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!validateForm()) {
                return;
            }

            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';

            fetch(this.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccess('Quiz saved successfully');
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 1000);
                } else {
                    showErrors(data.errors || ['Failed to save quiz']);
                }
            })
            .catch(error => {
                showErrors(['An error occurred while saving the quiz']);
                console.error('Error:', error);
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Save Quiz';
            });
        });
    }

    // Add Question functionality
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener('click', addNewQuestion);
    }

    // Helper functions
    function addNewQuestion() {
        questionCounter++;
        const questionBlock = document.createElement('div');
        questionBlock.className = 'question-block card mb-3';
        questionBlock.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <div class="drag-handle cursor-move">
                    <i class="fas fa-grip-vertical"></i>
                </div>
                <div class="question-number">Question #${questionCounter}</div>
                <div class="question-actions">
                    <button type="button" class="btn btn-sm btn-info preview-question">
                        <i class="fas fa-eye"></i> Preview
                    </button>
                    <button type="button" class="btn btn-sm btn-danger remove-question">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label class="form-label">Question Text</label>
                    <input type="text" name="new_question_text[]" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Description (Optional)</label>
                    <textarea name="new_question_description[]" class="form-control"></textarea>
                </div>
                <div class="mb-3">
                    <label class="form-label">Points</label>
                    <input type="number" name="new_question_points[]" value="1" class="form-control" min="1">
                </div>
                <div class="answers-container">
                    ${Array(4).fill(0).map((_, i) => `
                        <div class="mb-2">
                            <div class="input-group">
                                <div class="input-group-text">
                                    <input type="radio" name="new_correct_answer_${questionCounter}" value="${i}" ${i === 0 ? 'checked' : ''}>
                                </div>
                                <input type="text" name="new_answer_text[]" class="form-control" required
                                       placeholder="Answer ${i + 1}">
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        questionsContainer.appendChild(questionBlock);
        initializeQuestionBlock(questionBlock);
    }

    function initializeQuestionBlock(block) {
        const removeBtn = block.querySelector('.remove-question');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                block.remove();
                updateQuestionNumbers();
            });
        }

        const previewBtn = block.querySelector('.preview-question');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => previewQuestion(block));
        }
    }

    function updateQuestionNumbers() {
        document.querySelectorAll('.question-block').forEach((block, index) => {
            const numberEl = block.querySelector('.question-number');
            if (numberEl) numberEl.textContent = `Question #${index + 1}`;
        });
    }

    function updateQuestionOrder() {
        document.querySelectorAll('.question-block').forEach((block, index) => {
            const orderInput = block.querySelector('input[name^="question_order"]');
            if (orderInput) {
                orderInput.value = index + 1;
            } else {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = `question_order_${block.dataset.questionId || 'new_' + index}`;
                input.value = index + 1;
                block.appendChild(input);
            }
        });
    }

    // Initialize existing questions
    document.querySelectorAll('.question-block').forEach(initializeQuestionBlock);

    // Utility functions
    function markInvalid(element, message) {
        if (element) {
            element.classList.add('is-invalid');
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.textContent = message;
            element.parentNode.appendChild(feedback);
        }
    }

    function showErrors(errors) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger mt-3';
        alertDiv.innerHTML = `
            <strong>Please correct the following errors:</strong>
            <ul class="mb-0 mt-2">
                ${errors.map(error => `<li>${error}</li>`).join('')}
            </ul>
        `;
        quizForm.insertBefore(alertDiv, quizForm.firstChild);
    }

    function showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success mt-3';
        alertDiv.textContent = message;
        quizForm.insertBefore(alertDiv, quizForm.firstChild);
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
