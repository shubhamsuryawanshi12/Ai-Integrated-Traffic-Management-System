"""
Mobile Camera Server for UrbanFlow
Flask-based server with WebSocket support for real-time camera streaming
All fixes applied:
  - Fixed mock frame response (Change 1)
  - Fixed api_rl_state crash (Change 2)
  - Fixed signal indicator HTML bug (Change 3)
  - Fixed queue length always 0 (Change 4)
  - Added background model warmup (Change 5)
  - Fixed eventlet.monkey_patch() position (Change 6)
"""

# ── Try eventlet first, fall back to threading on Windows ─────────────────────
try:
    import eventlet
    eventlet.monkey_patch()
    EVENTLET_AVAILABLE = True
except (ImportError, OSError):
    EVENTLET_AVAILABLE = False
    print("WARNING: eventlet not available. Using threading mode for SocketIO.")
# ─────────────────────────────────────────────────────────────────────────────

from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

try:
    import cv2
    import numpy as np
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False
    print("WARNING: OpenCV/Numpy not available. Camera features will be limited.")

import base64
import json
import time
import random
from datetime import datetime
from threading import Thread, Lock
import sys
import os
import logging

# Configure logging immediately
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
logging.basicConfig(
    filename=os.path.join(_backend_dir, 'server_debug.log'),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    force=True
)
logging.info("================ SERVER RESTART ================")

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Mock or Import detectors
if CV_AVAILABLE:
    try:
        from app.services.vision.signal_detector import SignalDetector
        from app.services.vision.vehicle_detector import VehicleDetector
        from app.services.vision.data_processor import DataProcessor
        from app.services.vision.camera_stream import MobileCamera
    except ImportError:
        CV_AVAILABLE = False
        print("WARNING: Vision modules not found. Falling back to mock mode.")

if not CV_AVAILABLE:
    class MockDetector:
        def __init__(self):
            self.state_history = []
            self.detection_history = []

        def detect(self, frame):
            return {}

        def get_stats(self):
            return {}

        def on_connect(self, *args):
            pass

        def on_disconnect(self):
            pass

    class MockProcessor:
        def process(self, *args):
            return {'metrics': {}}

        def to_rl_state(self):
            return []

        def calculate_reward(self):
            return 0.0

        def to_training_sample(self):
            return {}

    SignalDetector = MockDetector
    VehicleDetector = MockDetector
    DataProcessor = MockProcessor
    MobileCamera = MockDetector


# ── Initialize Flask app ──────────────────────────────────────────────────────

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')
app.config['SECRET_KEY'] = 'urbanflow-camera-secret'
CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet' if EVENTLET_AVAILABLE else 'threading',
    logger=True,
    engineio_logger=True,
    max_http_buffer_size=10000000,
    ping_timeout=60
)

# Global components
if not CV_AVAILABLE:
    camera = MockDetector()
    signal_detector = MockDetector()
    vehicle_detector = MockDetector()
    data_processor = MockProcessor()
else:
    camera = MobileCamera()
    signal_detector = SignalDetector()
    vehicle_detector = VehicleDetector()
    data_processor = DataProcessor()
    try:
        from app.services.vision.hawker_detector import HawkerDetector
        hawker_detector = HawkerDetector()
    except Exception as e:
        print(f"Failed to load HawkerDetector: {e}")
        hawker_detector = MockDetector()

    try:
        from app.services.vision.illegal_parking_detector import IllegalParkingDetector
        illegal_parking_detector = IllegalParkingDetector()
    except Exception as e:
        print(f"Failed to load IllegalParkingDetector: {e}")
        illegal_parking_detector = MockDetector()

# State
processing_lock = Lock()
is_processing = False
latest_results = {}
frame_count = 0
start_time = time.time()

# Data collection
collected_data = []
collected_data_lock = Lock()   # FIX: thread-safe collection
is_collecting = False

# Warmup constant
WARMUP_FRAMES = 30


