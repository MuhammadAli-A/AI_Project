"""
Example script to test the face analyzer independently
"""
import cv2
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.face_analyzer import FaceAnalyzer


def main():
    """Test face analysis"""
    print("Starting face analysis test...")
    print("Press 'q' to quit")
    
    # Initialize
    cap = cv2.VideoCapture(0)
    analyzer = FaceAnalyzer()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Analyze face
        analyzed_frame, face_data = analyzer.analyze_face(frame)
        
        # Show frame
        cv2.imshow('Face Analysis Test', analyzed_frame)
        
        # Print stats
        print(f"Face: {face_data['face_detected']}, "
              f"Eye Contact: {face_data['eye_contact']}, "
              f"Emotion: {face_data['emotion']}")
        
        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Test completed!")


if __name__ == '__main__':
    main()
