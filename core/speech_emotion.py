"""
Simplified Speech Emotion Analyzer
Uses pre-trained CNN model for speech emotion recognition
Works with RAVDESS-trained model - no training required
"""
import numpy as np
import os
import time
import threading
import queue
from collections import deque, Counter

# Suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Import audio processing
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("⚠ librosa not available. Install: pip install librosa")

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("⚠ sounddevice not available. Install: pip install sounddevice")

# Import TensorFlow
try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠ TensorFlow not available")


class SpeechEmotionAnalyzer:
    """
    Real-time speech emotion detection using pre-trained CNN model
    Emotions: Neutral, Calm, Happy, Sad, Angry, Fearful, Disgust, Surprised
    """
    
    # RAVDESS emotion labels
    EMOTION_LABELS = ['Neutral', 'Calm', 'Happy', 'Sad', 'Angry', 'Fearful', 'Disgust', 'Surprised']
    
    # Interview-appropriate emotions
    POSITIVE_EMOTIONS = ['Happy', 'Calm', 'Neutral']
    NEGATIVE_EMOTIONS = ['Angry', 'Fearful', 'Sad', 'Disgust']
    
    def __init__(self, sample_rate=16000):
        """Initialize speech analyzer"""
        self.sample_rate = sample_rate
        self.model = None
        
        # History tracking
        self.emotion_history = deque(maxlen=20)
        self.confidence_history = deque(maxlen=20)
        
        # Audio buffer
        self.audio_buffer = deque(maxlen=sample_rate * 10)  # 10 seconds
        
        # Current state
        self.current_emotion = 'Neutral'
        self.current_confidence = 0.0
        self.is_speaking = False
        
        # Initialize model
        self._initialize()
    
    def _initialize(self):
        """Load pre-trained model"""
        if not TF_AVAILABLE:
            print("⚠ TensorFlow not available, using fallback analysis")
            return
        
        model_paths = [
            "models/speech_emotion_model.h5",
            "models/ravdess_cnn.h5",
            "support 2/SpeechEmotionAI/models/emotion_cnn_model.h5",
            "support 3/huaiyukhaw-speech-emotion-recognition-9c75f9f/models/cnn.h5"
        ]
        
        for path in model_paths:
            if os.path.exists(path):
                try:
                    print(f"Loading speech emotion model: {path}")
                    self.model = keras.models.load_model(path, compile=False)
                    
                    # Get expected input shape
                    self.input_shape = self.model.input_shape
                    print(f"✓ Speech emotion model loaded! Input shape: {self.input_shape}")
                    return
                except Exception as e:
                    print(f"⚠ Failed to load {path}: {e}")
        
        print("⚠ No speech emotion model found. Using feature-based analysis.")
    
    def analyze(self, audio_data, sample_rate=None):
        """
        Analyze audio for emotion
        
        Args:
            audio_data: numpy array of audio samples
            sample_rate: sample rate (optional)
            
        Returns:
            dict: Analysis results
        """
        if audio_data is None or len(audio_data) < 1000:
            return self._empty_result()
        
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        # Resample if needed
        if sample_rate != self.sample_rate and LIBROSA_AVAILABLE:
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=self.sample_rate)
        
        # Check if speaking (energy threshold)
        rms = np.sqrt(np.mean(audio_data ** 2))
        self.is_speaking = rms > 0.01
        
        if not self.is_speaking:
            return self._empty_result(silence=True)
        
        # Predict emotion
        emotion, confidence = self._predict_emotion(audio_data)
        
        # Update history
        self.emotion_history.append(emotion)
        self.confidence_history.append(confidence)
        
        # Smooth prediction
        if len(self.emotion_history) >= 3:
            emotion_counts = Counter(self.emotion_history)
            emotion = emotion_counts.most_common(1)[0][0]
        
        self.current_emotion = emotion
        self.current_confidence = confidence
        
        # Calculate additional metrics
        features = self._extract_features(audio_data)
        
        # Ensure all values are JSON serializable
        return {
            'emotion': str(emotion),
            'confidence': float(confidence),
            'is_speaking': True,
            'volume': float(features.get('volume', 0)),
            'pitch': float(features.get('pitch', 0)),
            'energy': float(features.get('energy', 0)),
            'clarity_score': float(features.get('clarity', 50)),
            'confidence_score': float(self._calculate_vocal_confidence(features))
        }
    
    def _predict_emotion(self, audio_data):
        """Predict emotion from audio"""
        if self.model is None:
            # Fallback: Use energy-based heuristics
            return self._fallback_prediction(audio_data)
        
        try:
            # Extract MFCC features
            if not LIBROSA_AVAILABLE:
                return 'Neutral', 50.0
            
            # Extract MFCCs
            mfcc = librosa.feature.mfcc(y=audio_data, sr=self.sample_rate, n_mfcc=40)
            
            # Prepare input based on model's expected shape
            if self.input_shape:
                expected_features = self.input_shape[-1] if len(self.input_shape) > 1 else 40
                
                # Mean across time
                mfcc_mean = np.mean(mfcc, axis=1)
                
                # Adjust feature size if needed
                if len(mfcc_mean) < expected_features:
                    mfcc_mean = np.pad(mfcc_mean, (0, expected_features - len(mfcc_mean)))
                elif len(mfcc_mean) > expected_features:
                    mfcc_mean = mfcc_mean[:expected_features]
                
                # Reshape for model
                features = mfcc_mean.reshape(1, -1)
            else:
                features = np.mean(mfcc, axis=1).reshape(1, -1)
            
            # Predict
            predictions = self.model.predict(features, verbose=0)[0]
            
            # Handle different output sizes
            if len(predictions) > len(self.EMOTION_LABELS):
                predictions = predictions[:len(self.EMOTION_LABELS)]
            elif len(predictions) < len(self.EMOTION_LABELS):
                # Map to available labels
                labels = self.EMOTION_LABELS[:len(predictions)]
            else:
                labels = self.EMOTION_LABELS
            
            emotion_idx = np.argmax(predictions)
            confidence = float(predictions[emotion_idx]) * 100
            
            return labels[emotion_idx], confidence
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return self._fallback_prediction(audio_data)
    
    def _fallback_prediction(self, audio_data):
        """
        Advanced fallback emotion prediction using audio features
        Uses prosodic features (pitch, energy, tempo) for emotion classification
        """
        if not LIBROSA_AVAILABLE:
            return 'Neutral', 50.0
        
        try:
            # Extract comprehensive features
            # Energy/RMS
            rms = np.sqrt(np.mean(audio_data ** 2))
            rms_db = 20 * np.log10(rms + 1e-8) + 60  # Normalize to 0-60 range
            
            # Zero crossing rate (correlates with high-frequency content)
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio_data))
            
            # Spectral centroid (brightness)
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate))
            
            # Tempo/speech rate estimation
            onset_env = librosa.onset.onset_strength(y=audio_data, sr=self.sample_rate)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=self.sample_rate)[0]
            
            # Pitch estimation
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=self.sample_rate)
            pitch_values = []
            for t in range(pitches.shape[1]):
                idx = magnitudes[:, t].argmax()
                if pitches[idx, t] > 0:
                    pitch_values.append(pitches[idx, t])
            
            avg_pitch = np.mean(pitch_values) if pitch_values else 150
            pitch_std = np.std(pitch_values) if len(pitch_values) > 1 else 0
            
            # Spectral rolloff (frequency below which 85% of energy is contained)
            rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio_data, sr=self.sample_rate))
            
            # Classify emotion based on acoustic features
            # High energy + high pitch + fast tempo = Angry/Happy
            # Low energy + low pitch + slow tempo = Sad
            # Moderate + stable = Calm/Neutral
            
            confidence = 60.0
            
            if rms_db > 45 and zcr > 0.12 and tempo > 120:
                # High energy, noisy, fast
                if pitch_std > 50:
                    emotion = 'Angry'
                    confidence = 65.0
                else:
                    emotion = 'Happy'
                    confidence = 65.0
            elif rms_db > 40 and avg_pitch > 200 and pitch_std > 40:
                # High pitch variation, energetic
                emotion = 'Surprised'
                confidence = 60.0
            elif rms_db < 30 and tempo < 100:
                # Low energy, slow
                if avg_pitch < 150:
                    emotion = 'Sad'
                    confidence = 60.0
                else:
                    emotion = 'Fearful'
                    confidence = 55.0
            elif rms_db > 35 and pitch_std < 30 and tempo < 130:
                # Moderate energy, stable pitch
                emotion = 'Calm'
                confidence = 65.0
            else:
                # Default
                emotion = 'Neutral'
                confidence = 70.0
            
            return emotion, confidence
                
        except Exception as e:
            return 'Neutral', 50.0
    
    def _extract_features(self, audio_data):
        """Extract audio features for metrics"""
        features = {
            'volume': 50.0,
            'pitch': 0.0,
            'energy': 50.0,
            'clarity': 50.0
        }
        
        if not LIBROSA_AVAILABLE:
            return features
        
        try:
            # Volume (RMS in dB-like scale)
            rms = np.sqrt(np.mean(audio_data ** 2))
            db = 20 * np.log10(rms + 1e-8)
            features['volume'] = float(np.clip((db + 60) / 60 * 100, 0, 100))
            
            # Pitch estimation
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=self.sample_rate)
            pitch_values = [pitches[magnitudes[:, t].argmax(), t] 
                          for t in range(pitches.shape[1])]
            pitch_values = [p for p in pitch_values if p > 0]
            features['pitch'] = float(np.mean(pitch_values)) if pitch_values else 0.0
            
            # Energy (spectral centroid)
            spectral = librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate)
            features['energy'] = float(np.mean(spectral))
            
            # Clarity (inverse of spectral flatness)
            flatness = librosa.feature.spectral_flatness(y=audio_data)
            features['clarity'] = float((1 - np.mean(flatness)) * 100)
            
        except:
            pass
        
        return features
    
    def _calculate_vocal_confidence(self, features):
        """Calculate vocal confidence score"""
        volume = features.get('volume', 50)
        clarity = features.get('clarity', 50)
        
        # Volume contribution (moderate volume is confident)
        volume_score = 100 - abs(volume - 65) * 2
        volume_score = np.clip(volume_score, 0, 100)
        
        # Clarity contribution
        clarity_score = clarity
        
        # Combine
        confidence = volume_score * 0.5 + clarity_score * 0.5
        return np.clip(confidence, 0, 100)
    
    def _empty_result(self, silence=False):
        """Return empty result"""
        return {
            'emotion': 'Neutral',
            'confidence': 0.0,
            'is_speaking': bool(not silence),
            'volume': 0.0,
            'pitch': 0.0,
            'energy': 0.0,
            'clarity_score': 50.0,
            'confidence_score': 50.0
        }
    
    def get_statistics(self):
        """Get speech analysis statistics"""
        if len(self.emotion_history) == 0:
            return {
                'dominant_emotion': 'Neutral',
                'emotion': 'Neutral',
                'confidence': 0.0,
                'emotion_distribution': {},
                'positive_emotion_percentage': 0.0,
                'negative_emotion_percentage': 0.0,
                'avg_confidence': 0.0,
                'interview_score': 50
            }
        
        # Emotion distribution
        emotion_counts = Counter(self.emotion_history)
        total = len(self.emotion_history)
        distribution = {str(e): float((c / total) * 100) for e, c in emotion_counts.items()}
        
        # Positive/negative percentage
        positive_pct = float(sum(distribution.get(e, 0) for e in self.POSITIVE_EMOTIONS))
        negative_pct = float(sum(distribution.get(e, 0) for e in self.NEGATIVE_EMOTIONS))
        
        avg_conf = float(np.mean(list(self.confidence_history))) if self.confidence_history else 0.0
        
        # Calculate interview score (0-100)
        # Higher positive emotions = higher score
        interview_score = min(100, max(0, 50 + (positive_pct - negative_pct) / 2))
        
        dominant = str(emotion_counts.most_common(1)[0][0])
        
        return {
            'dominant_emotion': dominant,
            'emotion': dominant,  # Alias for frontend
            'confidence': avg_conf / 100.0 if avg_conf > 1 else avg_conf,  # Normalized for frontend
            'emotion_distribution': distribution,
            'positive_emotion_percentage': positive_pct,
            'negative_emotion_percentage': negative_pct,
            'avg_confidence': avg_conf,
            'interview_score': interview_score
        }
    
    def reset(self):
        """Reset analyzer state"""
        self.emotion_history.clear()
        self.confidence_history.clear()
        self.audio_buffer.clear()
        self.current_emotion = 'Neutral'
        self.current_confidence = 0.0
        self.is_speaking = False
    
    def reset_history(self):
        """Alias for reset() - clears all history"""
        self.reset()


