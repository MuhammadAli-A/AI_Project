"""
Motion Detection Module
Detects and tracks motion in real-time video streams
"""
import cv2
import numpy as np
from collections import deque
import time


class MotionDetector:
    def __init__(self, min_area=500, delta_threshold=25):
        """
        Initialize motion detector
        
        Args:
            min_area: Minimum area for motion detection
            delta_threshold: Threshold for frame difference
        """
        self.min_area = min_area
        self.delta_threshold = delta_threshold
        self.avg_frame = None
        self.motion_history = deque(maxlen=30)  # Last 30 frames
        self.motion_detected = False
        self.motion_percentage = 0.0
        
    def detect_motion(self, frame):
        """
        Detect motion in the current frame
        
        Args:
            frame: Current video frame
            
        Returns:
            tuple: (motion_detected, motion_frame, motion_percentage)
        """
        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize average frame
        if self.avg_frame is None:
            self.avg_frame = gray.copy().astype("float")
            return False, frame, 0.0
        
        # Accumulate weighted average
        cv2.accumulateWeighted(gray, self.avg_frame, 0.5)
        
        # Compute difference between current frame and running average
        frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg_frame))
        
        # Threshold the delta image
        thresh = cv2.threshold(frame_delta, self.delta_threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        motion_frame = frame.copy()
        total_motion_area = 0
        
        # Loop over contours
        for contour in contours:
            # Filter small contours
            if cv2.contourArea(contour) < self.min_area:
                continue
                
            motion_detected = True
            total_motion_area += cv2.contourArea(contour)
            
            # Draw rectangle around motion
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(motion_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Calculate motion percentage
        frame_area = frame.shape[0] * frame.shape[1]
        motion_percentage = (total_motion_area / frame_area) * 100
        
        # Update history
        self.motion_history.append(motion_detected)
        self.motion_detected = motion_detected
        self.motion_percentage = motion_percentage
        
        return motion_detected, motion_frame, motion_percentage
    
    def get_motion_statistics(self):
        """
        Get motion statistics from history
        
        Returns:
            dict: Motion statistics
        """
        if len(self.motion_history) == 0:
            return {
                'motion_frequency': 0.0,
                'is_fidgeting': False,
                'activity_level': 'low'
            }
        
        motion_count = sum(self.motion_history)
        motion_frequency = motion_count / len(self.motion_history)
        
        # Determine if fidgeting (high motion frequency)
        is_fidgeting = motion_frequency > 0.7
        
        # Determine activity level
        if motion_frequency > 0.6:
            activity_level = 'high'
        elif motion_frequency > 0.3:
            activity_level = 'medium'
        else:
            activity_level = 'low'
        
        return {
            'motion_frequency': round(motion_frequency * 100, 2),
            'is_fidgeting': is_fidgeting,
            'activity_level': activity_level,
            'motion_percentage': round(self.motion_percentage, 2)
        }
    
    def reset(self):
        """Reset motion detector"""
        self.avg_frame = None
        self.motion_history.clear()
        self.motion_detected = False
        self.motion_percentage = 0.0
