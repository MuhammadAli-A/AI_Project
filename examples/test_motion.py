"""
Example script to test the motion detector independently
"""
import cv2
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.motion_detector import MotionDetector


def main():
    """Test motion detection"""
    print("Starting motion detection test...")
    print("Press 'q' to quit")
    
    # Initialize
    cap = cv2.VideoCapture(0)
    detector = MotionDetector()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect motion
        motion_detected, motion_frame, motion_percentage = detector.detect_motion(frame)
        
        # Get statistics
        stats = detector.get_motion_statistics()
        
        # Display info
        cv2.putText(motion_frame, f"Motion: {motion_percentage:.2f}%", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(motion_frame, f"Activity: {stats['activity_level']}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show frame
        cv2.imshow('Motion Detection Test', motion_frame)
        
        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Test completed!")


if __name__ == '__main__':
    main()
