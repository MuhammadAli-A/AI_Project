// AI Interview Analyzer - Frontend JavaScript

let isRecording = false;
let statsInterval = null;

// Start recording
async function startRecording() {
    try {
        const response = await fetch('/start_recording', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            isRecording = true;
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('reportBtn').disabled = true;
            document.getElementById('recordingIndicator').classList.add('active');
            
            // Start polling for statistics
            statsInterval = setInterval(updateStats, 1000);
            
            showNotification('Interview started! Good luck!', 'success');
        }
    } catch (error) {
        console.error('Error starting recording:', error);
        showNotification('Error starting interview', 'error');
    }
}

// Stop recording
async function stopRecording() {
    try {
        const response = await fetch('/stop_recording', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            isRecording = false;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('reportBtn').disabled = false;
            document.getElementById('recordingIndicator').classList.remove('active');
            
            // Stop polling
            if (statsInterval) {
                clearInterval(statsInterval);
                statsInterval = null;
            }
            
            showNotification('Interview completed! View your report.', 'success');
            
            // Auto-open report
            setTimeout(() => viewReport(), 1000);
        }
    } catch (error) {
        console.error('Error stopping recording:', error);
        showNotification('Error stopping interview', 'error');
    }
}

// Update statistics
async function updateStats() {
    try {
        const response = await fetch('/get_stats');
        const data = await response.json();
        
        // Update eye contact
        const eyeContact = data.face.eye_contact_percentage || 0;
        document.getElementById('eyeContact').textContent = eyeContact.toFixed(1) + '%';
        document.getElementById('eyeContactRating').textContent = data.face.eye_contact_rating || 'N/A';
        document.getElementById('eyeContactProgress').style.width = eyeContact + '%';
        
        // Update emotion
        const emotion = data.face.dominant_emotion || 'N/A';
        document.getElementById('emotion').textContent = capitalizeFirst(emotion);
        
        // Update motion
        const motionFreq = data.motion.motion_frequency || 0;
        document.getElementById('motionLevel').textContent = motionFreq.toFixed(1) + '%';
        document.getElementById('motionActivity').textContent = capitalizeFirst(data.motion.activity_level || 'N/A');
        document.getElementById('motionProgress').style.width = motionFreq + '%';
        
        // Update face detection
        const faceDetected = data.face.face_detected;
        document.getElementById('faceStatus').textContent = faceDetected ? '✓ Detected' : '✗ Not Detected';
        document.getElementById('faceStatus').style.color = faceDetected ? 'var(--success-color)' : 'var(--danger-color)';
        
        // Update speech analysis if available
        if (data.speech && data.speech.dominant_emotion) {
            const speechEmotion = data.speech.dominant_emotion || 'N/A';
            document.getElementById('speechEmotion').textContent = capitalizeFirst(speechEmotion);
            
            const positivePercent = data.speech.positive_emotion_percentage || 0;
            document.getElementById('speechPositivity').textContent = positivePercent.toFixed(1) + '%';
            document.getElementById('speechProgress').style.width = positivePercent + '%';
            
            // Show speech card if hidden
            const speechCard = document.getElementById('speechCard');
            if (speechCard && speechCard.style.display === 'none') {
                speechCard.style.display = 'block';
            }
        }
        
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// View report
async function viewReport() {
    const modal = document.getElementById('reportModal');
    const content = document.getElementById('reportContent');
    
    modal.style.display = 'block';
    content.innerHTML = '<div class="loading">Loading report...</div>';
    
    try {
        const response = await fetch('/get_report');
        const report = await response.json();
        
        if (report.status === 'error') {
            content.innerHTML = `<div class="loading">${report.message}</div>`;
            return;
        }
        
        // Generate report HTML
        const reportHTML = generateReportHTML(report);
        content.innerHTML = reportHTML;
        
    } catch (error) {
        console.error('Error loading report:', error);
        content.innerHTML = '<div class="loading">Error loading report</div>';
    }
}

// Generate report HTML
function generateReportHTML(report) {
    const scores = report.scores;
    const session = report.session_info;
    
    return `
        <div class="report-section">
            <h3>Session Information</h3>
            <p><strong>Duration:</strong> ${scores.duration_minutes.toFixed(2)} minutes</p>
            <p><strong>Generated:</strong> ${new Date(report.generated_at).toLocaleString()}</p>
        </div>
        
        <div class="report-section">
            <h3>Overall Performance</h3>
            <div class="score-grid">
                <div class="score-item">
                    <h4>Overall Score</h4>
                    <div class="score" style="color: ${getScoreColor(scores.overall_score)}">${scores.overall_score}</div>
                    <p>${scores.rating}</p>
                </div>
                <div class="score-item">
                    <h4>Eye Contact</h4>
                    <div class="score">${scores.eye_contact_score}</div>
                </div>
                <div class="score-item">
                    <h4>Body Language</h4>
                    <div class="score">${scores.body_language_score}</div>
                </div>
                <div class="score-item">
                    <h4>Emotion</h4>
                    <div class="score">${scores.emotion_score}</div>
                </div>
                <div class="score-item">
                    <h4>Engagement</h4>
                    <div class="score">${scores.engagement_score}</div>
                </div>
                ${scores.speech_score !== undefined ? `
                <div class="score-item">
                    <h4>Speech Analysis</h4>
                    <div class="score">${scores.speech_score}</div>
                </div>
                ` : ''}
            </div>
        </div>
        
        <div class="report-section">
            <h3>Detailed Analysis</h3>
            <div class="recommendations">
                <p><strong>Face Detection Rate:</strong> ${report.face_analysis.face_detection_rate.toFixed(1)}%</p>
                <p><strong>Average Eye Contact:</strong> ${report.face_analysis.average_eye_contact.toFixed(1)}%</p>
                <p><strong>Average Motion:</strong> ${report.motion_analysis.average_motion.toFixed(1)}%</p>
                ${report.speech_analysis && report.speech_analysis.available ? `
                <p><strong>Speech Clarity:</strong> ${report.speech_analysis.average_clarity.toFixed(1)}%</p>
                <p><strong>Vocal Confidence:</strong> ${report.speech_analysis.average_confidence.toFixed(1)}%</p>
                <p><strong>Dominant Speech Emotion:</strong> ${capitalizeFirst(report.speech_analysis.dominant_emotion)}</p>
                ` : '<p><em>Speech analysis not available</em></p>'}
            </div>
        </div>
        
        <div class="report-section">
            <h3>Recommendations</h3>
            <div class="recommendations">
                <ul>
                    ${scores.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
}

// Close report modal
function closeReport() {
    document.getElementById('reportModal').style.display = 'none';
}

// Show notification
function showNotification(message, type) {
    // Simple alert for now - can be enhanced with a toast library
    console.log(`${type.toUpperCase()}: ${message}`);
}

// Utility functions
function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function getScoreColor(score) {
    if (score >= 85) return 'var(--success-color)';
    if (score >= 70) return 'var(--primary-color)';
    if (score >= 55) return 'var(--warning-color)';
    return 'var(--danger-color)';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('reportModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Interview Analyzer initialized');
    
    // Set initial stats
    document.getElementById('eyeContact').textContent = '--';
    document.getElementById('emotion').textContent = '--';
    document.getElementById('motionLevel').textContent = '--';
    document.getElementById('faceStatus').textContent = '--';
    document.getElementById('speechEmotion').textContent = '--';
    document.getElementById('speechPositivity').textContent = '--';
});
