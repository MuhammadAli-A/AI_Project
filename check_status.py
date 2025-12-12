"""
Simple Model & Dataset Check
"""
import os

print("\n" + "="*70)
print("  MODEL & DATASET STATUS CHECK")
print("="*70)

# Check 1: Python packages
print("\n[1] Checking Python Packages...")
packages = {
    'transformers': 'HuggingFace Transformers',
    'torch': 'PyTorch',
    'librosa': 'librosa',
    'soundfile': 'soundfile',
    'mediapipe': 'MediaPipe',
    'cv2': 'OpenCV',
    'flask': 'Flask'
}

all_installed = True
for pkg, name in packages.items():
    try:
        __import__(pkg)
        print(f"  ✓ {name}")
    except ImportError:
        print(f"  ✗ {name} - NOT INSTALLED")
        all_installed = False

# Check 2: HuggingFace Cache
print("\n[2] Checking HuggingFace Model Cache...")
cache_locations = [
    os.path.expanduser("~/.cache/huggingface/hub"),
    os.path.expanduser("~/.cache/huggingface"),
    os.path.join(os.getcwd(), ".cache"),
]

model_found = False
for location in cache_locations:
    if os.path.exists(location):
        print(f"  Cache location: {location}")
        try:
            files = os.listdir(location)
            if files:
                print(f"  Files found: {len(files)} items")
                for f in files[:5]:
                    print(f"    - {f}")
                model_found = True
                break
        except Exception as e:
            pass

if not model_found:
    print("  ⚠ Model cache not found - will download on first run")

# Check 3: Try loading model
print("\n[3] Attempting to Load Wav2Vec2 Model...")
if all_installed:
    try:
        from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
        model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
        
        print(f"  Loading: {model_name}")
        print("  (This will download ~300MB if not cached)")
        
        extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
        
        print(f"  ✓ Model loaded successfully!")
        print(f"  ✓ Emotions: {list(model.config.id2label.values())}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
else:
    print("  ⚠ Skipped (missing packages)")

# Check 4: Project files
print("\n[4] Checking Project Files...")
required_files = [
    'app.py',
    'src/speech_analyzer.py',
    'src/face_analyzer.py',
    'src/analytics.py',
    'requirements.txt'
]

for file in required_files:
    if os.path.exists(file):
        print(f"  ✓ {file}")
    else:
        print(f"  ✗ {file} - MISSING")

# Info about datasets
print("\n[5] Dataset Information...")
print("  📊 Training Datasets (OPTIONAL - not required):")
print("  ")
print("  1. TESS (Toronto Emotional Speech Set)")
print("     Size: 281 MB")
print("     Link: https://www.kaggle.com/datasets/ejlok1/toronto-emotional-speech-set-tess")
print("  ")
print("  2. RAVDESS (Ryerson Audio-Visual Database)")
print("     Size: 2+ GB")
print("     Link: https://www.kaggle.com/datasets/uwrfkaggle/ravdess-emotional-speech-audio")
print("  ")
print("  3. ESD (Emotional Speech Dataset)")
print("     Size: 2 GB")
print("     Link: https://github.com/HLTSingapore/Emotional-Speech-Data")
print("  ")
print("  ⚠ NOTE: These datasets are ONLY needed if you want to:")
print("     - Fine-tune the model")
print("     - Train a custom model")
print("     - Research/experimentation")
print("  ")
print("  ✅ The pre-trained Wav2Vec2 model works perfectly WITHOUT datasets!")

# Summary
print("\n" + "="*70)
print("  SUMMARY")
print("="*70)

if all_installed:
    print("\n✅ All packages installed")
else:
    print("\n⚠ Some packages missing - run: pip install -r requirements.txt")

print("\n📋 Next Steps:")
print("  1. Models will auto-download on first run (~300MB)")
print("  2. Datasets are optional (only for training)")
print("  3. Start app: python app.py")
print("  4. Open: http://localhost:5000")

print("\n" + "="*70)
