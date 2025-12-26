# Core Interview Analyzer Modules
# Import core analyzers
try:
    from .realtime_speech_emotion import RealtimeSpeechEmotionRecognizer, get_speech_emotion_recognizer
except ImportError as e:
    print(f"⚠ Could not import realtime_speech_emotion: {e}")
    RealtimeSpeechEmotionRecognizer = None
    get_speech_emotion_recognizer = None

try:
    from .face_emotion import FaceEmotionAnalyzer
except ImportError as e:
    print(f"⚠ Could not import face_emotion: {e}")
    FaceEmotionAnalyzer = None

try:
    from .speech_emotion import SpeechEmotionAnalyzer
except ImportError as e:
    print(f"⚠ Could not import speech_emotion: {e}")
    SpeechEmotionAnalyzer = None

try:
    from .fusion import FusionAnalyzer
except ImportError as e:
    print(f"⚠ Could not import fusion: {e}")
    FusionAnalyzer = None

__all__ = [
    'RealtimeSpeechEmotionRecognizer',
    'get_speech_emotion_recognizer', 
    'FaceEmotionAnalyzer',
    'SpeechEmotionAnalyzer',
    'FusionAnalyzer'
]