class AudioCapture:
    """
    Real-time audio capture using sounddevice
    More reliable than PyAudio on Windows
    """
    
    def __init__(self, sample_rate=16000, chunk_duration=0.1):
        """Initialize audio capture"""
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
    
    def start_recording(self):
        """Start audio recording"""
        if not SOUNDDEVICE_AVAILABLE:
            print("⚠ sounddevice not available")
            return False
        
        try:
            self.is_recording = True
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
            self.stream.start()
            print("✓ Audio recording started")
            return True
            
        except Exception as e:
            print(f"⚠ Error starting audio: {e}")
            self.is_recording = False
            return False
    
    def start(self):
        """Alias for start_recording()"""
        return self.start_recording()
    
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                break
        
        print("✓ Audio recording stopped")
    
    def stop(self):
        """Alias for stop_recording()"""
        self.stop_recording()
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream"""
        if self.is_recording:
            self.audio_queue.put(indata.copy().flatten())
    
    def get_audio_chunk(self, duration=3.0):
        """
        Get audio chunk of specified duration
        
        Args:
            duration: Duration in seconds
            
        Returns:
            numpy array of audio data
        """
        num_samples = int(self.sample_rate * duration)
        chunks = []
        
        timeout = time.time() + duration + 0.5
        while len(chunks) * self.chunk_size < num_samples and time.time() < timeout:
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                chunks.append(chunk)
            except queue.Empty:
                break
        
        if chunks:
            audio = np.concatenate(chunks)
            # Trim or pad to exact duration
            if len(audio) > num_samples:
                audio = audio[:num_samples]
            elif len(audio) < num_samples:
                audio = np.pad(audio, (0, num_samples - len(audio)))
            return audio
        
        return np.zeros(num_samples, dtype=np.float32)
    
    def get_chunk(self, duration=3.0):
        """Alias for get_audio_chunk()"""
        return self.get_audio_chunk(duration)


# Test
if __name__ == "__main__":
    print("Testing Speech Emotion Analyzer...")
    
    analyzer = SpeechEmotionAnalyzer()
    
    # Test with synthetic audio
    duration = 3.0
    test_audio = np.random.randn(int(16000 * duration)) * 0.1
    result = analyzer.analyze(test_audio)
    
    print(f"Result: {result}")
    print("✓ Test complete!")
