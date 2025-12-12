"""
Interview Analytics Module
Calculates scores and generates reports
"""
import time
from datetime import datetime, timedelta
import json


class InterviewAnalytics:
    def __init__(self):
        """Initialize analytics tracker"""
        self.start_time = None
        self.end_time = None
        self.motion_data = []
        self.face_data = []
        self.speech_data = []
        self.session_active = False
        
    def start_session(self):
        """Start interview session"""
        self.start_time = datetime.now()
        self.session_active = True
        self.motion_data = []
        self.face_data = []
        self.speech_data = []
    
    def end_session(self):
        """End interview session"""
        self.end_time = datetime.now()
        self.session_active = False
    
    def add_motion_data(self, motion_stats):
        """Add motion statistics"""
        if self.session_active:
            self.motion_data.append({
                'timestamp': datetime.now().isoformat(),
                **motion_stats
            })
    
    def add_face_data(self, face_stats):
        """Add face statistics"""
        if self.session_active:
            self.face_data.append({
                'timestamp': datetime.now().isoformat(),
                **face_stats
            })
    
    def add_speech_data(self, speech_stats):
        """Add speech statistics"""
        if self.session_active:
            self.speech_data.append(speech_stats)
    
    def calculate_scores(self):
        """
        Calculate overall interview scores
        
        Returns:
            dict: Comprehensive interview scores
        """
        if not self.motion_data or not self.face_data:
            return {
                'overall_score': 0,
                'error': 'Insufficient data'
            }
        
        # Calculate individual scores
        eye_contact_score = self._calculate_eye_contact_score()
        body_language_score = self._calculate_body_language_score()
        emotion_score = self._calculate_emotion_score()
        engagement_score = self._calculate_engagement_score()
        speech_score = self._calculate_speech_score()
        
        # Calculate overall score (weighted average)
        # Adjust weights if speech data is available
        if self.speech_data:
            overall_score = (
                eye_contact_score * 0.25 +
                body_language_score * 0.20 +
                emotion_score * 0.20 +
                engagement_score * 0.15 +
                speech_score * 0.20
            )
        else:
            overall_score = (
                eye_contact_score * 0.30 +
                body_language_score * 0.25 +
                emotion_score * 0.25 +
                engagement_score * 0.20
            )
        
        duration = self._calculate_duration()
        
        result = {
            'overall_score': round(overall_score, 2),
            'eye_contact_score': round(eye_contact_score, 2),
            'body_language_score': round(body_language_score, 2),
            'emotion_score': round(emotion_score, 2),
            'engagement_score': round(engagement_score, 2),
            'duration_minutes': round(duration, 2),
            'rating': self._get_rating(overall_score),
            'recommendations': self._generate_recommendations(
                eye_contact_score,
                body_language_score,
                emotion_score,
                engagement_score,
                speech_score
            )
        }
        
        # Add speech score if available
        if self.speech_data:
            result['speech_score'] = round(speech_score, 2)
        
        return result
    
    def _calculate_eye_contact_score(self):
        """Calculate eye contact score"""
        if not self.face_data:
            return 0
        
        eye_contact_values = [
            data.get('eye_contact_percentage', 0) 
            for data in self.face_data
        ]
        
        avg_eye_contact = sum(eye_contact_values) / len(eye_contact_values)
        return min(avg_eye_contact, 100)
    
    def _calculate_body_language_score(self):
        """Calculate body language score based on motion"""
        if not self.motion_data:
            return 0
        
        motion_frequencies = [
            data.get('motion_frequency', 0) 
            for data in self.motion_data
        ]
        
        avg_motion = sum(motion_frequencies) / len(motion_frequencies)
        
        # Optimal motion is moderate (20-40%)
        if 20 <= avg_motion <= 40:
            score = 100
        elif avg_motion < 20:
            # Too still
            score = 50 + (avg_motion / 20) * 50
        else:
            # Too fidgety
            score = 100 - ((avg_motion - 40) / 60) * 50
        
        return max(0, min(score, 100))
    
    def _calculate_emotion_score(self):
        """Calculate emotion appropriateness score"""
        if not self.face_data:
            return 0
        
        # FER2013 emotions with interview appropriateness scores
        positive_emotions = ['Happy', 'Neutral']
        moderate_emotions = ['Surprise']
        negative_emotions = ['Angry', 'Disgust', 'Fear', 'Sad']
        
        emotion_scores = []
        for data in self.face_data:
            emotion = data.get('dominant_emotion', 'Neutral')
            
            if emotion in positive_emotions:
                emotion_scores.append(100)
            elif emotion in moderate_emotions:
                emotion_scores.append(70)
            elif emotion in negative_emotions:
                emotion_scores.append(30)
            else:
                emotion_scores.append(60)
        
        return sum(emotion_scores) / len(emotion_scores) if emotion_scores else 0
    
    def _calculate_engagement_score(self):
        """Calculate engagement based on face detection consistency"""
        if not self.face_data:
            return 0
        
        face_detected_count = sum(
            1 for data in self.face_data 
            if data.get('face_detected', False)
        )
        
        engagement = (face_detected_count / len(self.face_data)) * 100
        return engagement
    
    def _calculate_speech_score(self):
        """Calculate speech analysis score"""
        if not self.speech_data:
            return 75  # Default neutral score
        
        # Extract metrics
        clarity_scores = [d.get('clarity_score', 0) for d in self.speech_data]
        confidence_scores = [d.get('confidence_score', 0) for d in self.speech_data]
        emotions = [d.get('emotion', 'neutral') for d in self.speech_data]
        
        # Calculate averages
        avg_clarity = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 50
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 50
        
        # Analyze emotion distribution
        positive_emotions = ['happy', 'calm', 'neutral']
        positive_count = sum(1 for e in emotions if e in positive_emotions)
        emotion_score = (positive_count / len(emotions)) * 100 if emotions else 50
        
        # Weighted combination
        speech_score = (
            avg_clarity * 0.35 +
            avg_confidence * 0.40 +
            emotion_score * 0.25
        )
        
        return min(max(speech_score, 0), 100)
    
    def _calculate_duration(self):
        """Calculate session duration in minutes"""
        if not self.start_time:
            return 0
        
        end = self.end_time if self.end_time else datetime.now()
        duration = (end - self.start_time).total_seconds() / 60
        return duration
    
    def _get_rating(self, score):
        """Get rating based on score"""
        if score >= 85:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 55:
            return "Average"
        elif score >= 40:
            return "Below Average"
        else:
            return "Needs Improvement"
    
    def _generate_recommendations(self, eye_contact, body_language, emotion, engagement, speech=None):
        """Generate personalized recommendations"""
        recommendations = []
        
        if eye_contact < 50:
            recommendations.append("Practice maintaining eye contact with the camera. Aim for 60-70% eye contact.")
        
        if body_language < 50:
            recommendations.append("Work on your body language. Avoid excessive fidgeting or staying too still.")
        
        if emotion < 60:
            recommendations.append("Try to maintain a positive and professional demeanor throughout the interview.")
        
        if engagement < 70:
            recommendations.append("Stay engaged and present throughout the interview. Keep your face visible to the camera.")
        
        if speech is not None:
            if speech < 60:
                recommendations.append("Focus on speaking clearly and confidently. Practice your vocal delivery.")
            elif speech < 75:
                recommendations.append("Good communication skills. Work on maintaining consistent vocal confidence.")
        
        if not recommendations:
            recommendations.append("Great job! Keep maintaining this performance level.")
        
        return recommendations
    
    def generate_report(self):
        """
        Generate detailed interview report
        
        Returns:
            dict: Comprehensive interview report
        """
        scores = self.calculate_scores()
        
        # Summary statistics
        motion_summary = self._summarize_motion_data()
        face_summary = self._summarize_face_data()
        speech_summary = self._summarize_speech_data()
        
        report = {
            'session_info': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_minutes': scores.get('duration_minutes', 0)
            },
            'scores': scores,
            'motion_analysis': motion_summary,
            'face_analysis': face_summary,
            'speech_analysis': speech_summary,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _summarize_motion_data(self):
        """Summarize motion data"""
        if not self.motion_data:
            return {}
        
        motion_frequencies = [d.get('motion_frequency', 0) for d in self.motion_data]
        
        return {
            'average_motion': round(sum(motion_frequencies) / len(motion_frequencies), 2),
            'max_motion': round(max(motion_frequencies), 2),
            'min_motion': round(min(motion_frequencies), 2),
            'samples': len(self.motion_data)
        }
    
    def _summarize_face_data(self):
        """Summarize face data"""
        if not self.face_data:
            return {}
        
        eye_contact_values = [d.get('eye_contact_percentage', 0) for d in self.face_data]
        face_detected_count = sum(1 for d in self.face_data if d.get('face_detected', False))
        
        # Emotion distribution
        emotions = [d.get('dominant_emotion', 'neutral') for d in self.face_data]
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        return {
            'average_eye_contact': round(sum(eye_contact_values) / len(eye_contact_values), 2),
            'face_detection_rate': round((face_detected_count / len(self.face_data)) * 100, 2),
            'emotion_distribution': emotion_counts,
            'samples': len(self.face_data)
        }
    
    def _summarize_speech_data(self):
        """Summarize speech data"""
        if not self.speech_data:
            return {'available': False}
        
        clarity_scores = [d.get('clarity_score', 0) for d in self.speech_data]
        confidence_scores = [d.get('confidence_score', 0) for d in self.speech_data]
        emotions = [d.get('emotion', 'neutral') for d in self.speech_data]
        volumes = [d.get('volume', 0) for d in self.speech_data]
        
        # Emotion distribution
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        return {
            'available': True,
            'average_clarity': round(sum(clarity_scores) / len(clarity_scores), 2) if clarity_scores else 0,
            'average_confidence': round(sum(confidence_scores) / len(confidence_scores), 2) if confidence_scores else 0,
            'average_volume': round(sum(volumes) / len(volumes), 2) if volumes else 0,
            'emotion_distribution': emotion_counts,
            'dominant_emotion': max(emotion_counts, key=emotion_counts.get) if emotion_counts else 'neutral',
            'samples': len(self.speech_data)
        }
    
    def save_report(self, filepath):
        """Save report to JSON file"""
        report = self.generate_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=4)
        return filepath
