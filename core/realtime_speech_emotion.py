"""
Real-Time Speech Emotion Recognition Module
Based on the tested standalone speech module (speech 1/RealTime_Speech_SER)
Uses HuggingFace Wav2Vec2 pre-trained model for emotion recognition

Emotions: angry, calm, disgust, fear, happy, neutral, sad, surprise
"""
import torch
import numpy as np
import soundfile as sf
import sounddevice as sd
import tempfile
import os
import time
from collections import deque, Counter

# Load model from HuggingFace
from transformers import Wav2Vec2FeatureExtractor, AutoModelForAudioClassification


class RealtimeSpeechEmotionRecognizer:
    """
    Real-time Speech Emotion Recognition using Wav2Vec2 model
    This is a simplified, tested implementation based on the standalone module
    """
    
    # Model - using the pre-trained speech emotion model
    MODEL_NAME = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
    
    def __init__(self, sample_rate=16000, chunk_duration=3):
        """
        Initialize the speech emotion recognizer
        
        Args:
            sample_rate: Audio sample rate (16000 Hz required for the model)
            chunk_duration: Duration of audio chunks to analyze (seconds)
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        
        # Load model
        print("🔃 Loading pre-trained Speech Emotion Recognition model...")
        self.processor = Wav2Vec2FeatureExtractor.from_pretrained(self.MODEL_NAME)
        self.model = AutoModelForAudioClassification.from_pretrained(self.MODEL_NAME)
        
        # Get emotion labels from model config
        self.EMOTIONS = self.model.config.id2label  # e.g. {0: 'neutral', 1:'calm', ...}
        print(f"✓ Model loaded! Emotions: {list(self.EMOTIONS.values())}")
        
        # Interview-appropriate emotions mapping
        self.positive_emotions = ['happy', 'calm', 'neutral']
        self.negative_emotions = ['angry', 'fear', 'sad', 'disgust']
        self.neutral_emotions = ['surprise']
        
        # History tracking
        self.emotion_history = deque(maxlen=20)
        self.confidence_history = deque(maxlen=20)
        
        # Session tracking
        self.session_active = False
        self.session_results = []
    
    def predict_emotion_from_file(self, audio_file):
        """
        Load a .wav file and predict the emotion
        
        Args:
            audio_file: Path to .wav audio file
            
        Returns:
            tuple: (emotion, confidence_percentage)
        """
        try:
            speech, sr = sf.read(audio_file)
            return self.predict_emotion(speech, sr)
        except Exception as e:
            print(f"Error reading audio file: {e}")
            return 'neutral', 0.0
    
    def predict_emotion(self, audio_data, sample_rate=None):
        """
        Predict emotion from audio data
        
        Args:
            audio_data: numpy array of audio samples
            sample_rate: Sample rate of the audio
            
        Returns:
            tuple: (emotion, confidence_percentage)
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
            
        try:
            # Ensure audio is mono
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Ensure float32
            audio_data = audio_data.astype(np.float32)
            
            # Process audio
            inputs = self.processor(
                audio_data, 
                sampling_rate=sample_rate, 
                return_tensors="pt", 
                padding=True
            )
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Get probabilities
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1).detach().cpu().numpy()[0]
            idx = np.argmax(probs)
            emotion = self.EMOTIONS[idx]
            confidence = round(float(probs[idx]) * 100, 2)
            
            # Update history
            self.emotion_history.append(emotion)
            self.confidence_history.append(confidence)
            
            return emotion, confidence
            
        except Exception as e:
            print(f"Error predicting emotion: {e}")
            return 'neutral', 0.0
    
    def record_and_predict(self, duration=3, filename="temp_audio.wav"):
        """
        Record audio from microphone and predict emotion
        
        Args:
            duration: Recording duration in seconds
            filename: Temporary filename for audio
            
        Returns:
            tuple: (emotion, confidence_percentage)
        """
        try:
            print("🎙 Recording audio (speak now)...")
            audio = sd.rec(
                int(duration * self.sample_rate), 
                samplerate=self.sample_rate, 
                channels=1
            )
            sd.wait()
            
            audio = np.squeeze(audio)
            sf.write(filename, audio, self.sample_rate)
            print(f"🎧 Saved audio to {filename}")
            
            return self.predict_emotion_from_file(filename)
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            return 'neutral', 0.0
    
    def analyze_audio_chunk(self, audio_data, sample_rate=None):
        """
        Analyze audio chunk - compatible with SpeechAnalyzer interface
        
        Args:
            audio_data: numpy array of audio samples
            sample_rate: Sample rate
            
        Returns:
            dict: Analysis results with emotion and confidence
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
            
        # Check for silence
        rms = np.sqrt(np.mean(audio_data ** 2))
        is_speech = rms > 0.01
        
        if not is_speech:
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'is_speech': False,
                'volume': float(rms * 100),
                'emotion_scores': {}
            }
        
        # Predict emotion
        emotion, confidence = self.predict_emotion(audio_data, sample_rate)
        
        # Get all emotion scores
        try:
            audio_data = audio_data.astype(np.float32)
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
                
            inputs = self.processor(
                audio_data, 
                sampling_rate=sample_rate, 
                return_tensors="pt", 
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1).detach().cpu().numpy()[0]
            emotion_scores = {self.EMOTIONS[i]: float(probs[i]) for i in range(len(probs))}
        except:
            emotion_scores = {}
        
        return {
            'emotion': emotion,
            'confidence': confidence,
            'is_speech': True,
            'volume': float(rms * 100),
            'emotion_scores': emotion_scores,
            'confidence_score': confidence  # Alias for compatibility
        }
    
    def get_dominant_emotion(self):
        """
        Get the dominant emotion from history
        
        Returns:
            tuple: (dominant_emotion, average_confidence)
        """
        if not self.emotion_history:
            return 'neutral', 0.0
        
        # Most frequent emotion
        emotion_counts = Counter(self.emotion_history)
        dominant_emotion = emotion_counts.most_common(1)[0][0]
        
        # Average confidence
        avg_confidence = sum(self.confidence_history) / len(self.confidence_history) if self.confidence_history else 0.0
        
        return dominant_emotion, round(avg_confidence, 2)
    
    def get_emotion_distribution(self):
        """
        Get distribution of emotions in history
        
        Returns:
            dict: Emotion counts
        """
        if not self.emotion_history:
            return {}
        
        return dict(Counter(self.emotion_history))
    
    def get_interview_score(self):
        """
        Calculate interview score based on emotional presentation
        
        Returns:
            dict: Score details
        """
        if not self.emotion_history:
            return {
                'overall_score': 50,
                'positive_percentage': 0,
                'negative_percentage': 0,
                'neutral_percentage': 100,
                'feedback': 'No speech detected'
            }
        
        total = len(self.emotion_history)
        positive = sum(1 for e in self.emotion_history if e in self.positive_emotions)
        negative = sum(1 for e in self.emotion_history if e in self.negative_emotions)
        neutral = sum(1 for e in self.emotion_history if e in self.neutral_emotions)
        
        positive_pct = (positive / total) * 100
        negative_pct = (negative / total) * 100
        neutral_pct = (neutral / total) * 100
        
        # Calculate score (positive emotions are good, negative are bad)
        overall_score = min(100, max(0, 50 + positive_pct * 0.5 - negative_pct * 0.3))
        
        # Generate feedback
        if overall_score >= 80:
            feedback = "Excellent emotional presentation! You displayed confidence and positivity."
        elif overall_score >= 60:
            feedback = "Good emotional presentation. Consider maintaining more calm and confident tone."
        elif overall_score >= 40:
            feedback = "Average emotional presentation. Work on displaying more positive emotions."
        else:
            feedback = "Needs improvement. Practice maintaining calm and confident demeanor."
        
        return {
            'overall_score': round(overall_score, 1),
            'positive_percentage': round(positive_pct, 1),
            'negative_percentage': round(negative_pct, 1),
            'neutral_percentage': round(neutral_pct, 1),
            'dominant_emotion': self.get_dominant_emotion()[0],
            'average_confidence': self.get_dominant_emotion()[1],
            'feedback': feedback
        }
    
    def start_session(self):
        """Start a new emotion recognition session"""
        self.session_active = True
        self.session_results = []
        self.emotion_history.clear()
        self.confidence_history.clear()
        print("🟢 Speech emotion recognition session started")
    
    def end_session(self):
        """End the current session and return summary"""
        self.session_active = False
        score = self.get_interview_score()
        print("🔴 Speech emotion recognition session ended")
        return score
    
    def run_realtime_session(self, duration=60, chunk_duration=3):
        """
        Run a real-time emotion recognition session
        
        Args:
            duration: Total session duration in seconds
            chunk_duration: Duration of each analysis chunk
            
        Returns:
            dict: Session summary
        """
        print("🟢 Real-Time Speech Emotion Recognition")
        print(f"Speak naturally for the next {duration} seconds...\n")
        
        self.start_session()
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                emotion, confidence = self.record_and_predict(duration=chunk_duration)
                self.session_results.append((emotion, confidence))
                print(f"🎤 Detected: {emotion} ({confidence}%)\n")
            except KeyboardInterrupt:
                print("\n⚠ Session interrupted by user")
                break
            except Exception as e:
                print(f"⚠ Error during recording: {e}")
        
        return self.end_session()
    
    def reset(self):
        """Reset all history and state"""
        self.emotion_history.clear()
        self.confidence_history.clear()
        self.session_results = []
        self.session_active = False


# Convenience function for quick analysis
def analyze_speech_emotion(audio_file):
    """
    Quick function to analyze speech emotion from a file
    
    Args:
        audio_file: Path to audio file
        
    Returns:
        tuple: (emotion, confidence)
    """
    recognizer = RealtimeSpeechEmotionRecognizer()
    return recognizer.predict_emotion_from_file(audio_file)


# Singleton instance for easy access
_recognizer_instance = None

def get_speech_emotion_recognizer():
    """Get or create singleton recognizer instance"""
    global _recognizer_instance
    if _recognizer_instance is None:
        _recognizer_instance = RealtimeSpeechEmotionRecognizer()
    return _recognizer_instance


if __name__ == "__main__":
    # Test the module
    print("Testing Real-Time Speech Emotion Recognition Module")
    print("=" * 50)
    
    recognizer = RealtimeSpeechEmotionRecognizer()
    
    # Run a short test session
    summary = recognizer.run_realtime_session(duration=15, chunk_duration=3)
    
    print("\n" + "=" * 50)
    print("SESSION SUMMARY")
    print("=" * 50)
    for key, value in summary.items():
        print(f"{key}: {value}")
