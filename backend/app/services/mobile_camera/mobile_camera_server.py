"""
Mobile Camera Server for UrbanFlow
Flask-based server with WebSocket support for real-time camera streaming
"""

from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import json
import time
from datetime import datetime
from threading import Thread, Lock
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.services.vision.signal_detector import SignalDetector
from app.services.vision.vehicle_detector import VehicleDetector
from app.services.vision.data_processor import DataProcessor
from app.services.vision.camera_stream import MobileCamera

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.config['SECRET_KEY'] = 'urbanflow-camera-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global components
camera = MobileCamera()
signal_detector = SignalDetector()
vehicle_detector = VehicleDetector()
data_processor = DataProcessor()

# State
processing_lock = Lock()
is_processing = False
latest_results = {}
frame_count = 0
start_time = time.time()

# Data collection
collected_data = []
is_collecting = False


# ============= HTML TEMPLATES =============

CAMERA_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>UrbanFlow Camera</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            padding: 15px 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 24px;
            font-weight: 700;
        }
        .header p {
            font-size: 12px;
            opacity: 0.8;
        }
        .camera-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            position: relative;
        }
        #videoElement {
            width: 100%;
            max-width: 640px;
            border-radius: 12px;
            border: 2px solid #334155;
            background: #1e293b;
        }
        #canvasElement {
            display: none;
        }
        .status-bar {
            display: flex;
            gap: 15px;
            margin-top: 15px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .status-item {
            background: #1e293b;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-dot.connected { background: #22c55e; }
        .status-dot.disconnected { background: #ef4444; }
        .status-dot.streaming { background: #3b82f6; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .btn {
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, opacity 0.2s;
        }
        .btn:active { transform: scale(0.95); }
        .btn-primary { background: #3b82f6; color: white; }
        .btn-success { background: #22c55e; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .results {
            width: 100%;
            max-width: 640px;
            margin-top: 20px;
            background: #1e293b;
            border-radius: 12px;
            padding: 15px;
            border: 1px solid #334155;
        }
        .results h3 {
            font-size: 16px;
            margin-bottom: 10px;
            color: #94a3b8;
        }
        .result-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #334155;
            font-size: 14px;
        }
        .result-item:last-child { border-bottom: none; }
        .signal-indicator {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-left: 10px;
            box-shadow: 0 0 10px currentColor;
        }
        .signal-red { background: #ef4444; color: #ef4444; }
        .signal-yellow { background: #fbbf24; color: #fbbf24; }
        .signal-green { background: #22c55e; color: #22c55e; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📷 UrbanFlow Camera</h1>
        <p>Real-time Traffic Data Collection</p>
    </div>
    
    <div class="camera-container">
        <video id="videoElement" autoplay playsinline></video>
        <canvas id="canvasElement"></canvas>
        
        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot" id="connectionDot"></span>
                <span id="connectionStatus">Connecting...</span>
            </div>
            <div class="status-item">
                <span class="status-dot streaming" id="streamingDot"></span>
                <span id="streamingStatus">Waiting</span>
            </div>
            <div class="status-item">
                <span>📊 FPS:</span>
                <span id="fpsCounter">0</span>
            </div>
            <div class="status-item">
                <span>📦 Frames:</span>
                <span id="frameCounter">0</span>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn btn-success" id="startBtn" onclick="startCamera()">
                ▶ Start Camera
            </button>
            <button class="btn btn-danger" id="stopBtn" onclick="stopCamera()" disabled>
                ⏹ Stop
            </button>
            <button class="btn btn-primary" id="switchBtn" onclick="switchCamera()">
                🔄 Switch Camera
            </button>
        </div>
        
        <div class="results" id="resultsPanel">
            <h3>🔍 Detection Results</h3>
            <div class="result-item">
                <span>Signal State:</span>
                <span id="signalState">-<span class="signal-indicator" id="signalIndicator"></span></span>
            </div>
            <div class="result-item">
                <span>Phase Duration:</span>
                <span id="phaseDuration">-</span>
            </div>
            <div class="result-item">
                <span>Total Vehicles:</span>
                <span id="totalVehicles">-</span>
            </div>
            <div class="result-item">
                <span>Queue Length:</span>
                <span id="queueLength">-</span>
            </div>
            <div class="result-item">
                <span>Avg Speed:</span>
                <span id="avgSpeed">-</span>
            </div>
        </div>
    </div>

    <script>
        const video = document.getElementById('videoElement');
        const canvas = document.getElementById('canvasElement');
        const ctx = canvas.getContext('2d');
        
        let socket = null;
        let stream = null;
        let isStreaming = false;
        let frameInterval = null;
        let frameCount = 0;
        let lastFpsTime = Date.now();
        let fps = 0;
        let facingMode = 'environment'; // Start with back camera
        
        // Connect to server
        function connectSocket() {
            socket = io(window.location.origin);
            
            socket.on('connect', () => {
                document.getElementById('connectionDot').classList.add('connected');
                document.getElementById('connectionDot').classList.remove('disconnected');
                document.getElementById('connectionStatus').textContent = 'Connected';
                console.log('✅ Connected to server');
            });
            
            socket.on('disconnect', () => {
                document.getElementById('connectionDot').classList.remove('connected');
                document.getElementById('connectionDot').classList.add('disconnected');
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                console.log('❌ Disconnected from server');
            });
            
            socket.on('detection_result', (data) => {
                updateResults(data);
            });
            
            socket.on('error', (data) => {
                console.error('Server error:', data);
            });
        }
        
        // Start camera
        async function startCamera() {
            try {
                const constraints = {
                    video: {
                        facingMode: facingMode,
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    },
                    audio: false
                };
                
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = stream;
                
                video.onloadedmetadata = () => {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    startStreaming();
                };
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                
            } catch (err) {
                console.error('Camera error:', err);
                alert('Failed to access camera. Please grant permission.');
            }
        }
        
        // Stop camera
        function stopCamera() {
            stopStreaming();
            
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            
            video.srcObject = null;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }
        
        // Switch camera
        async function switchCamera() {
            facingMode = facingMode === 'environment' ? 'user' : 'environment';
            if (stream) {
                stopCamera();
                setTimeout(startCamera, 500);
            }
        }
        
        // Start streaming frames
        function startStreaming() {
            if (isStreaming) return;
            isStreaming = true;
            
            document.getElementById('streamingStatus').textContent = 'Streaming';
            document.getElementById('streamingDot').style.background = '#22c55e';
            
            // Send frames at ~5 FPS
            frameInterval = setInterval(captureAndSend, 200);
        }
        
        // Stop streaming
        function stopStreaming() {
            isStreaming = false;
            if (frameInterval) {
                clearInterval(frameInterval);
                frameInterval = null;
            }
            document.getElementById('streamingStatus').textContent = 'Stopped';
            document.getElementById('streamingDot').style.background = '#ef4444';
        }
        
        // Capture and send frame
        function captureAndSend() {
            if (!isStreaming || !video.videoWidth) return;
            
            ctx.drawImage(video, 0, 0);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
            const base64 = dataUrl.split(',')[1];
            
            socket.emit('frame', { image: base64 });
            
            frameCount++;
            document.getElementById('frameCounter').textContent = frameCount;
            
            // Calculate FPS
            const now = Date.now();
            if (now - lastFpsTime >= 1000) {
                fps = Math.round(frameCount / ((now - lastFpsTime) / 1000));
                document.getElementById('fpsCounter').textContent = fps;
                frameCount = 0;
                lastFpsTime = now;
            }
        }
        
        // Update results display
        function updateResults(data) {
            if (data.signal) {
                const signal = data.signal;
                document.getElementById('signalState').innerHTML = 
                    signal.state ? signal.state.toUpperCase() : '-';
                
                const indicator = document.getElementById('signalIndicator');
                indicator.className = 'signal-indicator';
                if (signal.state) {
                    indicator.classList.add('signal-' + signal.state);
                }
                
                document.getElementById('phaseDuration').textContent = 
                    signal.duration ? signal.duration.toFixed(1) + 's' : '-';
            }
            
            if (data.vehicles) {
                document.getElementById('totalVehicles').textContent = 
                    data.vehicles.total || 0;
                document.getElementById('queueLength').textContent = 
                    data.vehicles.queue || 0;
                document.getElementById('avgSpeed').textContent = 
                    data.vehicles.speed ? data.vehicles.speed.toFixed(1) + ' m/s' : '-';
            }
        }
        
        // Initialize on load
        connectSocket();
    </script>
</body>
</html>
'''


# ============= ROUTES =============

@app.route('/')
def index():
    """Serve the camera interface."""
    return CAMERA_HTML


@app.route('/dashboard')
def dashboard():
    """Serve the monitoring dashboard."""
    return render_template('dashboard.html')


@app.route('/api/status')
def api_status():
    """Get server status."""
    global frame_count, start_time
    
    uptime = time.time() - start_time
    
    return jsonify({
        'status': 'running',
        'uptime': round(uptime, 1),
        'frame_count': frame_count,
        'avg_fps': round(frame_count / max(uptime, 1), 1),
        'is_processing': is_processing,
        'is_collecting': is_collecting,
        'collected_samples': len(collected_data),
        'camera_stats': camera.get_stats(),
        'detector_stats': {
            'signal_detections': len(signal_detector.state_history),
            'vehicle_detections': len(vehicle_detector.detection_history)
        }
    })


@app.route('/api/latest')
def api_latest():
    """Get latest detection results."""
    return jsonify(latest_results)


@app.route('/api/collect/start', methods=['POST'])
def start_collection():
    """Start data collection."""
    global is_collecting, collected_data
    is_collecting = True
    collected_data = []
    return jsonify({'status': 'started'})


@app.route('/api/collect/stop', methods=['POST'])
def stop_collection():
    """Stop data collection."""
    global is_collecting
    is_collecting = False
    return jsonify({
        'status': 'stopped',
        'samples': len(collected_data)
    })


@app.route('/api/collect/export', methods=['GET'])
def export_collection():
    """Export collected data as JSON."""
    return jsonify({
        'export_time': datetime.now().isoformat(),
        'num_samples': len(collected_data),
        'data': collected_data
    })


@app.route('/api/rl_state')
def api_rl_state():
    """Get current state in RL format."""
    state = data_processor.to_rl_state()
    reward = data_processor.calculate_reward()
    
    return jsonify({
        'state': state.tolist(),
        'reward': reward,
        'timestamp': datetime.now().isoformat()
    })


# ============= WEBSOCKET EVENTS =============

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"[MOBILE] Client connected: {request.sid}")
    camera.on_connect({'sid': request.sid, 'time': datetime.now().isoformat()})
    emit('status', {'connected': True})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"[MOBILE] Client disconnected: {request.sid}")
    camera.on_disconnect()


@socketio.on('frame')
def handle_frame(data):
    """Process incoming frame from mobile camera."""
    global frame_count, is_processing, latest_results
    
    if is_processing:
        return
    
    try:
        with processing_lock:
            is_processing = True
            
            # Decode frame
            base64_data = data.get('image', '')
            if not base64_data:
                return
            
            img_data = base64.b64decode(base64_data)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return
            
            frame_count += 1
            
            # Run detections
            signal_result = signal_detector.detect(frame)
            vehicle_result = vehicle_detector.detect(frame)
            
            # Process data
            processed = data_processor.process(signal_result, vehicle_result)
            
            # Build response
            latest_results = {
                'timestamp': datetime.now().isoformat(),
                'frame': frame_count,
                'signal': {
                    'state': signal_result.get('signal_state'),
                    'duration': signal_result.get('phase_duration'),
                    'confidence': signal_result.get('confidence')
                },
                'vehicles': {
                    'total': vehicle_result.get('total_vehicles', 0),
                    'queue': sum(l.get('queue_length', 0) for l in vehicle_result.get('lanes', {}).values()),
                    'speed': processed.get('metrics', {}).get('average_speed', 0)
                },
                'metrics': processed.get('metrics', {})
            }
            
            # Collect data if enabled
            if is_collecting:
                sample = data_processor.to_training_sample()
                sample['reward'] = data_processor.calculate_reward()
                collected_data.append(sample)
            
            # Send results back to client
            emit('detection_result', latest_results)
            
    except Exception as e:
        print(f"[ERROR] Frame processing error: {e}")
        emit('error', {'message': str(e)})
        
    finally:
        is_processing = False


# ============= MAIN =============

def get_local_ip():
    """Get local IP address for display."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


if __name__ == '__main__':
    ip = get_local_ip()
    port = 5000
    
    print("\n" + "="*60)
    print("[START] UrbanFlow Mobile Camera Server")
    print("="*60)
    print(f"\n[MOBILE] Open this URL on your phone:")
    print(f"   http://{ip}:{port}")
    print(f"\n[LOCAL] Local access:")
    print(f"   http://localhost:{port}")
    print(f"\n[API] API Status:")
    print(f"   http://{ip}:{port}/api/status")
    print(f"\n[RL] RL State:")
    print(f"   http://{ip}:{port}/api/rl_state")
    print("\n" + "="*60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

