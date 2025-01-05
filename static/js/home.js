// <!-- Custom JavaScript -->
// Animate stats numbers
const animateStats = () => {
    const statsNumbers = document.querySelectorAll('.stats-number');
    
    statsNumbers.forEach(stat => {
        const target = parseInt(stat.getAttribute('data-target'));
        const duration = 2000; // Animation duration in milliseconds
        const step = target / (duration / 16); // Update every 16ms (60fps)
        let current = 0;

	const updateNumber = () => {
    if (current < target) {
        current += step;
        if (current > target) current = target;

        // Format the number based on its magnitude
        let displayValue;
        if (target >= 1000000) {
            displayValue = (current / 1000000).toFixed(1) + 'M+';
        } else if (target >= 1000) {
            displayValue = Math.floor(current / 1000) + 'K+';
        } else if (target <= 100) {
            displayValue = Math.floor(current) + '%';
        } else {
            displayValue = Math.floor(current);
        }

        stat.textContent = displayValue;
        requestAnimationFrame(updateNumber);
    }
};
        // Start animation when element is in viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateNumber();
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        observer.observe(stat);
    });
};

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar background change on scroll
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
        navbar.style.boxShadow = '0 2px 15px rgba(0,0,0,0.1)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.boxShadow = 'none';
    }
});

// Feature cards hover effect enhancement
document.querySelectorAll('.feature-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
        card.querySelector('.feature-icon').style.transform = 'rotate(0deg) scale(1.1)';
    });
    
    card.addEventListener('mouseleave', () => {
        card.querySelector('.feature-icon').style.transform = 'rotate(-5deg) scale(1)';
    });
});

// Initialize animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    animateStats();
});

// Add loading animation for images
document.querySelectorAll('img').forEach(img => {
    img.addEventListener('load', () => {
        img.style.animation = 'fadeIn 0.5s ease-in';
    });
});

// Mobile menu toggle enhancement
const navbarToggler = document.querySelector('.navbar-toggler');
const navbarCollapse = document.querySelector('.navbar-collapse');

navbarToggler.addEventListener('click', () => {
    navbarCollapse.classList.toggle('show');
});

// Close mobile menu when clicking outside
document.addEventListener('click', (e) => {
    if (!navbarCollapse.contains(e.target) && !navbarToggler.contains(e.target)) {
        navbarCollapse.classList.remove('show');
    }
});


// FAQ Data
const faqData = [
    {
        id: 1,
        question: "How is my quiz score calculated?",
        answer: "Your quiz score is calculated as a percentage of correct answers. Each question carries equal weight, and your final score is the number of correct answers divided by the total number of questions, multiplied by 100. For example, if you get 4 out of 5 questions correct, your score would be 80%."
    },
    {
        id: 2,
        question: "Can I review my answers after completing the quiz?",
        answer: "Yes! You can review all your answers in the Question Summary section. Each question card shows your answer, the correct answer (if you got it wrong), and a helpful explanation. Use the 'View All Answers' button to expand all questions at once."
    },
    {
        id: 3,
        question: "How can I improve my score?",
        answer: "To improve your score, we recommend: 1) Carefully review the explanations provided for each question, 2) Pay special attention to topics where you made mistakes, 3) Use the 'Try Again' feature to practice with different questions, and 4) Take notes on challenging concepts for future reference."
    },
    {
        id: 4,
        question: "Can I share my quiz results?",
        answer: "Absolutely! Use the 'Share Result' button to share your achievement with friends and colleagues. You can share your results via social media, email, or generate a unique link to your results page."
    },
    {
        id: 5,
        question: "What happens if I lose internet connection during the quiz?",
        answer: "Don't worry! Your answers are automatically saved as you progress through the quiz. If you lose connection, simply reconnect and continue from where you left off. Your progress will be preserved."
    },
    {
        id: 6,
        question: "Are the questions randomized?",
        answer: "Yes, questions are randomly selected from our question bank each time you take a quiz. This helps ensure a unique learning experience and prevents memorization of answer patterns."
    }
];

// Initialize FAQ section
function initializeFAQ() {
    const accordion = document.getElementById('faqAccordion');
    
    // Generate FAQ items
    faqData.forEach((faq, index) => {
        const faqItem = `
            <div class="accordion-item fade-in" style="animation-delay: ${index * 0.1}s">
                <h2 class="accordion-header" id="heading${faq.id}">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                            data-bs-target="#collapse${faq.id}" aria-expanded="false" 
                            aria-controls="collapse${faq.id}">
                        ${faq.question}
                    </button>
                </h2>
                <div id="collapse${faq.id}" class="accordion-collapse collapse" 
                     aria-labelledby="heading${faq.id}" data-bs-parent="#faqAccordion">
                    <div class="accordion-body">
                        ${faq.answer}
                    </div>
                </div>
            </div>
        `;
        accordion.innerHTML += faqItem;
    });

    // Initialize search functionality
    const searchInput = document.getElementById('faqSearch');
    searchInput.addEventListener('input', handleSearch);
}

// Handle FAQ search
function handleSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    const faqItems = document.querySelectorAll('.accordion-item');
    let hasResults = false;

    faqItems.forEach(item => {
        const question = item.querySelector('.accordion-button').textContent.toLowerCase();
        const answer = item.querySelector('.accordion-body').textContent.toLowerCase();

        if (question.includes(searchTerm) || answer.includes(searchTerm)) {
            item.style.display = 'block';
            highlightText(item, searchTerm);
            hasResults = true;
        } else {
            item.style.display = 'none';
        }
    });

    // Show/hide no results message
    const existingNoResults = document.querySelector('.no-results');
    if (!hasResults) {
        if (!existingNoResults) {
            const noResults = `
                <div class="no-results fade-in">
                    <i class="fas fa-search mb-3" style="font-size: 2rem; color: #6c757d;"></i>
                    <p class="mt-2">No matching questions found. Try a different search term.</p>
                </div>
            `;
            document.getElementById('faqAccordion').insertAdjacentHTML('afterend', noResults);
        }
    } else if (existingNoResults) {
        existingNoResults.remove();
    }
}

// Highlight search terms in text
function highlightText(item, searchTerm) {
    if (searchTerm === '') {
        // Remove existing highlights
        item.innerHTML = item.innerHTML.replace(/<mark class="faq-highlight">|<\/mark>/g, '');
        return;
    }

    const question = item.querySelector('.accordion-button');
    const answer = item.querySelector('.accordion-body');
    
    [question, answer].forEach(element => {
        const text = element.innerHTML;
        const regex = new RegExp(searchTerm, 'gi');
        element.innerHTML = text.replace(regex, match => `<mark class="faq-highlight">${match}</mark>`);
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeFAQ);
