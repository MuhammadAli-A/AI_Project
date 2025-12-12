"""
Speech Analyzer Module using HuggingFace Pre-trained Models
Advanced speech emotion recognition and communication analysis
"""
import numpy as np
import librosa
import soundfile as sf
import torch
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
import threading
import queue
import time
from collections import deque, Counter
import warnings
warnings.filterwarnings('ignore')


class SpeechAnalyzer:
    """
    Advanced Speech Analyzer using HuggingFace Wav2Vec2 models
    Provides real-time speech emotion recognition and communication metrics
    """
    
    def __init__(self, model_name="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"):
        """
        Initialize Speech Analyzer with pre-trained model
        
        Args:
            model_name: HuggingFace model identifier
        """
        print("Initializing Speech Analyzer...")
        print(f"Loading model: {model_name}")
        
        try:
            # Load pre-trained model and feature extractor
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"Using device: {self.device}")
            
            self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
            self.model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # Emotion labels (model-specific)
            self.emotion_labels = {
                0: 'angry',
                1: 'calm',
                2: 'disgust',
                3: 'fear',
                4: 'happy',
                5: 'neutral',
                6: 'sad',
                7: 'surprise'
            }
            
            # Interview-specific emotion mapping for scoring
            self.positive_emotions = ['happy', 'calm', 'neutral']
            self.negative_emotions = ['angry', 'fear', 'sad', 'disgust']
            self.neutral_emotions = ['surprise']
            
            print("✓ Model loaded successfully!")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to basic audio analysis...")
            self.model = None
        
        # Audio parameters
        self.sample_rate = 16000  # Required by Wav2Vec2
        self.chunk_duration = 3.0  # Analyze 3-second chunks
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # Statistics tracking
        self.emotion_history = deque(maxlen=20)  # Last 20 predictions
        self.audio_buffer = deque(maxlen=self.chunk_size * 2)
        self.speaking_segments = []
        self.silence_segments = []
        
        # Communication metrics
        self.total_speech_time = 0
        self.total_silence_time = 0
        self.avg_volume = 0
        self.pitch_values = []
        self.energy_values = []
        self.filler_words_count = 0
        
        # Session tracking
        self.session_start_time = None
        self.is_analyzing = False
        
    def analyze_audio_chunk(self, audio_data, sample_rate=16000):
        """
        Analyze a chunk of audio for emotion and communication metrics
        
        Args:
            audio_data: Audio data (numpy array)
            sample_rate: Sample rate of audio
            
        Returns:
            dict: Analysis results with emotion, confidence, and metrics
        """
        try:
            # Resample if needed
            if sample_rate != self.sample_rate:
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=sample_rate, 
                    target_sr=self.sample_rate
                )
            
            # Ensure minimum length
            if len(audio_data) < self.sample_rate:  # At least 1 second
                return self._get_empty_result()
            
            # Detect speech vs silence
            is_speech = self._detect_speech(audio_data)
            
            if not is_speech:
                return self._get_empty_result(is_silence=True)
            
            # Extract audio features
            volume = self._calculate_volume(audio_data)
            pitch = self._calculate_pitch(audio_data)
            energy = self._calculate_energy(audio_data)
            speaking_rate = self._estimate_speaking_rate(audio_data)
            
            # Emotion recognition using pre-trained model
            emotion, confidence = self._predict_emotion(audio_data)
            
            # Update statistics
            self._update_statistics(emotion, volume, pitch, energy, speaking_rate)
            
            # Calculate communication scores
            clarity_score = self._calculate_clarity_score(audio_data)
            confidence_score = self._calculate_confidence_score(volume, pitch, energy)
            
            return {
                'emotion': emotion,
                'confidence': float(confidence),
                'volume': float(volume),
                'pitch': float(pitch),
                'energy': float(energy),
                'speaking_rate': float(speaking_rate),
                'clarity_score': float(clarity_score),
                'confidence_score': float(confidence_score),
                'is_speech': True
            }
            
        except Exception as e:
            print(f"Error in audio analysis: {e}")
            return self._get_empty_result()
    
    def _predict_emotion(self, audio_data):
        """
        Predict emotion using Wav2Vec2 model
        
        Returns:
            tuple: (emotion_label, confidence)
        """
        if self.model is None:
            return 'neutral', 0.5
        
        try:
            # Normalize audio
            audio_data = audio_data / (np.max(np.abs(audio_data)) + 1e-8)
            
            # Extract features
            inputs = self.feature_extractor(
                audio_data, 
                sampling_rate=self.sample_rate, 
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {key: val.to(self.device) for key, val in inputs.items()}
            
            # Predict
            with torch.no_grad():
                logits = self.model(**inputs).logits
            
            # Get prediction
            predicted_ids = torch.argmax(logits, dim=-1)
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
            confidence = torch.max(probabilities).item()
            
            emotion_id = predicted_ids.item()
            emotion = self.emotion_labels.get(emotion_id, 'neutral')
            
            return emotion, confidence
            
        except Exception as e:
            print(f"Error in emotion prediction: {e}")
            return 'neutral', 0.5
    
    def _detect_speech(self, audio_data):
        """
        Detect if audio contains speech using energy threshold
        
        Returns:
            bool: True if speech detected
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_data**2))
        
        # Adaptive threshold
        threshold = 0.01  # Adjust based on your microphone
        
        return rms > threshold
    
    def _calculate_volume(self, audio_data):
        """Calculate average volume (RMS)"""
        rms = np.sqrt(np.mean(audio_data**2))
        # Convert to dB-like scale
        db = 20 * np.log10(rms + 1e-8)
        # Normalize to 0-100
        normalized = np.clip((db + 60) / 60 * 100, 0, 100)
        return normalized
    
    def _calculate_pitch(self, audio_data):
        """Calculate average pitch using autocorrelation"""
        try:
            # Use librosa to estimate pitch
            pitches, magnitudes = librosa.piptrack(
                y=audio_data, 
                sr=self.sample_rate,
                fmin=50,
                fmax=400
            )
            
            # Get pitch values with highest magnitude
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                return np.mean(pitch_values)
            return 0.0
            
        except Exception as e:
            return 0.0
    
    def _calculate_energy(self, audio_data):
        """Calculate spectral energy"""
        try:
            # Compute spectral centroid
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_data, 
                sr=self.sample_rate
            )[0]
            return np.mean(spectral_centroids)
        except:
            return 0.0
    
    def _estimate_speaking_rate(self, audio_data):
        """
        Estimate speaking rate (syllables per second)
        Uses zero-crossing rate as proxy
        """
        try:
            # Calculate zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
            
            # Estimate syllables (rough approximation)
            # Average ZCR correlates with speaking rate
            speaking_rate = np.mean(zcr) * 100  # Scale to interpretable range
            
            return speaking_rate
            
        except:
            return 0.0
    
    def _calculate_clarity_score(self, audio_data):
        """
        Calculate speech clarity score (0-100)
        Based on spectral characteristics
        """
        try:
            # Spectral flatness (measure of noisiness)
            flatness = librosa.feature.spectral_flatness(y=audio_data, sr=self.sample_rate)[0]
            
            # Spectral rolloff
            rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=self.sample_rate)[0]
            
            # Lower flatness = more tonal = clearer speech
            clarity = (1 - np.mean(flatness)) * 100
            clarity = np.clip(clarity, 0, 100)
            
            return clarity
            
        except:
            return 50.0
    
    def _calculate_confidence_score(self, volume, pitch, energy):
        """
        Calculate vocal confidence score (0-100)
        Based on volume stability, pitch variation, and energy
        """
        try:
            # Volume score (50-80 is ideal)
            volume_score = 100 - abs(volume - 65) * 2
            volume_score = np.clip(volume_score, 0, 100)
            
            # Pitch stability (if we have history)
            if len(self.pitch_values) > 5:
                pitch_std = np.std(self.pitch_values[-10:])
                pitch_score = 100 - np.clip(pitch_std, 0, 50) * 2
            else:
                pitch_score = 70
            
            # Energy score (higher energy = more confident)
            energy_score = np.clip(energy / 30, 0, 100)
            
            # Weighted combination
            confidence = (
                volume_score * 0.4 +
                pitch_score * 0.3 +
                energy_score * 0.3
            )
            
            return np.clip(confidence, 0, 100)
            
        except:
            return 50.0
    
    def _update_statistics(self, emotion, volume, pitch, energy, speaking_rate):
        """Update running statistics"""
        self.emotion_history.append(emotion)
        self.pitch_values.append(pitch)
        self.energy_values.append(energy)
        
        # Update averages
        if len(self.pitch_values) > 0:
            self.avg_volume = np.mean([p for p in self.pitch_values if p > 0])
    
    def _get_empty_result(self, is_silence=False):
        """Return empty result for silence or errors"""
        return {
            'emotion': 'neutral',
            'confidence': 0.0,
            'volume': 0.0,
            'pitch': 0.0,
            'energy': 0.0,
            'speaking_rate': 0.0,
            'clarity_score': 0.0,
            'confidence_score': 0.0,
            'is_speech': False
        }
    
    def get_statistics(self):
        """
        Get comprehensive speech statistics
        
        Returns:
            dict: Speech analysis statistics
        """
        if len(self.emotion_history) == 0:
            return {
                'dominant_emotion': 'neutral',
                'emotion_distribution': {},
                'avg_confidence': 0.0,
                'avg_clarity': 0.0,
                'speaking_time_percentage': 0.0
            }
        
        # Emotion distribution
        emotion_counts = Counter(self.emotion_history)
        total = len(self.emotion_history)
        emotion_distribution = {
            emotion: (count / total) * 100 
            for emotion, count in emotion_counts.items()
        }
        
        # Dominant emotion
        dominant_emotion = emotion_counts.most_common(1)[0][0]
        
        # Calculate averages (would need to store these in real implementation)
        return {
            'dominant_emotion': dominant_emotion,
            'emotion_distribution': emotion_distribution,
            'total_samples': total,
            'positive_emotion_percentage': sum(
                emotion_distribution.get(e, 0) 
                for e in self.positive_emotions
            ),
            'negative_emotion_percentage': sum(
                emotion_distribution.get(e, 0) 
                for e in self.negative_emotions
            )
        }
    
    def reset(self):
        """Reset all statistics"""
        self.emotion_history.clear()
        self.audio_buffer.clear()
        self.speaking_segments.clear()
        self.silence_segments.clear()
        self.pitch_values.clear()
        self.energy_values.clear()
        self.total_speech_time = 0
        self.total_silence_time = 0
        self.filler_words_count = 0
        self.session_start_time = None
    
    def start_session(self):
        """Start analysis session"""
        self.reset()
        self.session_start_time = time.time()
        self.is_analyzing = True
    
    def end_session(self):
        """End analysis session"""
        self.is_analyzing = False


class AudioCapture:
    """
    Real-time audio capture using PyAudio
    Handles microphone input and buffering
    """
    
    def __init__(self, sample_rate=16000, chunk_size=1024):
        """
        Initialize audio capture
        
        Args:
            sample_rate: Audio sample rate (Hz)
            chunk_size: Number of frames per buffer
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
        self.pyaudio_instance = None
        
    def start_recording(self):
        """Start audio recording"""
        try:
            import pyaudio
            
            self.pyaudio_instance = pyaudio.PyAudio()
            
            self.stream = self.pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            self.stream.start_stream()
            print("✓ Audio recording started")
            
        except Exception as e:
            print(f"Error starting audio recording: {e}")
            print("Note: PyAudio might need to be installed separately on Windows")
    
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        
        print("✓ Audio recording stopped")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        import pyaudio
        
        if self.is_recording:
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            self.audio_queue.put(audio_data)
        
        return (in_data, pyaudio.paContinue)
    
    def get_audio_chunk(self, duration=3.0):
        """
        Get accumulated audio chunk
        
        Args:
            duration: Duration in seconds
            
        Returns:
            numpy.ndarray: Audio data
        """
        num_samples = int(self.sample_rate * duration)
        audio_chunks = []
        
        # Collect audio from queue
        timeout = time.time() + duration + 0.5
        while len(audio_chunks) * self.chunk_size < num_samples and time.time() < timeout:
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                audio_chunks.append(chunk)
            except queue.Empty:
                break
        
        if audio_chunks:
            return np.concatenate(audio_chunks)
        return np.zeros(num_samples, dtype=np.float32)


# Test function
if __name__ == "__main__":
    print("Testing Speech Analyzer...")
    
    analyzer = SpeechAnalyzer()
    
    # Test with sample audio
    duration = 3.0
    sample_rate = 16000
    test_audio = np.random.randn(int(sample_rate * duration)) * 0.1
    
    result = analyzer.analyze_audio_chunk(test_audio, sample_rate)
    print("\nTest Result:")
    print(f"Emotion: {result['emotion']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Volume: {result['volume']:.2f}")
    print(f"Clarity: {result['clarity_score']:.2f}")
    print(f"Vocal Confidence: {result['confidence_score']:.2f}")
    
    print("\n✓ Speech Analyzer test completed!")
