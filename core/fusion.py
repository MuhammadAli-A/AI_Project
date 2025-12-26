"""
Multimodal Fusion Module
Combines facial and speech emotion analysis for interview evaluation
Generates comprehensive candidate reports
"""
import numpy as np
from datetime import datetime
import json
import os


class MultimodalFusion:
    """
    Fuses facial and speech emotion analysis for comprehensive interview evaluation
    
    Fusion Weights:
    - Facial Emotion: 40%
    - Speech Emotion: 35%
    - Eye Contact: 15%
    - Vocal Confidence: 10%
    """
    
    # Emotion weights for interview appropriateness
    EMOTION_SCORES = {
        # Positive for interviews
        'Happy': 90,
        'Calm': 85,
        'Neutral': 75,
        
        # Neutral/Acceptable
        'Surprise': 60,
        'Surprised': 60,
        
        # Negative for interviews
        'Sad': 40,
        'Fear': 35,
        'Fearful': 35,
        'Angry': 25,
        'Disgust': 20
    }
    
    def __init__(self):
        """Initialize fusion module"""
        self.session_start = None
        self.session_end = None
        self.face_data = []
        self.speech_data = []
    
    def start_session(self):
        """Start a new analysis session"""
        self.session_start = datetime.now()
        self.session_end = None
        self.face_data = []
        self.speech_data = []
    
    def end_session(self):
        """End the analysis session"""
        self.session_end = datetime.now()
    
    def add_face_data(self, data):
        """Add face analysis data point"""
        self.face_data.append({
            'timestamp': datetime.now().isoformat(),
            **data
        })
    
    def add_speech_data(self, data):
        """Add speech analysis data point"""
        self.speech_data.append({
            'timestamp': datetime.now().isoformat(),
            **data
        })
    
    def calculate_fusion_score(self, face_stats, speech_stats):
        """
        Calculate fused confidence score
        
        Args:
            face_stats: Face analysis statistics
            speech_stats: Speech analysis statistics
            
        Returns:
            float: Fused confidence score (0-100)
        """
        scores = []
        weights = []
        
        # Facial emotion score (40%)
        if face_stats and face_stats.get('dominant_emotion'):
            emotion = face_stats['dominant_emotion']
            face_score = self.EMOTION_SCORES.get(emotion, 50)
            scores.append(face_score)
            weights.append(0.40)
        
        # Speech emotion score (35%)
        if speech_stats and speech_stats.get('dominant_emotion'):
            emotion = speech_stats['dominant_emotion']
            speech_score = self.EMOTION_SCORES.get(emotion, 50)
            scores.append(speech_score)
            weights.append(0.35)
        
        # Eye contact score (15%)
        if face_stats and 'eye_contact_percentage' in face_stats:
            eye_score = face_stats['eye_contact_percentage']
            scores.append(eye_score)
            weights.append(0.15)
        
        # Positive emotion ratio (10%)
        if speech_stats and 'positive_emotion_percentage' in speech_stats:
            positive_pct = speech_stats['positive_emotion_percentage']
            scores.append(positive_pct)
            weights.append(0.10)
        
        if not scores:
            return 50.0
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Calculate weighted score
        fusion_score = sum(s * w for s, w in zip(scores, weights))
        
        return np.clip(fusion_score, 0, 100)
    
    def generate_report(self, face_stats, speech_stats):
        """
        Generate comprehensive interview report
        
        Args:
            face_stats: Face analysis statistics
            speech_stats: Speech analysis statistics
            
        Returns:
            dict: Complete interview report
        """
        # Calculate duration
        duration = 0
        if self.session_start and self.session_end:
            duration = (self.session_end - self.session_start).total_seconds()
        elif self.session_start:
            duration = (datetime.now() - self.session_start).total_seconds()
        
        # Calculate scores
        fusion_score = self.calculate_fusion_score(face_stats, speech_stats)
        
        # Individual scores
        eye_contact_score = face_stats.get('eye_contact_percentage', 0) if face_stats else 0
        face_emotion_score = self.EMOTION_SCORES.get(
            face_stats.get('dominant_emotion', 'Neutral'), 50
        ) if face_stats else 50
        speech_emotion_score = self.EMOTION_SCORES.get(
            speech_stats.get('dominant_emotion', 'Neutral'), 50
        ) if speech_stats else 50
        
        # Generate rating
        if fusion_score >= 80:
            rating = 'Excellent'
            feedback = 'Outstanding interview performance!'
        elif fusion_score >= 65:
            rating = 'Good'
            feedback = 'Strong performance with minor areas for improvement.'
        elif fusion_score >= 50:
            rating = 'Average'
            feedback = 'Satisfactory performance with room for growth.'
        elif fusion_score >= 35:
            rating = 'Below Average'
            feedback = 'Several areas need improvement.'
        else:
            rating = 'Needs Improvement'
            feedback = 'Significant improvements needed in multiple areas.'
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            eye_contact_score, face_emotion_score, speech_emotion_score, fusion_score
        )
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'session_info': {
                'start_time': self.session_start.isoformat() if self.session_start else None,
                'end_time': self.session_end.isoformat() if self.session_end else None,
                'duration_seconds': duration,
                'data_points': {
                    'face': len(self.face_data),
                    'speech': len(self.speech_data)
                }
            },
            'scores': {
                'overall_score': round(fusion_score, 1),
                'eye_contact_score': round(eye_contact_score, 1),
                'facial_emotion_score': round(face_emotion_score, 1),
                'speech_emotion_score': round(speech_emotion_score, 1),
                'duration_minutes': round(duration / 60, 2),
                'rating': rating
            },
            'face_analysis': face_stats or {},
            'speech_analysis': speech_stats or {},
            'feedback': feedback,
            'recommendations': recommendations
        }
        
        return report
    
    def _generate_recommendations(self, eye_score, face_score, speech_score, overall):
        """Generate personalized recommendations"""
        recommendations = []
        
        # Eye contact recommendations
        if eye_score < 50:
            recommendations.append({
                'area': 'Eye Contact',
                'priority': 'High',
                'suggestion': 'Practice maintaining consistent eye contact with the camera. Try placing a sticker near your webcam as a focal point.'
            })
        elif eye_score < 70:
            recommendations.append({
                'area': 'Eye Contact',
                'priority': 'Medium',
                'suggestion': 'Good eye contact overall. Try to avoid looking away during pauses in speech.'
            })
        
        # Facial expression recommendations
        if face_score < 50:
            recommendations.append({
                'area': 'Facial Expressions',
                'priority': 'High',
                'suggestion': 'Practice showing more positive expressions. A natural smile and engaged look convey confidence and enthusiasm.'
            })
        elif face_score < 70:
            recommendations.append({
                'area': 'Facial Expressions',
                'priority': 'Medium',
                'suggestion': 'Your expressions are generally appropriate. Practice maintaining a pleasant, engaged demeanor throughout.'
            })
        
        # Speech/vocal recommendations
        if speech_score < 50:
            recommendations.append({
                'area': 'Vocal Delivery',
                'priority': 'High',
                'suggestion': 'Focus on speaking with more energy and enthusiasm. Practice varying your tone to convey confidence.'
            })
        elif speech_score < 70:
            recommendations.append({
                'area': 'Vocal Delivery',
                'priority': 'Medium',
                'suggestion': 'Good vocal delivery. Consider adding more vocal variety to engage the interviewer.'
            })
        
        # Overall recommendations
        if overall >= 80:
            recommendations.append({
                'area': 'Overall Performance',
                'priority': 'Low',
                'suggestion': 'Excellent performance! Continue practicing to maintain consistency across all interviews.'
            })
        elif overall < 50:
            recommendations.append({
                'area': 'Overall Performance',
                'priority': 'High',
                'suggestion': 'Consider recording practice interviews and reviewing them to identify patterns. Mock interviews with feedback can help significantly.'
            })
        
        return recommendations
    
    def save_report(self, report, filepath=None):
        """Save report to file"""
        if filepath is None:
            os.makedirs('reports', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f'reports/interview_report_{timestamp}.json'
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Report saved to: {filepath}")
        return filepath
    
    def reset(self):
        """Reset fusion module"""
        self.session_start = None
        self.session_end = None
        self.face_data = []
        self.speech_data = []


# Test
if __name__ == "__main__":
    print("Testing Multimodal Fusion...")
    
    fusion = MultimodalFusion()
    fusion.start_session()
    
    # Simulate data
    face_stats = {
        'dominant_emotion': 'Happy',
        'eye_contact_percentage': 75,
        'avg_confidence': 80
    }
    
    speech_stats = {
        'dominant_emotion': 'Calm',
        'positive_emotion_percentage': 70,
        'avg_confidence': 75
    }
    
    fusion.end_session()
    
    report = fusion.generate_report(face_stats, speech_stats)
    print(f"Overall Score: {report['scores']['overall_score']}")
    print(f"Rating: {report['scores']['rating']}")
    
    print("✓ Test complete!")
