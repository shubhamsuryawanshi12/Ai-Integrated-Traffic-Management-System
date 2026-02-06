"""
Camera Stream Handler
Manages video input from mobile cameras, webcams, or video files
"""

import cv2
import numpy as np
import base64
import threading
import queue
from datetime import datetime
from typing import Optional, Callable, Generator
import time


class CameraStream:
    """
    Handles video streaming from various sources.
    Supports: webcam, mobile phone camera (via WebRTC), IP cameras, video files.
    """
    
    def __init__(self, source: int = 0, config: Optional[dict] = None):
        """
        Initialize camera stream.
        
        Args:
            source: Camera source (0 for webcam, URL for IP camera, path for video)
            config: Optional configuration
        """
        self.source = source
        self.config = config or {}
        
        self.cap = None
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.latest_frame = None
        self.frame_count = 0
        self.fps = 0
        self.last_frame_time = None
        
        # Processing settings
        self.target_fps = self.config.get('target_fps', 10)
        self.resize_width = self.config.get('resize_width', 640)
        self.resize_height = self.config.get('resize_height', 480)
        
        # Callbacks
        self.on_frame_callback: Optional[Callable] = None
        
        # Thread control
        self.capture_thread = None
        self.lock = threading.Lock()
    
    def start(self) -> bool:
        """Start the camera stream."""
        try:
            self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                print(f"[ERROR] Failed to open camera: {self.source}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resize_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resize_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            print(f"[OK] Camera started: {self.source}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Camera error: {e}")
            return False
    
    def stop(self):
        """Stop the camera stream."""
        self.is_running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        print("[STOP] Camera stopped")
    
    def _capture_loop(self):
        """Main capture loop running in separate thread."""
        frame_interval = 1.0 / self.target_fps
        
        while self.is_running:
            start_time = time.time()
            
            ret, frame = self.cap.read()
            
            if not ret:
                print("[WARNING] Failed to read frame")
                time.sleep(0.1)
                continue
            
            # Resize if needed
            if frame.shape[1] != self.resize_width or frame.shape[0] != self.resize_height:
                frame = cv2.resize(frame, (self.resize_width, self.resize_height))
            
            # Update frame data
            with self.lock:
                self.latest_frame = frame
                self.frame_count += 1
                
                # Calculate FPS
                current_time = time.time()
                if self.last_frame_time:
                    self.fps = 1.0 / max(current_time - self.last_frame_time, 0.001)
                self.last_frame_time = current_time
            
            # Add to queue (non-blocking)
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                # Remove oldest frame
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(frame)
                except:
                    pass
            
            # Call callback if set
            if self.on_frame_callback:
                try:
                    self.on_frame_callback(frame)
                except Exception as e:
                    print(f"[WARNING] Callback error: {e}")
            
            # Maintain target FPS
            elapsed = time.time() - start_time
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame."""
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None
    
    def get_frame_blocking(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get next frame from queue (blocking)."""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def frames(self) -> Generator[np.ndarray, None, None]:
        """Generator yielding frames."""
        while self.is_running:
            frame = self.get_frame_blocking()
            if frame is not None:
                yield frame
    
    def get_jpeg(self, quality: int = 80) -> Optional[bytes]:
        """Get latest frame as JPEG bytes."""
        frame = self.get_frame()
        if frame is None:
            return None
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, buffer = cv2.imencode('.jpg', frame, encode_param)
        return buffer.tobytes()
    
    def get_base64(self, quality: int = 80) -> Optional[str]:
        """Get latest frame as base64 encoded JPEG."""
        jpeg = self.get_jpeg(quality)
        if jpeg is None:
            return None
        
        return base64.b64encode(jpeg).decode('utf-8')
    
    def set_frame_from_base64(self, base64_data: str):
        """
        Set frame from base64 encoded image (for mobile camera).
        Called by the web server when receiving frames from phone.
        """
        try:
            # Decode base64
            img_data = base64.b64decode(base64_data)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                with self.lock:
                    self.latest_frame = frame
                    self.frame_count += 1
                    
                    current_time = time.time()
                    if self.last_frame_time:
                        self.fps = 1.0 / max(current_time - self.last_frame_time, 0.001)
                    self.last_frame_time = current_time
                
                # Add to queue
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    pass
                
                # Call callback
                if self.on_frame_callback:
                    self.on_frame_callback(frame)
                
                return True
        except Exception as e:
            print(f"[WARNING] Failed to decode base64 frame: {e}")
        
        return False
    
    def get_stats(self) -> dict:
        """Get camera statistics."""
        return {
            'source': str(self.source),
            'is_running': self.is_running,
            'frame_count': self.frame_count,
            'fps': round(self.fps, 1),
            'resolution': f"{self.resize_width}x{self.resize_height}",
            'queue_size': self.frame_queue.qsize()
        }
    
    def record(self, output_path: str, duration: float = None, max_frames: int = None):
        """
        Record video to file.
        
        Args:
            output_path: Path to save video
            duration: Recording duration in seconds (optional)
            max_frames: Maximum frames to record (optional)
        """
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.target_fps,
                             (self.resize_width, self.resize_height))
        
        start_time = time.time()
        frames_recorded = 0
        
        print(f"[RECORDING] Recording started: {output_path}")
        
        try:
            for frame in self.frames():
                out.write(frame)
                frames_recorded += 1
                
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # Check frame limit
                if max_frames and frames_recorded >= max_frames:
                    break
                    
        finally:
            out.release()
            print(f"[RECORDING] Recording saved: {frames_recorded} frames")
        
        return frames_recorded


class MobileCamera(CameraStream):
    """
    Specialized camera stream for mobile phone input via WebRTC/WebSocket.
    Receives frames from phone browser.
    """
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(source='mobile', config=config)
        self.connected = False
        self.device_info = {}
    
    def start(self) -> bool:
        """Start listening for mobile frames."""
        self.is_running = True
        self.connected = False
        print("[MOBILE] Mobile camera initialized - waiting for connection...")
        return True
    
    def on_connect(self, device_info: dict):
        """Called when mobile device connects."""
        self.connected = True
        self.device_info = device_info
        print(f"[MOBILE] Mobile connected: {device_info}")
    
    def on_disconnect(self):
        """Called when mobile device disconnects."""
        self.connected = False
        print("[MOBILE] Mobile disconnected")
    
    def receive_frame(self, base64_data: str) -> bool:
        """Receive frame from mobile device."""
        if not self.is_running:
            return False
        return self.set_frame_from_base64(base64_data)
    
    def get_stats(self) -> dict:
        stats = super().get_stats()
        stats.update({
            'type': 'mobile',
            'connected': self.connected,
            'device_info': self.device_info
        })
        return stats
