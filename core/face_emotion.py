"""
Simplified Face Emotion Analyzer
Uses pre-trained FER2013 model with OpenCV/MediaPipe for face detection
No training required - works with existing models
"""
import cv2
import numpy as np
import os
from collections import deque, Counter

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Import TensorFlow
try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠ TensorFlow not available")

# Import MediaPipe for face detection
try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False
    print("⚠ MediaPipe not available, using OpenCV Haar Cascade")


class FaceEmotionAnalyzer:
    """
    Real-time facial emotion detection using pre-trained CNN model
    Emotions: Angry, Disgust, Fear, Happy, Sad, Surprise, Neutral
    """
    
    EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
    IMG_SIZE = 48  # FER2013 input size
    
    def __init__(self):
        """Initialize face analyzer with pre-trained model"""
        self.model = None
        self.face_detector = None
        self.mp_face = None
        
        # History for smoothing
        self.emotion_history = deque(maxlen=10)
        self.confidence_history = deque(maxlen=10)
        self.eye_contact_history = deque(maxlen=30)
        
        # Current state
        self.current_emotion = 'Neutral'
        self.current_confidence = 0.0
        self.face_detected = False
        
        # Initialize model and detector
        self._initialize()
    
    def _initialize(self):
        """Initialize model and face detector"""
        global MP_AVAILABLE
        
        # Load emotion model
        if TF_AVAILABLE:
            model_paths = [
                "models/facial_emotion_model.h5",
                "src/fer2013_model.h5",
                "models/fer2013_model.h5"
            ]
            
            for path in model_paths:
                if os.path.exists(path):
                    try:
                        print(f"Loading facial emotion model: {path}")
                        self.model = keras.models.load_model(path, compile=False)
                        print("✓ Facial emotion model loaded!")
                        break
                    except Exception as e:
                        print(f"⚠ Failed to load {path}: {e}")
        
        # Initialize face detection
        if MP_AVAILABLE:
            try:
                self.mp_face = mp.solutions.face_detection
                self.face_detector = self.mp_face.FaceDetection(
                    min_detection_confidence=0.5
                )
                print("✓ MediaPipe face detector initialized")
            except:
                MP_AVAILABLE = False
        
        if not MP_AVAILABLE or self.face_detector is None:
            # Fallback to OpenCV Haar Cascade
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_detector = cv2.CascadeClassifier(cascade_path)
            self.mp_face = None
            print("✓ OpenCV Haar Cascade face detector initialized")
    
    def analyze(self, frame):
        """
        Analyze face in frame and detect emotion
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            tuple: (processed_frame, analysis_data)
        """
        if frame is None:
            return frame, self._empty_result()
        
        processed_frame = frame.copy()
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        face_rect = self._detect_face(frame)
        
        if face_rect is None:
            self.face_detected = False
            self.eye_contact_history.append(False)
            return processed_frame, self._empty_result()
        
        self.face_detected = True
        x, y, bw, bh = face_rect
        
        # Draw face rectangle
        cv2.rectangle(processed_frame, (x, y), (x+bw, y+bh), (0, 255, 0), 2)
        
        # Extract and preprocess face for emotion detection
        face_roi = gray[y:y+bh, x:x+bw]
        emotion, confidence = self._predict_emotion(face_roi)
        
        # Update history
        self.emotion_history.append(emotion)
        self.confidence_history.append(confidence)
        
        # Smooth prediction
        if len(self.emotion_history) >= 3:
            emotion_counts = Counter(self.emotion_history)
            emotion = emotion_counts.most_common(1)[0][0]
        
        self.current_emotion = emotion
        self.current_confidence = confidence
        
        # Check eye contact (simplified: if face is centered)
        face_center_x = x + bw // 2
        eye_contact = abs(face_center_x - w // 2) < w * 0.2
        self.eye_contact_history.append(eye_contact)
        
        # Draw emotion label
        label = f"{emotion}: {confidence:.0f}%"
        cv2.putText(processed_frame, label, (x, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw eye contact indicator
        eye_color = (0, 255, 0) if eye_contact else (0, 0, 255)
        cv2.circle(processed_frame, (w - 30, 30), 15, eye_color, -1)
        cv2.putText(processed_frame, "EYE", (w - 55, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, eye_color, 1)
        
        # Ensure all values are JSON serializable
        return processed_frame, {
            'face_detected': True,
            'emotion': str(emotion),
            'confidence': float(confidence),
            'eye_contact': bool(eye_contact),
            'face_rect': (int(x), int(y), int(bw), int(bh))
        }
    
    def _detect_face(self, frame):
        """Detect face in frame, return bounding box"""
        h, w = frame.shape[:2]
        
        if self.mp_face is not None:
            # MediaPipe detection
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detector.process(rgb)
            
            if results.detections:
                detection = results.detections[0]
                box = detection.location_data.relative_bounding_box
                x = max(0, int(box.xmin * w))
                y = max(0, int(box.ymin * h))
                bw = min(w - x, int(box.width * w))
                bh = min(h - y, int(box.height * h))
                return (x, y, bw, bh)
        else:
            # OpenCV Haar Cascade
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48)
            )
            
            if len(faces) > 0:
                return tuple(max(faces, key=lambda r: r[2] * r[3]))
        
        return None
    
    def _predict_emotion(self, face_roi):
        """Predict emotion from face region"""
        if self.model is None or face_roi.size == 0:
            return 'Neutral', 50.0
        
        try:
            # Preprocess: resize to 48x48, normalize
            face = cv2.resize(face_roi, (self.IMG_SIZE, self.IMG_SIZE))
            face = face.astype('float32') / 255.0
            face = face.reshape(1, self.IMG_SIZE, self.IMG_SIZE, 1)
            
            # Predict
            predictions = self.model.predict(face, verbose=0)[0]
            emotion_idx = np.argmax(predictions)
            confidence = float(predictions[emotion_idx]) * 100
            
            return self.EMOTION_LABELS[emotion_idx], confidence
            
        except Exception as e:
            return 'Neutral', 50.0
    
    def _empty_result(self):
        """Return empty result when no face detected"""
        return {
            'face_detected': False,
            'emotion': 'Neutral',
            'confidence': 0.0,
            'eye_contact': False,
            'face_rect': None
        }
    
    def _to_python_type(self, value):
        """Convert numpy types to Python native types for JSON serialization"""
        if isinstance(value, (np.bool_, np.generic)):
            return value.item()
        elif isinstance(value, np.ndarray):
            return value.tolist()
        elif isinstance(value, dict):
            return {k: self._to_python_type(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [self._to_python_type(v) for v in value]
        return value
    
    def get_statistics(self):
        """Get analysis statistics"""
        if len(self.emotion_history) == 0:
            return {
                'face_detected': False,
                'dominant_emotion': 'Neutral',
                'confidence': 0.0,
                'avg_confidence': 0.0,
                'eye_contact': 0.0,
                'eye_contact_percentage': 0.0,
                'eye_contact_rating': 'N/A',
                'positivity_score': 0.5,
                'emotion_distribution': {},
                'emotion_counts': {},
                'overall_confidence': 0.0
            }
        
        # Emotion distribution
        emotion_counts = Counter(self.emotion_history)
        total = len(self.emotion_history)
        distribution = {e: float((c / total) * 100) for e, c in emotion_counts.items()}
        
        # Eye contact
        eye_contact_pct = float((sum(self.eye_contact_history) / max(1, len(self.eye_contact_history))) * 100)
        
        # Rating
        if eye_contact_pct >= 70:
            rating = 'Excellent'
        elif eye_contact_pct >= 50:
            rating = 'Good'
        elif eye_contact_pct >= 30:
            rating = 'Fair'
        else:
            rating = 'Needs Improvement'
        
        avg_conf = float(np.mean(list(self.confidence_history))) if self.confidence_history else 0.0
        
        # Calculate positivity score based on positive emotions
        positive_emotions = ['Happy', 'Neutral', 'Surprise', 'Calm']
        positive_count = sum(emotion_counts.get(e, 0) for e in positive_emotions)
        positivity_score = float(positive_count / max(1, total))  # 0-1 range
        
        return {
            'face_detected': bool(self.face_detected),
            'dominant_emotion': str(emotion_counts.most_common(1)[0][0]) if emotion_counts else 'Neutral',
            'confidence': avg_conf / 100.0,  # Normalize to 0-1 for frontend
            'avg_confidence': avg_conf,  # Keep original for reports
            'eye_contact': eye_contact_pct / 100.0,  # Normalize to 0-1 for frontend
            'eye_contact_percentage': eye_contact_pct,  # Keep original for reports
            'eye_contact_rating': rating,
            'positivity_score': positivity_score,  # 0-1 range
            'emotion_distribution': distribution,
            'emotion_counts': emotion_counts,  # Raw counts for report
            'overall_confidence': avg_conf / 100.0  # Normalize to 0-1 for frontend
        }
    
    def reset(self):
        """Reset analyzer state"""
        self.emotion_history.clear()
        self.confidence_history.clear()
        self.eye_contact_history.clear()
        self.current_emotion = 'Neutral'
        self.current_confidence = 0.0
        self.face_detected = False
    
    def reset_history(self):
        """Alias for reset() - clears all history"""
        self.reset()


# Test
if __name__ == "__main__":
    print("Testing Face Emotion Analyzer...")
    analyzer = FaceEmotionAnalyzer()
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            processed, data = analyzer.analyze(frame)
            print(f"Result: {data}")
        cap.release()
    
    print("✓ Test complete!")
