"""
AI Interview Analyzer - Flask Backend
Main application server
"""
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import cv2
import threading
import time
from datetime import datetime
import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.motion_detector import MotionDetector
from src.face_analyzer import FaceAnalyzer
from src.analytics import InterviewAnalytics
from src.speech_analyzer import SpeechAnalyzer, AudioCapture

app = Flask(__name__)
CORS(app)

# Global variables
camera = None
motion_detector = MotionDetector()
face_analyzer = FaceAnalyzer()
analytics = InterviewAnalytics()
speech_analyzer = None  # Initialize later to avoid startup delay
audio_capture = None
is_recording = False
output_frame = None
lock = threading.Lock()
audio_lock = threading.Lock()


class VideoCamera:
    def __init__(self):
        """Initialize video camera"""
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
    def __del__(self):
        """Release camera"""
        if self.video.isOpened():
            self.video.release()
    
    def get_frame(self):
        """Get current frame from camera"""
        success, frame = self.video.read()
        if not success:
            return None
        return frame


def process_frame():
    """Process video frames continuously"""
    global output_frame, lock, is_recording
    
    video_camera = VideoCamera()
    frame_count = 0
    
    while True:
        frame = video_camera.get_frame()
        if frame is None:
            continue
        
        frame_count += 1
        
        # Detect motion
        motion_detected, motion_frame, motion_percentage = motion_detector.detect_motion(frame)
        
        # Analyze face (every frame)
        analyzed_frame, face_data = face_analyzer.analyze_face(motion_frame)
        
        # Record analytics data every 30 frames (~1 second)
        if is_recording and frame_count % 30 == 0:
            motion_stats = motion_detector.get_motion_statistics()
            face_stats = face_analyzer.get_face_statistics()
            
            analytics.add_motion_data(motion_stats)
            analytics.add_face_data(face_stats)
        
        # Add recording indicator
        if is_recording:
            cv2.circle(analyzed_frame, (20, 20), 10, (0, 0, 255), -1)
            cv2.putText(analyzed_frame, "REC", (40, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            # Add audio indicator
            cv2.circle(analyzed_frame, (20, 50), 8, (255, 0, 0), -1)
            cv2.putText(analyzed_frame, "AUDIO", (40, 55), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', analyzed_frame)
        frame_bytes = buffer.tobytes()
        
        # Update output frame
        with lock:
            output_frame = frame_bytes
        
        time.sleep(0.03)  # ~30 FPS


def generate_frames():
    """Generator function for video streaming"""
    global output_frame, lock
    
    while True:
        with lock:
            if output_frame is None:
                continue
            frame = output_frame
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_recording', methods=['POST'])
def start_recording():
    """Start interview recording"""
    global is_recording, speech_analyzer, audio_capture
    
    is_recording = True
    analytics.start_session()
    motion_detector.reset()
    face_analyzer.reset()
    
    # Initialize speech analyzer if not already done
    if speech_analyzer is None:
        try:
            speech_analyzer = SpeechAnalyzer()
            audio_capture = AudioCapture()
            print("✓ Speech analyzer initialized")
        except Exception as e:
            print(f"Warning: Could not initialize speech analyzer: {e}")
    
    # Start audio recording and analysis
    if speech_analyzer and audio_capture:
        try:
            speech_analyzer.start_session()
            audio_capture.start_recording()
            # Start audio processing thread
            audio_thread = threading.Thread(target=process_audio, daemon=True)
            audio_thread.start()
            print("✓ Audio recording started")
        except Exception as e:
            print(f"Warning: Could not start audio recording: {e}")
    
    return jsonify({
        'status': 'success',
        'message': 'Recording started',
        'timestamp': datetime.now().isoformat(),
        'audio_enabled': speech_analyzer is not None
    })


@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    """Stop interview recording"""
    global is_recording, speech_analyzer, audio_capture
    
    is_recording = False
    analytics.end_session()
    
    # Stop audio recording
    if speech_analyzer:
        speech_analyzer.end_session()
    if audio_capture:
        try:
            audio_capture.stop_recording()
        except:
            pass
    
    # Generate report
    report = analytics.generate_report()
    
    # Save report
    os.makedirs('reports', exist_ok=True)
    report_filename = f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path = os.path.join('reports', report_filename)
    analytics.save_report(report_path)
    
    return jsonify({
        'status': 'success',
        'message': 'Recording stopped',
        'report': report,
        'report_file': report_filename
    })


@app.route('/get_stats', methods=['GET'])
def get_stats():
    """Get current statistics"""
    motion_stats = motion_detector.get_motion_statistics()
    face_stats = face_analyzer.get_face_statistics()
    
    # Get speech statistics if available
    speech_stats = {}
    if speech_analyzer:
        try:
            speech_stats = speech_analyzer.get_statistics()
        except Exception as e:
            print(f"Error getting speech stats: {e}")
    
    return jsonify({
        'motion': motion_stats,
        'face': face_stats,
        'speech': speech_stats,
        'recording': is_recording
    })


@app.route('/get_report', methods=['GET'])
def get_report():
    """Get current session report"""
    if not analytics.session_active and analytics.start_time:
        report = analytics.generate_report()
        return jsonify(report)
    else:
        return jsonify({
            'status': 'error',
            'message': 'No completed session available'
        })


def process_audio():
    """Process audio in background thread"""
    global is_recording, speech_analyzer, audio_capture, audio_lock
    
    print("Audio processing thread started")
    
    while True:
        if not is_recording or not audio_capture or not speech_analyzer:
            time.sleep(0.5)
            continue
        
        try:
            # Get 3-second audio chunk
            audio_chunk = audio_capture.get_audio_chunk(duration=3.0)
            
            if audio_chunk is not None and len(audio_chunk) > 0:
                # Analyze audio
                result = speech_analyzer.analyze_audio_chunk(audio_chunk)
                
                # Store result in analytics
                if result.get('is_speech', False):
                    with audio_lock:
                        analytics.add_speech_data({
                            'timestamp': datetime.now().isoformat(),
                            **result
                        })
                    
                    # Print occasional updates
                    if hasattr(speech_analyzer, '_sample_count'):
                        speech_analyzer._sample_count += 1
                    else:
                        speech_analyzer._sample_count = 1
                    
                    if speech_analyzer._sample_count % 5 == 0:
                        print(f"Speech: {result['emotion']} | "
                              f"Confidence: {result['confidence']:.2f} | "
                              f"Clarity: {result['clarity_score']:.0f}%")
            
            time.sleep(2.0)  # Slight overlap for continuity
            
        except Exception as e:
            print(f"Error in audio processing: {e}")
            time.sleep(1.0)


if __name__ == '__main__':
    # Start frame processing thread
    thread = threading.Thread(target=process_frame, daemon=True)
    thread.start()
    
    print("=" * 60)
    print("AI Interview Analyzer Starting...")
    print("=" * 60)
    print("\nAccess the application at: http://localhost:5000")
    print("\nPress CTRL+C to stop the server\n")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
