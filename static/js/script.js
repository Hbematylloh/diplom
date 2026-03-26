// Глобальные переменные
let currentAnswers = {};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeQuestions();
    initializeButtons();
    loadSavedProgress();
});

// Инициализация обработчиков для вопросов
function initializeQuestions() {
    const radioButtons = document.querySelectorAll('input[type="radio"]');

    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            const questionId = this.dataset.question;
            const answerValue = parseInt(this.value);
            handleAnswer(questionId, answerValue);
        });
    });
}

// Инициализация кнопок
function initializeButtons() {
    // Кнопка "Показать ответы"
    const showAnswersBtn = document.getElementById('showAnswersBtn');
    if (showAnswersBtn) {
        showAnswersBtn.addEventListener('click', toggleAnswers);
    }

    // Кнопка "Сбросить"
    const resetBtn = document.getElementById('resetTicketBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetTicket);
    }
}

// Обработка ответа пользователя
async function handleAnswer(questionId, answerValue) {
    const questionCard = document.querySelector(`[data-question-id="${questionId}"]`);
    const correctAnswer = parseInt(questionCard.dataset.correct);

    // Отправляем ответ на сервер
    try {
        const response = await fetch('/api/check-answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question_id: questionId,
                answer: answerValue,
                ticket_number: window.ticketNumber
            })
        });

        const data = await response.json();

        // Визуальное отображение результата
        highlightAnswer(questionId, answerValue, correctAnswer);

        // Показываем объяснение
        showExplanation(questionId, data.explanation);

        // Сохраняем результат
        currentAnswers[questionId] = {
            userAnswer: answerValue,
            isCorrect: data.correct
        };

        // Обновляем статистику
        updateStatistics();

    } catch (error) {
        console.error('Ошибка при проверке ответа:', error);
    }
}

// Подсветка правильного/неправильного ответа
function highlightAnswer(questionId, userAnswer, correctAnswer) {
    const questionCard = document.querySelector(`[data-question-id="${questionId}"]`);
    const answerItems = questionCard.querySelectorAll('.answer-item');

    // Сбрасываем классы
    answerItems.forEach(item => {
        item.classList.remove('correct', 'wrong', 'selected-correct', 'selected-wrong');
    });

    // Подсвечиваем правильный ответ
    answerItems.forEach(item => {
        const radio = item.querySelector('input');
        if (parseInt(radio.value) === correctAnswer) {
            item.classList.add('correct');
        }
    });

    // Подсвечиваем ответ пользователя
    answerItems.forEach(item => {
        const radio = item.querySelector('input');
        if (parseInt(radio.value) === userAnswer) {
            if (userAnswer === correctAnswer) {
                item.classList.add('selected-correct');
            } else {
                item.classList.add('selected-wrong');
            }
        }
    });
}

// Показать объяснение
function showExplanation(questionId, explanation) {
    const explanationDiv = document.getElementById(`explanation_${questionId}`);
    if (explanationDiv) {
        const explanationText = explanationDiv.querySelector('p');
        if (explanationText) {
            explanationText.textContent = explanation || 'Пояснение отсутствует.';
        }
        explanationDiv.classList.remove('hidden');
    }
}

// Переключение показа ответов
function toggleAnswers() {
    const explanations = document.querySelectorAll('.explanation');
    const button = document.getElementById('showAnswersBtn');

    // Переключаем класс
    explanations.forEach(exp => {
        exp.classList.toggle('hidden');
    });

    if (button) {
        // Считаем, сколько элементов НЕ скрыто (не имеют класса 'hidden')
        const visibleExplanations = Array.from(explanations).filter(exp => !exp.classList.contains('hidden'));

        // Если видимых объяснений больше 0, значит мы их показали, и кнопка должна говорить "Скрыть"
        if (visibleExplanations.length > 0) {
            button.textContent = 'Скрыть ответы';
        } else {
            button.textContent = 'Показать ответы';
        }
    }
}

// Сброс прогресса по билету
async function resetTicket() {
    if (!confirm('Сбросить весь прогресс по этому билету?')) {
        return;
    }

    try {
        const response = await fetch(`/api/reset-ticket/${window.ticketNumber}`, {
            method: 'POST'
        });

        if (response.ok) {
            // Очищаем локальное состояние
            currentAnswers = {};

            // Сбрасываем радио-кнопки
            document.querySelectorAll('input[type="radio"]').forEach(radio => {
                radio.checked = false;
            });

            // Скрываем объяснения
            document.querySelectorAll('.explanation').forEach(exp => {
                exp.classList.add('hidden');
            });

            // Сбрасываем классы
            document.querySelectorAll('.answer-item').forEach(item => {
                item.classList.remove('correct', 'wrong', 'selected-correct', 'selected-wrong');
            });

            alert('Прогресс сброшен');
        }
    } catch (error) {
        console.error('Ошибка при сбросе:', error);
    }
}

// Загрузка сохраненного прогресса
function loadSavedProgress() {
    // Здесь можно загрузить прогресс из localStorage или с сервера
    const savedAnswers = localStorage.getItem(`ticket_${window.ticketNumber}_progress`);
    if (savedAnswers) {
        try {
            const answers = JSON.parse(savedAnswers);
            Object.entries(answers).forEach(([questionId, data]) => {
                const radio = document.querySelector(`input[name="question_${questionId}"][value="${data.userAnswer}"]`);
                if (radio) {
                    radio.checked = true;
                    handleAnswer(questionId, data.userAnswer);
                }
            });
        } catch (e) {
            console.error('Ошибка загрузки прогресса:', e);
        }
    }
}

// Обновление статистики
function updateStatistics() {
    const totalQuestions = Object.keys(currentAnswers).length;
    const correctAnswers = Object.values(currentAnswers).filter(a => a.isCorrect).length;

    // Можно добавить отображение статистики где-нибудь на странице
    console.log(`Прогресс: ${correctAnswers}/${totalQuestions} правильных ответов`);
}

// Сохранение прогресса перед уходом со страницы
window.addEventListener('beforeunload', function() {
    if (Object.keys(currentAnswers).length > 0) {
        localStorage.setItem(`ticket_${window.ticketNumber}_progress`, JSON.stringify(currentAnswers));
    }
});