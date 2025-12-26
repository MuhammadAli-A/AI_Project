"""
AI Interview Analyzer - Flask Backend
Real-time facial emotion and speech emotion analysis for job interviews

Features:
- Facial Emotion Detection (FER2013 model with MediaPipe)
- Speech Emotion Recognition (Wav2Vec2 HuggingFace model)
- Multimodal Fusion for comprehensive interview scoring
"""
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import cv2
import threading
import time
from datetime import datetime
import os
import json

# Import core modules
from core.face_emotion import FaceEmotionAnalyzer
from core.speech_emotion import SpeechEmotionAnalyzer, AudioCapture
from core.fusion import MultimodalFusion

# Try to import the realtime speech emotion module (HuggingFace Wav2Vec2)
try:
    from core.realtime_speech_emotion import RealtimeSpeechEmotionRecognizer
    REALTIME_SER_AVAILABLE = True
    print("✓ Realtime Speech Emotion Recognition module available")
except ImportError as e:
    print(f"⚠ Realtime SER not available: {e}")
    REALTIME_SER_AVAILABLE = False


app = Flask(__name__)
CORS(app)

# Global variables
face_analyzer = FaceEmotionAnalyzer()
speech_analyzer = SpeechEmotionAnalyzer()
audio_capture = AudioCapture()
fusion = MultimodalFusion()
realtime_ser = None  # Realtime Speech Emotion Recognizer (Wav2Vec2)

is_recording = False
output_frame = None
frame_lock = threading.Lock()
data_lock = threading.Lock()

# Latest analysis results
latest_face_data = {}
latest_speech_data = {}


class VideoCamera:
    """Simple video camera wrapper"""
    
    def __init__(self):
        """Initialize video camera"""
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.video.set(cv2.CAP_PROP_FPS, 30)
        
    def __del__(self):
        """Release camera"""
        if self.video.isOpened():
            self.video.release()
    
    def get_frame(self):
        """Get current frame from camera"""
        success, frame = self.video.read()
        return frame if success else None


