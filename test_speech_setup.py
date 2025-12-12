"""
Test Script for Speech Analyzer
Verifies installation and basic functionality
"""
import sys
import os

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def test_dependencies():
    """Test if all required packages are installed"""
    print_header("Testing Dependencies")
    
    packages = [
        ('flask', 'Flask'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('mediapipe', 'MediaPipe'),
        ('tensorflow', 'TensorFlow'),
        ('transformers', 'HuggingFace Transformers'),
        ('torch', 'PyTorch'),
        ('librosa', 'librosa'),
        ('soundfile', 'soundfile'),
    ]
    
    missing = []
    
    for module_name, display_name in packages:
        try:
            __import__(module_name)
            print(f"✓ {display_name:<25} OK")
        except ImportError:
            print(f"✗ {display_name:<25} MISSING")
            missing.append(display_name)
    
    # Optional PyAudio
    try:
        import pyaudio
        print(f"✓ {'PyAudio':<25} OK")
    except ImportError:
        print(f"⚠ {'PyAudio':<25} MISSING (optional, but needed for audio capture)")
        print("  Install with: pip install pyaudio OR pip install pipwin && pipwin install pyaudio")
    
    if missing:
        print(f"\n❌ Missing required packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All required dependencies installed!")
    return True

def test_speech_analyzer():
    """Test speech analyzer initialization"""
    print_header("Testing Speech Analyzer")
    
    try:
        from src.speech_analyzer import SpeechAnalyzer
        print("✓ Speech analyzer module imported")
        
        print("\nInitializing speech analyzer (this may take a moment)...")
        analyzer = SpeechAnalyzer()
        print("✓ Speech analyzer initialized successfully!")
        
        # Test with dummy audio
        import numpy as np
        print("\nTesting with sample audio...")
        sample_audio = np.random.randn(16000 * 3) * 0.1  # 3 seconds
        result = analyzer.analyze_audio_chunk(sample_audio)
        
        print(f"✓ Analysis completed!")
        print(f"  Emotion: {result['emotion']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Clarity: {result['clarity_score']:.1f}%")
        print(f"  Vocal Confidence: {result['confidence_score']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_audio_capture():
    """Test audio capture (PyAudio)"""
    print_header("Testing Audio Capture")
    
    try:
        import pyaudio
        print("✓ PyAudio installed")
        
        from src.speech_analyzer import AudioCapture
        print("✓ AudioCapture class imported")
        
        # Just test initialization, don't actually record
        audio_capture = AudioCapture()
        print("✓ AudioCapture initialized")
        print("\n⚠ Note: Actual recording not tested (requires microphone)")
        print("  Will be tested when you run the application")
        
        return True
        
    except ImportError:
        print("⚠ PyAudio not installed - audio capture will not work")
        print("  Install with: pip install pipwin && pipwin install pyaudio")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_model_download():
    """Check if model is downloaded"""
    print_header("Checking Model Files")
    
    try:
        import torch
        from transformers import Wav2Vec2ForSequenceClassification
        
        model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        
        print(f"Model: {model_name}")
        print(f"Cache directory: {cache_dir}")
        
        # Try to load model
        print("\nChecking if model is cached...")
        try:
            model = Wav2Vec2ForSequenceClassification.from_pretrained(
                model_name,
                local_files_only=True  # Only check cache
            )
            print("✓ Model is already downloaded and cached!")
            return True
        except:
            print("⚠ Model not found in cache")
            print("\nTo download the model, run:")
            print("  python setup_speech_models.py")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_integration():
    """Test integration with main app"""
    print_header("Testing Integration")
    
    try:
        # Import main app components
        print("Checking app.py imports...")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from src.motion_detector import MotionDetector
        print("✓ MotionDetector imported")
        
        from src.face_analyzer import FaceAnalyzer
        print("✓ FaceAnalyzer imported")
        
        from src.analytics import InterviewAnalytics
        print("✓ InterviewAnalytics imported")
        
        from src.speech_analyzer import SpeechAnalyzer, AudioCapture
        print("✓ SpeechAnalyzer imported")
        
        print("\n✓ All modules can be imported successfully!")
        print("✓ Integration test passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  AI INTERVIEW ANALYZER - SPEECH ANALYSIS TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Test 1: Dependencies
    results.append(("Dependencies", test_dependencies()))
    
    # Test 2: Speech Analyzer
    if results[0][1]:  # Only if dependencies passed
        results.append(("Speech Analyzer", test_speech_analyzer()))
    
    # Test 3: Audio Capture
    results.append(("Audio Capture", test_audio_capture()))
    
    # Test 4: Model Download
    results.append(("Model Cache", test_model_download()))
    
    # Test 5: Integration
    results.append(("Integration", test_integration()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("  ✓ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✓ Your system is ready for speech analysis!")
        print("\nNext steps:")
        print("  1. If model is not cached, run: python setup_speech_models.py")
        print("  2. Start the application: python app.py")
        print("  3. Open browser: http://localhost:5000")
        print("\n" + "=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("  ⚠ SOME TESTS FAILED")
        print("=" * 70)
        print("\nPlease fix the issues above and run this test again.")
        print("For help, see: SPEECH_SETUP.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
