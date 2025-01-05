// static/js/quiz-timer.js
class QuizTimer {
    constructor(options) {
        this.timeRemaining = options.initialTime;
        this.quizId = options.quizId;
        this.timerDisplay = document.getElementById(options.displayId);
        this.warningThreshold = options.warningThreshold || 60;
        this.onTimeUp = options.onTimeUp;
        this.timerInterval = null;
        this.syncInterval = null;
        this.lastSync = Date.now();
        this.syncRetries = 0;
        this.maxSyncRetries = 3;
    }

    start() {
        this.updateDisplay();
        this.startInterval();
        this.startSync();
    }

    startInterval() {
        this.timerInterval = setInterval(() => {
            // Calculate time passed since last update using high-precision timing
            const now = Date.now();
            const timePassed = Math.floor((now - this.lastSync) / 1000);
            
            // Update time remaining
            this.timeRemaining = Math.max(0, this.timeRemaining - timePassed);
            this.lastSync = now;

            // Update display
            this.updateDisplay();

            // Check if time is up
            if (this.timeRemaining <= 0) {
                this.stop();
                if (this.onTimeUp) {
                    this.onTimeUp();
                }
                return;
            }

            // Warning check
            if (this.timeRemaining <= this.warningThreshold) {
                this.timerDisplay.parentElement.classList.add('warning');
            }
        }, 1000);
    }

    startSync() {
        // Sync with server every 30 seconds
        this.syncInterval = setInterval(() => {
            this.syncWithServer();
        }, 30000);
    }

    async syncWithServer() {
        try {
            const response = await fetch(`/quiz/${this.quizId}/time-check/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            // Only update if server time differs by more than 2 seconds
            if (Math.abs(data.timeRemaining - this.timeRemaining) > 2) {
                this.timeRemaining = data.timeRemaining;
                this.lastSync = Date.now();
                this.updateDisplay();
            }

            // Reset retry counter on successful sync
            this.syncRetries = 0;

        } catch (error) {
            console.error('Timer sync failed:', error);
            this.syncRetries++;
            
            // If we've failed multiple times, switch to local-only mode
            if (this.syncRetries >= this.maxSyncRetries) {
                console.warn('Switching to local-only timer mode after multiple sync failures');
                clearInterval(this.syncInterval);
            }
        }
    }

    stop() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
    }

    updateDisplay() {
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        this.timerDisplay.textContent = 
            `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    getRemainingTime() {
        return this.timeRemaining;
    }
}
