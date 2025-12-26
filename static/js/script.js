/**
 * AI Interview Analyzer - Frontend Controller
 * Professional Real-time Interview Analysis System
 */

class InterviewAnalyzer {
    constructor() {
        this.isRecording = false;
        this.sessionStartTime = null;
        this.timerInterval = null;
        this.statsInterval = null;
        this.videoFeedInterval = null;
        
        // DOM Elements
        this.elements = {
            startBtn: document.getElementById('startBtn'),
            stopBtn: document.getElementById('stopBtn'),
            reportBtn: document.getElementById('reportBtn'),
            sessionTimer: document.getElementById('sessionTimer'),
            recordingBadge: document.getElementById('recordingBadge'),
            videoFeed: document.getElementById('videoFeed'),
            
            // Analytics
            facialEmotion: document.getElementById('facialEmotion'),
            facialConfidence: document.getElementById('facialConfidence'),
            facialProgress: document.getElementById('facialProgress'),
            speechEmotion: document.getElementById('speechEmotion'),
            speechConfidence: document.getElementById('speechConfidence'),
            speechProgress: document.getElementById('speechProgress'),
            eyeContact: document.getElementById('eyeContact'),
            eyeProgress: document.getElementById('eyeProgress'),
            positivity: document.getElementById('positivity'),
            positivityProgress: document.getElementById('positivityProgress'),
            confidence: document.getElementById('confidence'),
            confidenceProgress: document.getElementById('confidenceProgress'),
            
            // Module status dots
            facialStatus: document.getElementById('facialStatus'),
            speechStatus: document.getElementById('speechStatus'),
            fusionStatus: document.getElementById('fusionStatus'),
            
            // Modal
            modal: document.getElementById('reportModal'),
            modalClose: document.getElementById('modalClose'),
            modalBackdrop: document.querySelector('.modal-backdrop'),
            reportContent: document.getElementById('reportContent')
        };
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateButtonStates();
        this.checkModulesStatus();
    }
    
