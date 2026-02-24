
import socketio
import time
import base64
import cv2
import numpy as np

# Standard Python Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print("[CLIENT] Connected!")

@sio.event
def connect_error(data):
    print(f"[CLIENT] Connection failed: {data}")

@sio.event
def disconnect():
    print("[CLIENT] Disconnected!")

@sio.event
def detection_result(data):
    print(f"[CLIENT] Received result: {data.keys()}")

def main():
    try:
        sio.connect('http://localhost:5000')
        
        # Create a dummy black image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', img)
        b64_str = base64.b64encode(buffer).decode('utf-8')
        
        print(f"[CLIENT] Sending 10 frames...")
        for i in range(10):
            sio.emit('frame', {'image': b64_str})
            time.sleep(0.1)
            print(f"[CLIENT] Sent frame {i+1}")
            
        time.sleep(2) # Wait for acks/responses
        sio.disconnect()
        
    except Exception as e:
        print(f"[CLIENT] Error: {e}")

if __name__ == '__main__':
    main()
