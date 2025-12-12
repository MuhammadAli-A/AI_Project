# Example Test Scripts

This directory contains standalone test scripts to verify individual components.

## Available Tests

### test_motion.py
Tests the motion detection module independently.

**Usage**:
```bash
python examples/test_motion.py
```

**What it does**:
- Opens your webcam
- Detects motion in real-time
- Displays motion percentage and activity level
- Press 'q' to quit

### test_face.py
Tests the face analysis module independently.

**Usage**:
```bash
python examples/test_face.py
```

**What it does**:
- Opens your webcam
- Detects face, eye contact, and emotions
- Displays face mesh overlay
- Prints analysis results
- Press 'q' to quit

## Requirements

Make sure you have installed all dependencies:
```bash
pip install -r requirements.txt
```

## Troubleshooting

If tests fail:
1. Ensure webcam is working
2. Check that no other application is using the camera
3. Verify all dependencies are installed
4. Try updating OpenCV: `pip install --upgrade opencv-python`
