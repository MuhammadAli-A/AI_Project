"""
Emotion Detection Module using FER2013-style approach
Detects 7 basic emotions: angry, disgust, fear, happy, sad, surprise, neutral
"""
import cv2
import numpy as np





class SimplifiedEmotionDetector:
    """
    Simplified emotion detector using OpenCV and facial feature analysis
    No deep learning required - works immediately
    """
    def __init__(self):
        self.emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
        
        # Track emotion history for smoothing
        self.emotion_history = []
        self.history_size = 5
        
    def detect_emotion(self, frame):
        """
        Detect emotion using facial features and cascade classifiers
        
        Args:
            frame: Input frame (BGR)
            
        Returns:
            tuple: (emotion_label, confidence, face_region)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return 'Neutral', 0.0, None
        
        # Get the largest face
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        (x, y, w, h) = largest_face
        
        # Extract face region
        face_roi_gray = gray[y:y+h, x:x+w]
        face_roi_color = frame[y:y+h, x:x+w]
        
        # Detect features
        eyes = self.eye_cascade.detectMultiScale(face_roi_gray, 1.1, 3)
        smiles = self.smile_cascade.detectMultiScale(face_roi_gray, 1.8, 20)
        
        # Analyze face characteristics
        emotion, confidence = self._analyze_features(face_roi_gray, face_roi_color, eyes, smiles)
        
        # Smooth predictions using history
        self.emotion_history.append(emotion)
        if len(self.emotion_history) > self.history_size:
            self.emotion_history.pop(0)
        
        # Get most common emotion from history
        if len(self.emotion_history) >= 3:
            from collections import Counter
            emotion_counts = Counter(self.emotion_history)
            emotion = emotion_counts.most_common(1)[0][0]
        
        return emotion, confidence, (x, y, w, h)
    
    def _analyze_features(self, face_gray, face_color, eyes, smiles):
        """
        Analyze facial features to determine emotion
        
        Returns:
            tuple: (emotion, confidence)
        """
        # Calculate statistics
        mean_intensity = np.mean(face_gray)
        std_intensity = np.std(face_gray)
        
        # Edge detection for expression intensity
        edges = cv2.Canny(face_gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Color analysis (for flushed face, etc.)
        hsv = cv2.cvtColor(face_color, cv2.COLOR_BGR2HSV)
        mean_saturation = np.mean(hsv[:, :, 1])
        
        # Feature counts
        num_eyes = len(eyes)
        num_smiles = len(smiles)
        
        # Emotion detection logic
        confidence = 65.0
        
        # Happy: Smile detected
        if num_smiles > 0:
            return 'Happy', 75.0
        
        # Surprise: Wide eyes (high edge density in upper face)
        upper_face = face_gray[0:face_gray.shape[0]//2, :]
        upper_edges = cv2.Canny(upper_face, 50, 150)
        upper_edge_density = np.sum(upper_edges > 0) / upper_edges.size
        
        if upper_edge_density > 0.15 and num_eyes >= 2:
            return 'Surprise', 70.0
        
        # Angry: Low brightness, high contrast, furrowed brows
        if mean_intensity < 100 and std_intensity > 45:
            # Check for furrowed brow (high edge density in upper face)
            if upper_edge_density > 0.12:
                return 'Angry', 68.0
        
        # Sad: Low overall brightness, low edge density
        if mean_intensity < 90 and edge_density < 0.08:
            return 'Sad', 65.0
        
        # Fear: High edge density, moderate brightness
        if edge_density > 0.12 and 90 < mean_intensity < 130:
            return 'Fear', 62.0
        
        # Disgust: Asymmetric features, moderate brightness
        if std_intensity > 50 and mean_saturation < 50:
            return 'Disgust', 60.0
        
        # Default to Neutral
        return 'Neutral', 70.0