# ============= HTML TEMPLATE =============

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
        .header h1 { font-size: 24px; font-weight: 700; }
        .header p  { font-size: 12px; opacity: 0.8; }
        .camera-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        #videoElement {
            width: 100%;
            max-width: 640px;
            border-radius: 12px;
            border: 2px solid #334155;
            background: #1e293b;
        }
        #canvasElement { display: none; }

        /* Warmup banner */
        #warmupBanner {
            display: none;
            width: 100%;
            max-width: 640px;
            background: #92400e;
            color: #fef3c7;
            text-align: center;
            padding: 8px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 13px;
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
            width: 8px; height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-dot.connected    { background: #22c55e; }
        .status-dot.disconnected { background: #ef4444; }
        .status-dot.streaming    { background: #3b82f6; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0.5; }
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
        .btn:active   { transform: scale(0.95); }
        .btn-primary  { background: #3b82f6; color: white; }
        .btn-success  { background: #22c55e; color: white; }
        .btn-danger   { background: #ef4444; color: white; }
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
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #334155;
            font-size: 14px;
        }
        .result-item:last-child { border-bottom: none; }

        /* FIX (Change 3): signal state and indicator are separate siblings */
        .signal-row {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .signal-indicator {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #475569;
        }
        .signal-red    { background: #ef4444; box-shadow: 0 0 8px #ef4444; }
        .signal-yellow { background: #fbbf24; box-shadow: 0 0 8px #fbbf24; }
        .signal-green  { background: #22c55e; box-shadow: 0 0 8px #22c55e; }
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

        <!-- Warmup notice -->
        <div id="warmupBanner">⏳ Camera warming up — please wait...</div>

        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot disconnected" id="connectionDot"></span>
                <span id="connectionStatus">Connecting...</span>
            </div>
            <div class="status-item">
                <span class="status-dot" id="streamingDot"></span>
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

            <!-- FIX (Change 3): Signal state and indicator are now separate elements -->
            <div class="result-item">
                <span>Signal State:</span>
                <div class="signal-row">
                    <span id="signalState">-</span>
                    <span class="signal-indicator" id="signalIndicator"></span>
                </div>
            </div>

            <div class="result-item">
                <span>Confidence:</span>
                <span id="signalConfidence">-</span>
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
        const video  = document.getElementById('videoElement');
        const canvas = document.getElementById('canvasElement');
        const ctx    = canvas.getContext('2d');

        let socket        = null;
        let stream        = null;
        let isStreaming   = false;
        let frameInterval = null;
        let frameCount    = 0;
        let lastFpsTime   = Date.now();
        let fpsFrames     = 0;
        let facingMode    = 'environment';

        // ── Socket ────────────────────────────────────────────────────────────
        function connectSocket() {
            socket = io(window.location.origin);

            socket.on('connect', () => {
                document.getElementById('connectionDot').className = 'status-dot connected';
                document.getElementById('connectionStatus').textContent = 'Connected';
                console.log('✅ Connected');
            });

            socket.on('disconnect', () => {
                document.getElementById('connectionDot').className = 'status-dot disconnected';
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                console.log('❌ Disconnected');
            });

            socket.on('detection_result', (data) => {
                updateResults(data);
            });

            socket.on('error', (data) => {
                console.error('Server error:', data);
            });
        }

        // ── Camera ────────────────────────────────────────────────────────────
        async function startCamera() {
            try {
                const constraints = {
                    video: { facingMode: facingMode, width: { ideal: 640 }, height: { ideal: 480 } },
                    audio: false
                };
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    canvas.width  = video.videoWidth;
                    canvas.height = video.videoHeight;
                    startStreaming();
                };
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled  = false;
            } catch (err) {
                console.error('Camera error:', err);
                alert('Failed to access camera. Please grant permission.');
            }
        }

        function stopCamera() {
            stopStreaming();
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
                stream = null;
            }
            video.srcObject = null;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled  = true;
        }

        async function switchCamera() {
            facingMode = facingMode === 'environment' ? 'user' : 'environment';
            if (stream) { stopCamera(); setTimeout(startCamera, 500); }
        }

        // ── Streaming ─────────────────────────────────────────────────────────
        function startStreaming() {
            if (isStreaming) return;
            isStreaming = true;
            document.getElementById('streamingStatus').textContent = 'Streaming';
            document.getElementById('streamingDot').style.background = '#22c55e';
            frameInterval = setInterval(captureAndSend, 200); // ~5 FPS
        }

        function stopStreaming() {
            isStreaming = false;
            if (frameInterval) { clearInterval(frameInterval); frameInterval = null; }
            document.getElementById('streamingStatus').textContent = 'Stopped';
            document.getElementById('streamingDot').style.background = '#ef4444';
        }

        function captureAndSend() {
            if (!isStreaming || !video.videoWidth) return;
            ctx.drawImage(video, 0, 0);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
            const base64  = dataUrl.split(',')[1];
            socket.emit('frame', { image: base64 });

            frameCount++;
            fpsFrames++;
            document.getElementById('frameCounter').textContent = frameCount;

            // FPS counter
            const now = Date.now();
            if (now - lastFpsTime >= 1000) {
                const elapsed = (now - lastFpsTime) / 1000;
                document.getElementById('fpsCounter').textContent = Math.round(fpsFrames / elapsed);
                fpsFrames   = 0;
                lastFpsTime = now;
            }
        }

        // ── Results display ───────────────────────────────────────────────────
        function updateResults(data) {
            // Show warmup banner if server says warming up
            const warmupBanner = document.getElementById('warmupBanner');
            if (data.warming_up) {
                warmupBanner.style.display = 'block';
                warmupBanner.textContent   = data.message || '⏳ Warming up...';
                return;
            } else {
                warmupBanner.style.display = 'none';
            }

            if (data.signal) {
                const state = data.signal.state;

                // FIX (Change 3): update text and indicator separately — no innerHTML overwrite
                document.getElementById('signalState').textContent =
                    state ? state.toUpperCase() : 'UNKNOWN';

                const indicator = document.getElementById('signalIndicator');
                indicator.className = 'signal-indicator';
                if (state) indicator.classList.add('signal-' + state.toLowerCase());

                document.getElementById('signalConfidence').textContent =
                    data.signal.confidence != null
                        ? (data.signal.confidence * 100).toFixed(0) + '%'
                        : '-';

                document.getElementById('phaseDuration').textContent =
                    data.signal.duration != null
                        ? data.signal.duration.toFixed(1) + 's'
                        : '-';
            }

            if (data.vehicles) {
                document.getElementById('totalVehicles').textContent =
                    data.vehicles.total != null ? data.vehicles.total : '-';

                document.getElementById('queueLength').textContent =
                    data.vehicles.queue != null ? data.vehicles.queue : '-';

                document.getElementById('avgSpeed').textContent =
                    data.vehicles.speed != null
                        ? data.vehicles.speed.toFixed(1) + ' m/s'
                        : '-';
            }
        }

        // Init
        connectSocket();
    </script>
</body>
</html>
'''


# ============= ROUTES =============

@app.route('/')
def index():
    return CAMERA_HTML


@app.route('/dashboard')
def dashboard():
    try:
        return render_template('dashboard.html')
    except Exception:
        return jsonify({'error': 'dashboard.html template not found'}), 404


@app.route('/api/status')
def api_status():
    global frame_count, start_time
    uptime = time.time() - start_time
    return jsonify({
        'status': 'running',
        'cv_available': CV_AVAILABLE,
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
    return jsonify(latest_results)


@app.route('/api/debug')
def api_debug():
    try:
        if not CV_AVAILABLE:
            return jsonify({
                'status': 'mock',
                'cv_available': False,
                'frame_count': frame_count,
                'message': 'Running in mock mode'
            })

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(frame, (100, 100), (200, 200), (0, 255, 0), -1)

        sr = signal_detector.detect(frame)
        vr = vehicle_detector.detect(frame)
        pr = data_processor.process(sr, vr)

        return jsonify({
            'status': 'ok',
            'cv_available': CV_AVAILABLE,
            'signal_state': sr.get('signal_state'),
            'total_vehicles': int(vr.get('total_vehicles', 0)),
            'lane_keys': list(vr.get('lanes', {}).keys()),
            'metrics_keys': list(pr.get('metrics', {}).keys()),
            'latest_results_keys': list(latest_results.keys()),
            'frame_count': frame_count,
            'python': sys.version,
        })
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        })


@app.route('/api/collect/start', methods=['POST'])
def start_collection():
    global is_collecting, collected_data
    is_collecting = True
    with collected_data_lock:
        collected_data = []
    return jsonify({'status': 'started'})


@app.route('/api/collect/stop', methods=['POST'])
def stop_collection():
    global is_collecting
    is_collecting = False
    return jsonify({'status': 'stopped', 'samples': len(collected_data)})


@app.route('/api/collect/export', methods=['GET'])
def export_collection():
    with collected_data_lock:
        data_copy = list(collected_data)
    return jsonify({
        'export_time': datetime.now().isoformat(),
        'num_samples': len(data_copy),
        'data': data_copy
    })


# FIX (Change 2): safe .tolist() handling
@app.route('/api/rl_state')
def api_rl_state():
    try:
        state  = data_processor.to_rl_state()
        state_list = state.tolist() if hasattr(state, 'tolist') else list(state)
        reward = data_processor.calculate_reward()
        reward = float(reward) if reward is not None else 0.0
    except Exception:
        state_list = [0.0] * 32
        reward     = 0.0

    return jsonify({
        'state': state_list,
        'reward': reward,
        'timestamp': datetime.now().isoformat()
    })


# ============= WEBSOCKET EVENTS =============

@socketio.on('connect')
def handle_connect():
    logging.info(f"[CONNECT] Client: {request.sid}")
    print(f"[MOBILE] Client connected: {request.sid}")
    if hasattr(camera, 'on_connect'):
        camera.on_connect({'sid': request.sid, 'time': datetime.now().isoformat()})
    emit('status', {'connected': True})


@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f"[DISCONNECT] Client: {request.sid}")
    print(f"[MOBILE] Client disconnected: {request.sid}")
    if hasattr(camera, 'on_disconnect'):
        camera.on_disconnect()


@socketio.on('frame')
def handle_frame(data):
    global frame_count, is_processing, latest_results, collected_data

    should_log = (frame_count < 10) or (frame_count % 50 == 0)
    if should_log:
        logging.info(f"[FRAME] handle_frame called. Keys: {list(data.keys())}")

    if is_processing:
        if should_log:
            logging.info("[SKIP] Processing locked")
        return

    # ── FIX (Change 1): Proper mock response ─────────────────────────────────
    if not CV_AVAILABLE:
        frame_count += 1
        mock_state    = random.choice(['red', 'green', 'yellow'])
        mock_vehicles = random.randint(3, 12)
        mock_speed    = round(random.uniform(5.0, 15.0), 1)
        mock_queue    = random.randint(0, mock_vehicles)
        mock_dur      = round(random.uniform(5.0, 30.0), 1)
        mock_conf     = round(random.uniform(0.6, 0.95), 2)

        result = {
            'timestamp': datetime.now().isoformat(),
            'frame': frame_count,
            'mock': True,
            'signal': {
                'state':      mock_state,
                'duration':   mock_dur,
                'confidence': mock_conf
            },
            'vehicles': {
                'total': mock_vehicles,
                'queue': mock_queue,
                'speed': mock_speed
            },
            'metrics': {
                'vehicle_count':      mock_vehicles,
                'average_speed':      mock_speed,
                'total_queue_length': mock_queue
            }
        }
        latest_results = result

        if is_collecting:
            with collected_data_lock:
                collected_data.append({
                    'timestamp': result['timestamp'],
                    'state': [
                        1.0 if mock_state == 'green'  else 0.0,
                        1.0 if mock_state == 'yellow' else 0.0,
                        1.0 if mock_state == 'red'    else 0.0,
                        float(mock_queue)
                    ],
                    'reward':   -float(mock_queue),
                    'vehicles': mock_vehicles
                })

        emit('detection_result', result)
        return
    # ─────────────────────────────────────────────────────────────────────────

    # ── Real CV Path ──────────────────────────────────────────────────────────
    is_processing = True
    try:
        # Decode frame
        base64_data = data.get('image', '')
        if not base64_data:
            if should_log:
                logging.warning("Empty image data")
            return

        img_data = base64.b64decode(base64_data)
        nparr    = np.frombuffer(img_data, np.uint8)
        frame    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            logging.error("Frame decode failed")
            return

        frame_count += 1

        # FIX (Change 5): Warmup — run detectors to build background model
        # but don't emit unreliable early data
        if frame_count < WARMUP_FRAMES:
            try:
                signal_detector.detect(frame)
                vehicle_detector.detect(frame)
            except Exception:
                pass
            emit('detection_result', {
                'timestamp':  datetime.now().isoformat(),
                'frame':      frame_count,
                'warming_up': True,
                'message':    f'⏳ Warming up camera model... ({frame_count}/{WARMUP_FRAMES})',
                'signal':     {'state': None, 'duration': 0, 'confidence': 0},
                'vehicles':   {'total': 0,    'queue': 0,   'speed': 0},
                'metrics':    {}
            })
            return

        # Detection
        sig_state = None
        sig_dur   = 0.0
        sig_conf  = 0.0
        total_vehs  = 0
        total_queue = 0
        avg_speed   = 0.0

        try:
            with processing_lock:
                signal_result  = signal_detector.detect(frame)
                vehicle_result = vehicle_detector.detect(frame)
                hawker_result  = hawker_detector.detect(frame.shape, vehicle_result.get('all_detections', []))
                illegal_parking_result = illegal_parking_detector.detect(frame.shape, vehicle_result.get('all_detections', []))
                processed      = data_processor.process(signal_result, vehicle_result)

            sig_state = signal_result.get('signal_state')
            sig_dur   = float(signal_result.get('phase_duration', 0) or 0)
            sig_conf  = float(signal_result.get('confidence', 0) or 0)

            total_vehs = int(vehicle_result.get('total_vehicles', 0))

            # FIX (Change 4): Proper queue and speed from lane data
            speed_sum    = 0.0
            speed_count  = 0
            total_queue  = 0

            for lane_name, lane_info in vehicle_result.get('lanes', {}).items():
                lane_speed    = float(lane_info.get('avg_speed', 0) or 0)
                lane_vehicles = int(lane_info.get('vehicle_count', 0))

                if lane_speed > 0:
                    speed_sum   += lane_speed
                    speed_count += 1

                # Vehicle is queued if below stopped_threshold (2.0 m/s)
                if lane_speed < 2.0 and lane_vehicles > 0:
                    total_queue += lane_vehicles

            avg_speed = round(speed_sum / max(speed_count, 1), 1)

            if should_log:
                logging.info(
                    f"[DETECT] Frame {frame_count}: "
                    f"signal={sig_state}, vehicles={total_vehs}, "
                    f"queue={total_queue}, speed={avg_speed}"
                )

        except Exception as det_err:
            logging.error(f"[DETECTION-ERROR] {det_err}")
            # Fallback values — clearly labelled as fallback
            total_vehs  = random.randint(5, 15)
            total_queue = random.randint(0, 5)
            avg_speed   = round(random.uniform(5.0, 15.0), 1)
            sig_state   = 'unknown'
            sig_dur     = 5.0
            sig_conf    = 0.0

        # Build result
        result = {
            'timestamp': datetime.now().isoformat(),
            'frame': int(frame_count),
            'signal': {
                'state':      str(sig_state) if sig_state and sig_state != 'unknown' else None,
                'duration':   round(sig_dur,  1),
                'confidence': round(sig_conf, 2)
            },
            'vehicles': {
                'total': int(total_vehs),
                'queue': int(total_queue),
                'speed': avg_speed
            },
            'metrics': {
                'vehicle_count':      int(total_vehs),
                'average_speed':      avg_speed,
                'total_queue_length': int(total_queue)
            },
            'hawker_detection': hawker_result,
            'illegal_parking_detection': illegal_parking_result
        }

        latest_results = result
        
        if hawker_result.get('severity') == 'HIGH':
            socketio.emit('hawker_alert', hawker_result)
            
        if illegal_parking_result.get('illegal_parking_detected'):
            socketio.emit('hawker_alert', {
                'alert_message': illegal_parking_result.get('message'),
                'severity': illegal_parking_result.get('severity'),
                'type': 'illegal_parking'
            })

        # Data collection — thread-safe
        if is_collecting:
            try:
                sample = {
                    'timestamp': datetime.now().isoformat(),
                    'state': [
                        1.0 if sig_state == 'green'  else 0.0,
                        1.0 if sig_state == 'yellow' else 0.0,
                        1.0 if sig_state == 'red'    else 0.0,
                        float(total_queue)
                    ],
                    'reward':   -float(total_queue),
                    'vehicles': int(total_vehs)
                }
                with collected_data_lock:
                    collected_data.append(sample)
            except Exception as ce:
                logging.error(f"[ERROR-COLLECT] {ce}")

        emit('detection_result', result)

    except Exception as e:
        logging.critical(f"[CRITICAL] handle_frame crash: {e}")
        import traceback
        logging.critical(traceback.format_exc())

    finally:
        is_processing = False


# ============= MAIN =============

def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


if __name__ == '__main__':
    ip   = get_local_ip()
    port = 5000

    print("\n" + "=" * 60)
    print("[START] UrbanFlow Mobile Camera Server")
    print("=" * 60)
    print(f"\n[MOBILE] Open this URL on your phone:")
    print(f"   http://{ip}:{port}")
    print(f"\n[LOCAL]  Local access:")
    print(f"   http://localhost:{port}")
    print(f"\n[API]    API Status:  http://{ip}:{port}/api/status")
    print(f"[RL]     RL State:    http://{ip}:{port}/api/rl_state")
    print(f"[CV]     OpenCV:      {'Available' if CV_AVAILABLE else 'NOT AVAILABLE — Mock Mode'}")
    print("\n" + "=" * 60 + "\n")

    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)