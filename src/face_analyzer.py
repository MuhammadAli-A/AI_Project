"""
Face Analysis Module
Detects faces, tracks eye contact, and analyzes emotions
"""
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from .emotion_detector import SimplifiedEmotionDetector


class FaceAnalyzer:
    def __init__(self):
        """Initialize face analyzer with MediaPipe and Emotion Detector"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Initialize emotion detector
        self.emotion_detector = SimplifiedEmotionDetector()
        
        self.eye_contact_history = deque(maxlen=30)
        self.emotion_history = deque(maxlen=10)
        self.face_detected = False
        self.current_emotion = "Neutral"
        self.emotion_confidence = 0.0
        self.eye_contact_score = 0.0
        
    def analyze_face(self, frame):
        """
        Analyze face in the current frame
        
        Args:
            frame: Current video frame
            
        Returns:
            tuple: (analyzed_frame, face_data)
        """
        analyzed_frame = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process face mesh
        results = self.face_mesh.process(rgb_frame)
        
        face_data = {
            'face_detected': False,
            'eye_contact': False,
            'emotion': 'neutral',
            'head_pose': 'center',
            'confidence': 0.0
        }
        
        if results.multi_face_landmarks:
            self.face_detected = True
            face_data['face_detected'] = True
            
            for face_landmarks in results.multi_face_landmarks:
                # Draw face mesh
                self.mp_drawing.draw_landmarks(
                    image=analyzed_frame,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                
                # Analyze eye contact
                eye_contact = self._check_eye_contact(face_landmarks, frame.shape)
                face_data['eye_contact'] = eye_contact
                self.eye_contact_history.append(eye_contact)
                
                # Analyze head pose
                head_pose = self._analyze_head_pose(face_landmarks, frame.shape)
                face_data['head_pose'] = head_pose
        else:
            self.face_detected = False
            self.eye_contact_history.append(False)
        
        # Emotion detection using real-time facial feature analysis
        try:
            emotion, confidence, face_rect = self.emotion_detector.detect_emotion(frame)
            
            self.current_emotion = emotion
            self.emotion_confidence = confidence
            self.emotion_history.append(emotion)
            face_data['emotion'] = emotion
            face_data['emotion_confidence'] = confidence
            
            # Draw emotion label on frame
            if face_rect:
                x, y, w, h = face_rect
                cv2.rectangle(analyzed_frame, (x, y), (x+w, y+h), (255, 0, 255), 2)
                cv2.putText(analyzed_frame, f"{emotion} ({confidence:.1f}%)", 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            
        except Exception as e:
            face_data['emotion'] = self.current_emotion
            face_data['emotion_confidence'] = self.emotion_confidence
        
        # Calculate eye contact score
        if len(self.eye_contact_history) > 0:
            self.eye_contact_score = sum(self.eye_contact_history) / len(self.eye_contact_history)
            face_data['confidence'] = round(self.eye_contact_score * 100, 2)
        
        # Add text overlay
        self._add_overlay(analyzed_frame, face_data)
        
        return analyzed_frame, face_data
    
    def _check_eye_contact(self, face_landmarks, frame_shape):
        """
        Check if person is making eye contact
        
        Args:
            face_landmarks: MediaPipe face landmarks
            frame_shape: Shape of the frame
            
        Returns:
            bool: True if eye contact detected
        """
        h, w = frame_shape[:2]
        
        # Get eye landmarks (iris center)
        left_iris = face_landmarks.landmark[468]  # Left iris center
        right_iris = face_landmarks.landmark[473]  # Right iris center
        
        # Get eye boundaries
        left_eye_left = face_landmarks.landmark[33]
        left_eye_right = face_landmarks.landmark[133]
        right_eye_left = face_landmarks.landmark[362]
        right_eye_right = face_landmarks.landmark[263]
        
        # Calculate iris position relative to eye
        left_iris_x = left_iris.x
        left_eye_center_x = (left_eye_left.x + left_eye_right.x) / 2
        
        right_iris_x = right_iris.x
        right_eye_center_x = (right_eye_left.x + right_eye_right.x) / 2
        
        # Check if iris is centered (eye contact)
        left_centered = abs(left_iris_x - left_eye_center_x) < 0.015
        right_centered = abs(right_iris_x - right_eye_center_x) < 0.015
        
        return left_centered and right_centered
    
    def _analyze_head_pose(self, face_landmarks, frame_shape):
        """
        Analyze head pose direction
        
        Args:
            face_landmarks: MediaPipe face landmarks
            frame_shape: Shape of the frame
            
        Returns:
            str: Head pose direction
        """
        # Get nose tip and chin
        nose_tip = face_landmarks.landmark[1]
        chin = face_landmarks.landmark[152]
        
        # Get left and right face boundaries
        left_face = face_landmarks.landmark[234]
        right_face = face_landmarks.landmark[454]
        
        # Calculate horizontal position
        face_center_x = (left_face.x + right_face.x) / 2
        nose_x = nose_tip.x
        
        # Determine head pose
        if nose_x < face_center_x - 0.03:
            return "left"
        elif nose_x > face_center_x + 0.03:
            return "right"
        else:
            return "center"
    
    def _add_overlay(self, frame, face_data):
        """Add text overlay with analysis results"""
        h, w = frame.shape[:2]
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (320, 170), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Add text with color coding
        y_offset = 30
        face_color = (0, 255, 0) if face_data['face_detected'] else (0, 0, 255)
        cv2.putText(frame, f"Face: {'Yes' if face_data['face_detected'] else 'No'}", 
                    (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, face_color, 2)
        
        y_offset += 30
        eye_color = (0, 255, 0) if face_data['eye_contact'] else (0, 165, 255)
        cv2.putText(frame, f"Eye Contact: {'Yes' if face_data['eye_contact'] else 'No'}", 
                    (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, eye_color, 2)
        
        y_offset += 30
        # Color-code emotions
        emotion_colors = {
            'Happy': (0, 255, 0),
            'Neutral': (255, 255, 0),
            'Surprise': (255, 165, 0),
            'Sad': (255, 0, 0),
            'Angry': (0, 0, 255),
            'Fear': (180, 0, 255),
            'Disgust': (128, 0, 128)
        }
        emotion_color = emotion_colors.get(face_data['emotion'], (255, 255, 255))
        confidence = face_data.get('emotion_confidence', 0)
        cv2.putText(frame, f"Emotion: {face_data['emotion']} ({confidence:.0f}%)", 
                    (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, emotion_color, 2)
        
        y_offset += 30
        cv2.putText(frame, f"Head: {face_data['head_pose']}", 
                    (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    def get_face_statistics(self):
        """
        Get face analysis statistics
        
        Returns:
            dict: Face statistics
        """
        eye_contact_percentage = round(self.eye_contact_score * 100, 2)
        
        # Emotion distribution
        emotion_counts = {}
        for emotion in self.emotion_history:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        return {
            'eye_contact_percentage': eye_contact_percentage,
            'eye_contact_rating': self._rate_eye_contact(eye_contact_percentage),
            'dominant_emotion': self.current_emotion,
            'emotion_distribution': emotion_counts,
            'face_detected': self.face_detected
        }
    
    def _rate_eye_contact(self, percentage):
        """Rate eye contact quality"""
        if percentage >= 70:
            return "Excellent"
        elif percentage >= 50:
            return "Good"
        elif percentage >= 30:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def reset(self):
        """Reset face analyzer"""
        self.eye_contact_history.clear()
        self.emotion_history.clear()
        self.face_detected = False
        self.current_emotion = "Neutral"
        self.emotion_confidence = 0.0
        self.eye_contact_score = 0.0