    bindEvents() {
        // Control buttons
        this.elements.startBtn.addEventListener('click', () => this.startRecording());
        this.elements.stopBtn.addEventListener('click', () => this.stopRecording());
        this.elements.reportBtn.addEventListener('click', () => this.viewReport());
        
        // Modal events
        this.elements.modalClose?.addEventListener('click', () => this.closeModal());
        this.elements.modalBackdrop?.addEventListener('click', () => this.closeModal());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeModal();
            if (e.key === 'r' && e.ctrlKey) {
                e.preventDefault();
                if (!this.isRecording) this.startRecording();
                else this.stopRecording();
            }
        });
    }
    
    updateButtonStates() {
        this.elements.startBtn.disabled = this.isRecording;
        this.elements.stopBtn.disabled = !this.isRecording;
        this.elements.reportBtn.disabled = this.isRecording;
        
        if (this.isRecording) {
            this.elements.recordingBadge.classList.add('active');
        } else {
            this.elements.recordingBadge.classList.remove('active');
        }
    }
    
    async checkModulesStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            if (data.facial_model) {
                this.elements.facialStatus?.classList.add('active');
            }
            if (data.speech_model) {
                this.elements.speechStatus?.classList.add('active');
            }
            if (data.fusion_enabled) {
                this.elements.fusionStatus?.classList.add('active');
            }
        } catch (error) {
            console.log('Could not fetch module status');
        }
    }
    
    async startRecording() {
        try {
            this.showNotification('Initializing AI analysis...', 'info');
            
            const response = await fetch('/start', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'started') {
                this.isRecording = true;
                this.sessionStartTime = Date.now();
                this.updateButtonStates();
                
                // Start video feed
                this.startVideoFeed();
                
                // Start timer
                this.startTimer();
                
                // Start fetching stats
                this.startStatsUpdates();
                
                // Add recording animation to icons
                this.setIconsRecording(true);
                
                this.showNotification('Analysis started successfully!', 'success');
            } else {
                throw new Error(data.error || 'Failed to start');
            }
        } catch (error) {
            this.showNotification('Failed to start: ' + error.message, 'error');
        }
    }
    
    async stopRecording() {
        try {
            const response = await fetch('/stop', { method: 'POST' });
            const data = await response.json();
            
            this.isRecording = false;
            this.updateButtonStates();
            
            // Stop intervals
            this.stopTimer();
            this.stopStatsUpdates();
            this.stopVideoFeed();
            
            // Remove recording animation from icons
            this.setIconsRecording(false);
            
            this.showNotification('Analysis stopped. Report available!', 'success');
        } catch (error) {
            this.showNotification('Error stopping: ' + error.message, 'error');
        }
    }
    
    setIconsRecording(isRecording) {
        // Get all card icons and toggle recording class
        const cardIcons = document.querySelectorAll('.card-icon');
        cardIcons.forEach(icon => {
            if (isRecording) {
                icon.classList.add('recording');
            } else {
                icon.classList.remove('recording');
            }
        });
    }
    
    startVideoFeed() {
        // Set video feed source
        this.elements.videoFeed.src = '/video_feed';
        this.elements.videoFeed.style.display = 'block';
    }
    
    stopVideoFeed() {
        this.elements.videoFeed.src = '';
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.sessionStartTime) / 1000);
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;
            
            this.elements.sessionTimer.textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
    
    startStatsUpdates() {
        this.statsInterval = setInterval(() => this.fetchStats(), 500);
    }
    
    stopStatsUpdates() {
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
            this.statsInterval = null;
        }
    }
    
    async fetchStats() {
        try {
            const response = await fetch('/stats');
            const data = await response.json();
            this.updateAnalytics(data);
        } catch (error) {
            console.log('Stats fetch error:', error);
        }
    }
    
    updateAnalytics(data) {
        // Facial emotion
        if (data.facial) {
            const facialConf = Math.round(data.facial.confidence * 100);
            this.elements.facialEmotion.textContent = this.capitalizeFirst(data.facial.emotion);
            this.elements.facialConfidence.textContent = `${facialConf}%`;
            this.elements.facialProgress.style.width = `${facialConf}%`;
        }
        
        // Speech emotion
        if (data.speech) {
            const speechConf = Math.round(data.speech.confidence * 100);
            this.elements.speechEmotion.textContent = this.capitalizeFirst(data.speech.emotion);
            this.elements.speechConfidence.textContent = `${speechConf}%`;
            this.elements.speechProgress.style.width = `${speechConf}%`;
        }
        
        // Eye contact
        if (data.eye_contact !== undefined) {
            const eyeVal = Math.round(data.eye_contact * 100);
            this.elements.eyeContact.textContent = `${eyeVal}%`;
            this.elements.eyeProgress.style.width = `${eyeVal}%`;
        }
        
        // Positivity
        if (data.positivity !== undefined) {
            const posVal = Math.round(data.positivity * 100);
            this.elements.positivity.textContent = `${posVal}%`;
            this.elements.positivityProgress.style.width = `${posVal}%`;
        }
        
        // Overall confidence
        if (data.confidence !== undefined) {
            const confVal = Math.round(data.confidence * 100);
            this.elements.confidence.textContent = `${confVal}%`;
            this.elements.confidenceProgress.style.width = `${confVal}%`;
        }
    }
    
    capitalizeFirst(str) {
        if (!str) return 'Analyzing...';
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }
    
    async viewReport() {
        this.openModal();
        this.elements.reportContent.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Generating AI Report...</p>
            </div>
        `;
        
        try {
            const response = await fetch('/report');
            const data = await response.json();
            this.renderReport(data);
        } catch (error) {
            this.elements.reportContent.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to generate report. Please try again.</p>
                </div>
            `;
        }
    }
    
    renderReport(data) {
        const facialScore = data.facial?.overall_score || 0;
        const speechScore = data.speech?.overall_score || 0;
        const eyeScore = data.eye_contact || 0;
        const overallScore = data.overall_score || ((facialScore + speechScore) / 2);
        
        const getScoreColor = (score) => {
            if (score >= 80) return 'var(--accent-green)';
            if (score >= 60) return 'var(--accent-orange)';
            return 'var(--accent-red)';
        };
        
        const getGrade = (score) => {
            if (score >= 90) return 'A+';
            if (score >= 80) return 'A';
            if (score >= 70) return 'B';
            if (score >= 60) return 'C';
            return 'D';
        };
        
        this.elements.reportContent.innerHTML = `
            <div class="report-section">
                <h3><i class="fas fa-chart-bar"></i> Overall Performance</h3>
                <div class="score-grid">
                    <div class="score-item">
                        <h4>Facial Analysis</h4>
                        <div class="score" style="color: ${getScoreColor(facialScore)}">${Math.round(facialScore)}%</div>
                        <p>Grade: ${getGrade(facialScore)}</p>
                    </div>
                    <div class="score-item">
                        <h4>Speech Analysis</h4>
                        <div class="score" style="color: ${getScoreColor(speechScore)}">${Math.round(speechScore)}%</div>
                        <p>Grade: ${getGrade(speechScore)}</p>
                    </div>
                    <div class="score-item">
                        <h4>Eye Contact</h4>
                        <div class="score" style="color: ${getScoreColor(eyeScore * 100)}">${Math.round(eyeScore * 100)}%</div>
                        <p>Grade: ${getGrade(eyeScore * 100)}</p>
                    </div>
                    <div class="score-item">
                        <h4>Overall Score</h4>
                        <div class="score" style="color: ${getScoreColor(overallScore)}">${Math.round(overallScore)}%</div>
                        <p>Grade: ${getGrade(overallScore)}</p>
                    </div>
                </div>
            </div>
            
            <div class="report-section">
                <h3><i class="fas fa-face-smile"></i> Facial Emotion Breakdown</h3>
                <div class="emotion-breakdown">
                    ${this.renderEmotionBreakdown(data.facial?.emotions)}
                </div>
            </div>
            
            <div class="report-section">
                <h3><i class="fas fa-microphone"></i> Speech Emotion Breakdown</h3>
                <div class="emotion-breakdown">
                    ${this.renderEmotionBreakdown(data.speech?.emotions)}
                </div>
            </div>
            
            <div class="report-section">
                <h3><i class="fas fa-lightbulb"></i> AI Recommendations</h3>
                <div class="recommendations">
                    ${this.generateRecommendations(data)}
                </div>
            </div>
        `;
    }
    
    renderEmotionBreakdown(emotions) {
        if (!emotions || Object.keys(emotions).length === 0) {
            return '<p style="color: var(--text-muted)">No emotion data available</p>';
        }
        
        return Object.entries(emotions).map(([emotion, count]) => `
            <div class="emotion-item" style="
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 0.75rem;
                background: var(--bg-input);
                border-radius: 8px;
                margin-bottom: 0.5rem;
            ">
                <span style="min-width: 100px; font-weight: 500;">${this.capitalizeFirst(emotion)}</span>
                <div style="flex: 1; height: 8px; background: var(--border-color); border-radius: 4px;">
                    <div style="width: ${Math.min(count * 10, 100)}%; height: 100%; background: var(--primary); border-radius: 4px;"></div>
                </div>
                <span style="min-width: 40px; text-align: right; color: var(--text-muted);">${count}</span>
            </div>
        `).join('');
    }
    
    generateRecommendations(data) {
        const recommendations = [];
        const facialScore = data.facial?.overall_score || 50;
        const speechScore = data.speech?.overall_score || 50;
        
        if (facialScore < 70) {
            recommendations.push({
                title: 'Facial Expression',
                text: 'Try to maintain more positive facial expressions during the interview. Practice smiling naturally and showing engagement.'
            });
        }
        
        if (speechScore < 70) {
            recommendations.push({
                title: 'Voice Tone',
                text: 'Work on your vocal delivery. Try to speak with more enthusiasm and vary your tone to keep the interviewer engaged.'
            });
        }
        
        if ((data.eye_contact || 0) < 0.6) {
            recommendations.push({
                title: 'Eye Contact',
                text: 'Maintain better eye contact with the camera. This helps build rapport and shows confidence in virtual interviews.'
            });
        }
        
        if (recommendations.length === 0) {
            recommendations.push({
                title: 'Excellent Performance!',
                text: 'You demonstrated strong interview skills across all areas. Keep up the great work!'
            });
        }
        
        return recommendations.map(rec => `
            <div class="rec-item">
                <strong><i class="fas fa-arrow-right"></i> ${rec.title}</strong>
                <p>${rec.text}</p>
            </div>
        `).join('');
    }
    
    openModal() {
        this.elements.modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
    
    closeModal() {
        this.elements.modal.style.display = 'none';
        document.body.style.overflow = '';
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.analyzer = new InterviewAnalyzer();
});

// Global functions for inline event handlers
function startRecording() {
    window.analyzer?.startRecording();
}

function stopRecording() {
    window.analyzer?.stopRecording();
}

function viewReport() {
    window.analyzer?.viewReport();
}

function closeModal() {
    window.analyzer?.closeModal();
}
