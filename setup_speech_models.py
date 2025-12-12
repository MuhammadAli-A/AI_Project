"""
Setup and Model Download Script for AI Interview Analyzer
Downloads HuggingFace pre-trained models for speech analysis
"""
import os
import sys
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor


def download_speech_models():
    """Download and cache HuggingFace models"""
    
    print("=" * 70)
    print("AI Interview Analyzer - Speech Model Setup")
    print("=" * 70)
    print()
    
    # Model to download
    model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
    
    print(f"Downloading model: {model_name}")
    print("This may take a few minutes depending on your internet connection...")
    print()
    
    try:
        # Download feature extractor
        print("📥 Downloading feature extractor...")
        feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        print("✓ Feature extractor downloaded successfully!")
        
        # Download model
        print("📥 Downloading Wav2Vec2 model (~300MB)...")
        model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
        print("✓ Model downloaded successfully!")
        
        print()
        print("=" * 70)
        print("✓ Setup Complete!")
        print("=" * 70)
        print()
        print("Models are cached and ready to use.")
        print("You can now run the application with: python app.py")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Error during setup:")
        print("=" * 70)
        print(f"{str(e)}")
        print()
        print("Troubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Ensure you have enough disk space (~500MB)")
        print("3. Try running: pip install --upgrade transformers torch")
        print()
        return False


def check_dependencies():
    """Check if required packages are installed"""
    
    print("Checking dependencies...")
    print()
    
    required_packages = [
        ('transformers', 'transformers'),
        ('torch', 'torch'),
        ('librosa', 'librosa'),
        ('soundfile', 'soundfile')
    ]
    
    missing_packages = []
    
    for display_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {display_name} is installed")
        except ImportError:
            print(f"✗ {display_name} is NOT installed")
            missing_packages.append(display_name)
    
    print()
    
    if missing_packages:
        print("=" * 70)
        print("Missing dependencies detected!")
        print("=" * 70)
        print()
        print("Please install missing packages:")
        print(f"  pip install {' '.join(missing_packages)}")
        print()
        print("Or install all requirements:")
        print("  pip install -r requirements.txt")
        print()
        return False
    
    return True


def main():
    """Main setup function"""
    
    print()
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    print("=" * 70)
    print()
    
    # Download models
    success = download_speech_models()
    
    if success:
        print("Note: On first run, the application may take a few seconds")
        print("      to load the models into memory.")
        print()
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