def video_processing_thread():
    """Process video frames continuously"""
    global output_frame, frame_lock, is_recording, latest_face_data
    
    camera = VideoCamera()
    
    # Check if camera opened
    if not camera.video.isOpened():
        print("⚠ Could not open camera. Video processing disabled.")
        return
    
    frame_count = 0
    print("✓ Video processing thread started")
    
    while True:
        frame = camera.get_frame()
        
        if frame is None:
            time.sleep(0.01)
            continue
        
        frame_count += 1
        
        # Analyze face every frame
        processed_frame, face_data = face_analyzer.analyze(frame)
        
        # Store latest face data
        with data_lock:
            latest_face_data = face_data
        
        # If recording, store data for fusion
        if is_recording and frame_count % 30 == 0:  # Every ~1 second
            fusion.add_face_data(face_data)
        
        # Add recording indicator
        if is_recording:
            cv2.circle(processed_frame, (20, 20), 10, (0, 0, 255), -1)
            cv2.putText(processed_frame, "REC", (40, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            # Add audio indicator
            cv2.circle(processed_frame, (20, 50), 8, (255, 0, 0), -1)
            cv2.putText(processed_frame, "AUDIO", (40, 55), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()
        
        # Update output frame
        with frame_lock:
            output_frame = frame_bytes
        
        time.sleep(0.03)  # ~30 FPS


def generate_frames():
    """Generator function for video streaming"""
    global output_frame, frame_lock
    
    while True:
        with frame_lock:
            if output_frame is None:
                time.sleep(0.01)
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


@app.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        'facial_model': face_analyzer is not None,
        'speech_model': speech_analyzer is not None or REALTIME_SER_AVAILABLE,
        'fusion_enabled': fusion is not None,
        'recording': is_recording,
        'realtime_ser_available': REALTIME_SER_AVAILABLE
    })


@app.route('/start', methods=['POST'])
@app.route('/start_recording', methods=['POST'])
def start_recording():
    """Start interview recording"""
    global is_recording, realtime_ser
    
    is_recording = True
    fusion.start_session()
    face_analyzer.reset_history()
    speech_analyzer.reset_history()
    
    # Initialize speech analyzer - prefer the realtime Wav2Vec2 module
    audio_initialized = False
    
    if REALTIME_SER_AVAILABLE:
        try:
            if realtime_ser is None:
                realtime_ser = RealtimeSpeechEmotionRecognizer()
            realtime_ser.start_session()
            audio_initialized = True
            print("✓ Realtime Speech Emotion Recognition (Wav2Vec2) initialized")
        except Exception as e:
            print(f"Warning: Could not initialize realtime SER: {e}")
            realtime_ser = None
    
    # Fallback to basic speech analyzer
    if not audio_initialized:
        try:
            audio_capture.start()
            audio_initialized = True
            print("✓ Basic speech analyzer initialized")
        except Exception as e:
            print(f"Warning: Could not start audio capture: {e}")
    
    # Start audio processing thread
    if audio_initialized:
        audio_thread = threading.Thread(target=audio_processing_thread, daemon=True)
        audio_thread.start()
        print("✓ Audio processing started")
    
    return jsonify({
        'status': 'started',
        'message': 'Recording started',
        'timestamp': datetime.now().isoformat(),
        'audio_enabled': audio_initialized,
        'using_realtime_ser': realtime_ser is not None
    })


@app.route('/stop', methods=['POST'])
@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    """Stop interview recording"""
    global is_recording, realtime_ser
    
    is_recording = False
    fusion.end_session()
    
    # Stop audio recording and get speech summary
    speech_summary = {}
    
    if realtime_ser:
        try:
            speech_summary = realtime_ser.end_session()
        except Exception as e:
            print(f"Error ending realtime SER session: {e}")
    
    try:
        audio_capture.stop()
    except:
        pass
    
    # Get face and speech statistics
    face_stats = face_analyzer.get_statistics()
    speech_stats = speech_analyzer.get_statistics()
    
    # Calculate fusion score
    fusion_score = fusion.calculate_fusion_score(face_stats, speech_stats)
    
    # Generate comprehensive report
    report = fusion.generate_report(face_stats, speech_stats)
    
    # Add speech emotion summary to report
    if speech_summary:
        report['speech_emotion_summary'] = speech_summary
    
    # Save report
    os.makedirs('reports', exist_ok=True)
    report_filename = f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path = os.path.join('reports', report_filename)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return jsonify({
        'status': 'success',
        'message': 'Recording stopped',
        'report': report,
        'report_file': report_filename,
        'speech_summary': speech_summary
    })


@app.route('/stats', methods=['GET'])
@app.route('/get_stats', methods=['GET'])
def get_stats():
    """Get current statistics"""
    global latest_face_data, latest_speech_data
    
    face_stats = face_analyzer.get_statistics()
    
    # Get speech statistics if available
    speech_stats = {}
    
    # Try realtime SER first
    if realtime_ser:
        try:
            emotion, confidence = realtime_ser.get_dominant_emotion()
            speech_stats = {
                'emotion': emotion,
                'confidence': confidence,
                'emotion_distribution': realtime_ser.get_emotion_distribution(),
                'interview_score': realtime_ser.get_interview_score()
            }
        except Exception as e:
            print(f"Error getting realtime SER stats: {e}")
    
    # Fallback to basic speech analyzer
    if not speech_stats:
        try:
            speech_stats = speech_analyzer.get_statistics()
        except Exception as e:
            print(f"Error getting speech stats: {e}")
    
    # Format response for frontend
    response = {
        'recording': is_recording,
        'using_realtime_ser': realtime_ser is not None
    }
    
    # Facial emotion data
    if face_stats:
        dominant = face_stats.get('dominant_emotion', 'neutral')
        # confidence is already normalized to 0-1 in face_emotion.py
        confidence = face_stats.get('confidence', 0)
        # Ensure confidence is in 0-1 range
        if confidence > 1:
            confidence = confidence / 100.0
        
        response['facial'] = {
            'emotion': dominant,
            'confidence': min(1.0, max(0, confidence))  # Clamp to 0-1
        }
        
        # eye_contact is already 0-1 from face_emotion.py
        eye_contact = face_stats.get('eye_contact', 0.7)
        if eye_contact > 1:
            eye_contact = eye_contact / 100.0
        response['eye_contact'] = min(1.0, max(0, eye_contact))
        
        # positivity_score is already 0-1 from face_emotion.py
        positivity = face_stats.get('positivity_score', 0.5)
        if positivity > 1:
            positivity = positivity / 100.0
        response['positivity'] = min(1.0, max(0, positivity))
        
        # overall_confidence is already 0-1 from face_emotion.py
        overall_conf = face_stats.get('overall_confidence', 0.6)
        if overall_conf > 1:
            overall_conf = overall_conf / 100.0
        response['confidence'] = min(1.0, max(0, overall_conf))
    
    # Speech emotion data
    if speech_stats:
        speech_conf = speech_stats.get('confidence', 0)
        # Normalize speech confidence to 0-1
        if speech_conf > 1:
            speech_conf = speech_conf / 100.0
        response['speech'] = {
            'emotion': speech_stats.get('emotion', 'neutral'),
            'confidence': min(1.0, max(0, speech_conf))
        }
    
    return jsonify(response)


@app.route('/report', methods=['GET'])
@app.route('/get_report', methods=['GET'])
def get_report():
    """Get current session report"""
    face_stats = face_analyzer.get_statistics()
    speech_stats = speech_analyzer.get_statistics()
    
    if face_stats or speech_stats:
        report = fusion.generate_report(face_stats, speech_stats)
        
        # Calculate facial score - positivity_score is 0-1, convert to percentage
        facial_score = 50  # default
        if face_stats:
            pos_score = face_stats.get('positivity_score', 0.5)
            # If already in 0-1 range, multiply by 100
            if pos_score <= 1:
                facial_score = pos_score * 100
            else:
                # Already a percentage, clamp it
                facial_score = min(100, max(0, pos_score))
        
        # Calculate speech score
        speech_score = 50  # default
        if speech_stats:
            sp_score = speech_stats.get('interview_score', 50)
            # Ensure it's a valid percentage
            speech_score = min(100, max(0, sp_score))
        
        # Calculate eye contact - normalize to 0-1
        eye_contact = 0.7  # default
        if face_stats:
            eye_val = face_stats.get('eye_contact', 0.7)
            if eye_val > 1:
                eye_contact = eye_val / 100.0
            else:
                eye_contact = eye_val
            eye_contact = min(1.0, max(0, eye_contact))
        
        # Get overall score from fusion report
        overall_score = report.get('scores', {}).get('overall_score', 50)
        if overall_score is None:
            overall_score = report.get('overall_score', 50)
        overall_score = min(100, max(0, overall_score))
        
        # Format for frontend
        formatted_report = {
            'facial': {
                'overall_score': facial_score,
                'emotions': face_stats.get('emotion_counts', {}) if face_stats else {}
            },
            'speech': {
                'overall_score': speech_score,
                'emotions': speech_stats.get('emotion_distribution', {}) if speech_stats else {}
            },
            'eye_contact': eye_contact,
            'overall_score': overall_score
        }
        
        return jsonify(formatted_report)
    else:
        return jsonify({
            'status': 'error',
            'message': 'No session data available',
            'facial': {'overall_score': 0, 'emotions': {}},
            'speech': {'overall_score': 0, 'emotions': {}},
            'eye_contact': 0,
            'overall_score': 0
        })


def audio_processing_thread():
    """Process audio in background thread"""
    global is_recording, realtime_ser, latest_speech_data
    
    print("Audio processing thread started")
    sample_count = 0
    
    while True:
        if not is_recording:
            time.sleep(0.5)
            continue
        
        try:
            # Use realtime SER module (Wav2Vec2 - tested and working)
            if realtime_ser:
                # Record and analyze 3-second audio chunk
                emotion, confidence = realtime_ser.record_and_predict(duration=3)
                
                if confidence > 0:
                    with data_lock:
                        latest_speech_data = {
                            'emotion': emotion,
                            'confidence': confidence,
                            'is_speech': True
                        }
                        fusion.add_speech_data(latest_speech_data)
                    
                    sample_count += 1
                    if sample_count % 3 == 0:
                        print(f"🎤 Speech Emotion: {emotion} | Confidence: {confidence:.1f}%")
                
                time.sleep(0.5)  # Brief pause between recordings
                
            # Fallback to basic speech analyzer
            else:
                audio_data = audio_capture.get_chunk(duration=3.0)
                
                if audio_data is not None and len(audio_data) > 0:
                    emotion, confidence = speech_analyzer.analyze(audio_data)
                    
                    if confidence > 0:
                        with data_lock:
                            latest_speech_data = {
                                'emotion': emotion,
                                'confidence': confidence,
                                'is_speech': True
                            }
                            fusion.add_speech_data(latest_speech_data)
                        
                        sample_count += 1
                        if sample_count % 5 == 0:
                            print(f"🎤 Speech Emotion: {emotion} | Confidence: {confidence:.1f}%")
                
                time.sleep(2.0)
            
        except Exception as e:
            print(f"Error in audio processing: {e}")
            time.sleep(1.0)


if __name__ == '__main__':
    # Start video processing thread
    video_thread = threading.Thread(target=video_processing_thread, daemon=True)
    video_thread.start()
    
    print("=" * 60)
    print("   🎯 AI INTERVIEW ANALYZER")
    print("   Real-time Facial & Speech Emotion Analysis")
    print("=" * 60)
    print("\n✓ Access the application at: http://localhost:5000")
    print("\nPress CTRL+C to stop the server\n")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
