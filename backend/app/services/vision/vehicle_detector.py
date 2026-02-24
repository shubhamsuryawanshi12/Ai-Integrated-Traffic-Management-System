"""
Vehicle Detector using YOLOv8 (with Motion Detection fallback)
Fixes applied:
  - FIX 1: IoU-based vehicle tracking replaces broken sequential-ID matching
  - FIX 2: Temporal smoothing (5-frame rolling average) eliminates ghost counts
  - FIX 3: Contour solidity filter removes noise blobs that aren't vehicles
  - FIX 4: Raised min_area + tighter aspect ratio to reduce false positives
  - FIX 5: Adaptive MOG2 learning rate speeds up background recovery
  - FIX 6: Larger morphological kernels merge fragmented vehicle blobs
  - FIX 7: Non-overlapping quadrant lane assignment (no vehicle counted twice)
  - FIX 8: Speed defaults to lane avg (not 0) for untracked vehicles
  - FIX 9: get_rl_state() returns flat 32-element list matching A2C input
  - FIX 10: Replaced print() with logging throughout
"""

import cv2
import numpy as np
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import json
import time
import logging

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning(
        "[VehicleDetector] ultralytics not installed — using MOG2 fallback. "
        "Install with: pip install ultralytics"
    )


# ── IoU helpers ───────────────────────────────────────────────────────────────

def _iou(boxA: List[int], boxB: List[int]) -> float:
    """Compute Intersection over Union for two [x1,y1,x2,y2] boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter = max(0, xB - xA) * max(0, yB - yA)
    if inter == 0:
        return 0.0

    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    union = areaA + areaB - inter
    return inter / union if union > 0 else 0.0


def _match_detections(prev: Dict[int, List[int]],
                      current: List[Dict],
                      iou_threshold: float = 0.3) -> Dict[int, int]:
    """
    Match current detections to previous tracked IDs using greedy IoU matching.

    Returns:
        mapping of current detection index → persistent track ID
    """
    if not prev:
        return {}

    prev_ids   = list(prev.keys())
    prev_boxes = [prev[pid] for pid in prev_ids]

    matched = {}          # current_index → track_id
    used_prev = set()

    # Build IoU matrix
    for ci, det in enumerate(current):
        best_iou = iou_threshold
        best_pi  = -1
        for pi, pbox in enumerate(prev_boxes):
            if pi in used_prev:
                continue
            score = _iou(det['bbox'], pbox)
            if score > best_iou:
                best_iou = score
                best_pi  = pi

        if best_pi >= 0:
            matched[ci] = prev_ids[best_pi]
            used_prev.add(best_pi)

    return matched


# ─────────────────────────────────────────────────────────────────────────────

class VehicleDetector:
    """
    Detects and tracks vehicles using YOLOv8 (or MOG2 fallback).
    Provides per-lane counts, queue lengths, and speed estimates.
    """

    # COCO class IDs for vehicles
    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck',
        1: 'bicycle'
    }

    def __init__(self, model_path: str = 'yolov8n.pt', config: Optional[Dict] = None):
        """
        Args:
            model_path: Path to YOLOv8 model weights.
            config:     Optional overrides for detection parameters.
        """
        self.config     = config or {}
        self.model_path = model_path
        self.model      = None

        # ── Detection parameters ──────────────────────────────────────────────
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        self.iou_threshold        = self.config.get('iou_threshold', 0.45)
        self.img_size             = self.config.get('img_size', 640)

        # ── Lane definitions (set on first frame once frame size is known) ────
        # FIX 7: non-overlapping quadrants — each pixel belongs to exactly one lane
        self._lanes_initialised = False
        self.lanes: Dict[str, Optional[List[Tuple]]] = {
            'north': None,
            'south': None,
            'east':  None,
            'west':  None,
        }

        # ── FIX 1: IoU-based persistent tracking ─────────────────────────────
        self._next_track_id   = 0
        self._tracked_boxes: Dict[int, List[int]] = {}   # track_id → bbox
        self._tracked_centers: Dict[int, Tuple[int, int]] = {}  # track_id → center
        self.track_history    = defaultdict(lambda: deque(maxlen=30))

        # ── Speed estimation ──────────────────────────────────────────────────
        self.pixels_per_meter  = self.config.get('pixels_per_meter', 10)
        self.stopped_threshold = self.config.get('stopped_threshold', 2.0)   # m/s
        self._track_speeds: Dict[int, float] = {}   # track_id → latest speed
        self.prev_time: Optional[float] = None

        # ── FIX 2: Temporal smoothing — rolling window of raw counts ─────────
        self._SMOOTH_WINDOW         = 5
        self._raw_count_history     = deque(maxlen=self._SMOOTH_WINDOW)

        # ── FIX 5 / 6: MOG2 with tuned parameters ────────────────────────────
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=200, varThreshold=40, detectShadows=False
        )
        # Larger kernels merge fragmented blobs (FIX 6)
        self._kernel_open  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        self._kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))

        # MOG2 tuning constants
        self._MIN_AREA         = self.config.get('min_area', 1500)    # FIX 4: raised from 500
        self._MAX_AREA_RATIO   = 0.4                                   # max 40 % of frame
        self._MIN_ASPECT       = 0.4                                   # FIX 4: tighter
        self._MAX_ASPECT       = 3.0
        self._MIN_SOLIDITY     = 0.5                                   # FIX 3: solidity gate

        # ── Statistics ───────────────────────────────────────────────────────
        self.frame_count              = 0
        self.total_vehicles_detected  = 0
        self.detection_history        = deque(maxlen=100)

        self._load_model()

    # ── Model loading ─────────────────────────────────────────────────────────

    def _load_model(self):
        if not YOLO_AVAILABLE:
            logging.warning("[VehicleDetector] YOLO unavailable — MOG2 fallback active.")
            return
        try:
            self.model = YOLO(self.model_path)
            logging.info(f"[VehicleDetector] YOLOv8 loaded: {self.model_path}")
        except Exception as e:
            logging.error(f"[VehicleDetector] Model load failed: {e}")
            self.model = None

    # ── Public API ────────────────────────────────────────────────────────────

    def detect(self, frame: np.ndarray) -> Dict:
        """
        Detect vehicles in a BGR frame.

        Returns a result dict matching the UrbanFlow schema.
        """
        timestamp    = datetime.now().isoformat()
        current_time = time.time()
        self.frame_count += 1

        # Initialise non-overlapping lane quadrants on first real frame
        if not self._lanes_initialised:
            self._init_lanes(frame.shape)

        # ── Raw detections ────────────────────────────────────────────────────
        if self.model:
            raw_detections = self._run_yolo(frame)
        else:
            raw_detections = self._motion_detect(frame)

        # Filter YOLO output to vehicle classes only
        vehicles_raw = [d for d in raw_detections if d['class_id'] in self.VEHICLE_CLASSES]

        # ── FIX 1: Assign persistent track IDs via IoU matching ───────────────
        vehicles = self._assign_track_ids(vehicles_raw)

        # ── FIX 2: Temporal smoothing ─────────────────────────────────────────
        self._raw_count_history.append(len(vehicles))
        smoothed_count = int(round(
            sum(self._raw_count_history) / len(self._raw_count_history)
        ))

        # ── Speed estimation ──────────────────────────────────────────────────
        dt = (current_time - self.prev_time) if self.prev_time else None
        self._update_speeds(vehicles, dt)

        # ── Lane assignment & per-lane stats ──────────────────────────────────
        lane_data     = self._assign_to_lanes(vehicles, frame.shape)
        queue_lengths = self._calculate_queue_lengths(lane_data)

        # Build per-lane dicts
        lanes_out = {}
        for lane, vlist in lane_data.items():
            lanes_out[lane] = {
                'vehicle_count': len(vlist),
                'queue_length':  queue_lengths.get(lane, 0),
                'avg_speed':     self._avg_speed_for_lane(vlist),
                'vehicles':      vlist,
            }

        # ── Result ────────────────────────────────────────────────────────────
        result = {
            'timestamp':      timestamp,
            'frame_number':   self.frame_count,
            'total_vehicles': smoothed_count,       # smoothed, not raw
            'raw_count':      len(vehicles),        # raw for debugging
            'lanes':          lanes_out,
            'vehicle_types':  self._count_vehicle_types(vehicles),
            'all_detections': vehicles,
            'processing_fps': self._calculate_fps(current_time),
        }

        self.detection_history.append(result)
        self.total_vehicles_detected += len(vehicles)

        # Update state for next frame
        self._tracked_boxes   = {v['track_id']: v['bbox']   for v in vehicles}
        self._tracked_centers = {v['track_id']: tuple(v['center']) for v in vehicles}
        self.prev_time        = current_time

        return result

    # ── Lane initialisation ───────────────────────────────────────────────────

    def _init_lanes(self, frame_shape: Tuple):
        """
        FIX 7: Define strictly non-overlapping quadrants so no vehicle is
        counted in two lanes.

        Layout (matches documentation diagram):
          North = top-left    East  = top-right
          West  = bot-left    South = bot-right
        """
        h, w = frame_shape[:2]
        mh, mw = h // 2, w // 2

        self.lanes = {
            'north': [(0,   0),  (mw,  0),  (mw,  mh), (0,   mh)],
            'east':  [(mw,  0),  (w,   0),  (w,   mh), (mw,  mh)],
            'west':  [(0,   mh), (mw,  mh), (mw,  h),  (0,   h)],
            'south': [(mw,  mh), (w,   mh), (w,   h),  (mw,  h)],
        }
        self._lanes_initialised = True
        logging.info(f"[VehicleDetector] Lanes initialised for frame {w}×{h}")

    # ── YOLO inference ────────────────────────────────────────────────────────

    def _run_yolo(self, frame: np.ndarray) -> List[Dict]:
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.img_size,
            verbose=False,
        )
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls  = int(box.cls[0])
                detections.append({
                    'id':         i,
                    'track_id':   -1,   # assigned later
                    'class_id':   cls,
                    'class_name': self.VEHICLE_CLASSES.get(cls, 'unknown'),
                    'confidence': round(conf, 2),
                    'bbox':       [int(x1), int(y1), int(x2), int(y2)],
                    'center':     [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                })
        return detections

    # ── MOG2 motion fallback ──────────────────────────────────────────────────

    def _motion_detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Background-subtraction fallback with all ghost-detection fixes applied.
        """
        frame_area = frame.shape[0] * frame.shape[1]

        # FIX 5: faster learning rate when scene is empty (speeds background recovery)
        # We peek at prev count; if zero, learn faster
        prev_count    = self._raw_count_history[-1] if self._raw_count_history else 1
        learning_rate = 0.01 if prev_count > 0 else 0.05

        mask = self.bg_subtractor.apply(frame, learningRate=learning_rate)

        # FIX 6: larger kernels → merge fragmented blobs, fill holes
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  self._kernel_open)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self._kernel_close)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)

            # FIX 4: tighter area gate
            if area < self._MIN_AREA or area > frame_area * self._MAX_AREA_RATIO:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / max(h, 1)

            # FIX 4: tighter aspect ratio
            if not (self._MIN_ASPECT < aspect_ratio < self._MAX_ASPECT):
                continue

            # FIX 3: solidity — real vehicles produce compact blobs
            hull      = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity  = area / hull_area if hull_area > 0 else 0.0
            if solidity < self._MIN_SOLIDITY:
                continue

            detections.append({
                'id':         len(detections),
                'track_id':   -1,
                'class_id':   2,          # default: car
                'class_name': 'car',
                'confidence': round(solidity, 2),   # use solidity as proxy confidence
                'bbox':       [x, y, x + w, y + h],
                'center':     [x + w // 2, y + h // 2],
            })

        if detections:
            logging.debug(f"[MOG2] {len(detections)} candidate blobs passed filters")

        return detections

    # ── Persistent tracking ───────────────────────────────────────────────────

    def _assign_track_ids(self, vehicles: List[Dict]) -> List[Dict]:
        """
        FIX 1: Match detections to existing tracks via IoU. Unmatched
        detections receive a new unique ID.
        """
        matched = _match_detections(self._tracked_boxes, vehicles)

        result = []
        for ci, det in enumerate(vehicles):
            det = dict(det)   # copy
            if ci in matched:
                det['track_id'] = matched[ci]
            else:
                det['track_id']      = self._next_track_id
                self._next_track_id += 1
            self.track_history[det['track_id']].append(det['center'])
            result.append(det)

        return result

    # ── Speed ─────────────────────────────────────────────────────────────────

    def _update_speeds(self, vehicles: List[Dict], dt: Optional[float]):
        """Calculate per-track speed using displacement from previous frame."""
        if dt is None or dt <= 0:
            return

        for v in vehicles:
            tid = v['track_id']
            if tid in self._tracked_centers:
                prev_cx, prev_cy = self._tracked_centers[tid]
                cx,  cy          = v['center']
                dist_px = np.sqrt((cx - prev_cx) ** 2 + (cy - prev_cy) ** 2)
                dist_m  = dist_px / self.pixels_per_meter
                self._track_speeds[tid] = round(dist_m / dt, 2)

    def _speed_for_vehicle(self, vehicle: Dict, lane_vehicles: List[Dict]) -> float:
        """
        FIX 8: Return track speed if known; otherwise use lane average rather
        than defaulting to 0 (which would falsely mark vehicles as stopped).
        """
        tid   = vehicle['track_id']
        speed = self._track_speeds.get(tid)
        if speed is not None:
            return speed

        # Fallback: lane average of vehicles that do have a speed
        known = [self._track_speeds[v['track_id']]
                 for v in lane_vehicles
                 if v['track_id'] in self._track_speeds]
        if known:
            return round(sum(known) / len(known), 2)

        # If nothing is known (e.g. first frame), assume moving
        return self.stopped_threshold + 1.0

    def _avg_speed_for_lane(self, vehicles: List[Dict]) -> float:
        if not vehicles:
            return 0.0
        speeds = [self._speed_for_vehicle(v, vehicles) for v in vehicles]
        return round(sum(speeds) / len(speeds), 2)

    # ── Queue calculation ─────────────────────────────────────────────────────

    def _calculate_queue_lengths(self, lane_data: Dict[str, List]) -> Dict[str, int]:
        queue_lengths = {}
        for lane, vehicles in lane_data.items():
            stopped = sum(
                1 for v in vehicles
                if self._speed_for_vehicle(v, vehicles) < self.stopped_threshold
            )
            queue_lengths[lane] = stopped
        return queue_lengths

    # ── Lane assignment ───────────────────────────────────────────────────────

    def _assign_to_lanes(self, vehicles: List[Dict], frame_shape: Tuple) -> Dict[str, List]:
        lane_data = {lane: [] for lane in self.lanes}

        for vehicle in vehicles:
            cx, cy = vehicle['center']
            for lane_name, polygon in self.lanes.items():
                if polygon and self._point_in_polygon(cx, cy, polygon):
                    lane_data[lane_name].append(vehicle)
                    break   # non-overlapping quadrants → only one lane matches

        return lane_data

    def _point_in_polygon(self, x: int, y: int, polygon: List[Tuple]) -> bool:
        """Ray-casting point-in-polygon test."""
        n      = len(polygon)
        inside = False
        j      = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _count_vehicle_types(self, vehicles: List[Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for v in vehicles:
            counts[v['class_name']] += 1
        return dict(counts)

    def _calculate_fps(self, current_time: float) -> float:
        if self.prev_time:
            return round(1.0 / max(current_time - self.prev_time, 0.001), 1)
        return 0.0

    def get_stats(self) -> Dict:
        return {
            'frame_count':             self.frame_count,
            'total_vehicles_detected': self.total_vehicles_detected,
            'active_tracks':           len(self._tracked_boxes),
            'yolo_available':          self.model is not None,
        }

    # ── RL state (FIX 9) ──────────────────────────────────────────────────────

    def get_rl_state(self) -> Optional[List[float]]:
        """
        FIX 9: Returns a flat 32-element list matching the A2C agent's
        expected input format (4 features × 4 lanes + 16 zeros padding).
        """
        if not self.detection_history:
            return None

        latest = self.detection_history[-1]
        lanes  = latest['lanes']

        state = []
        for lane in ('north', 'east', 'west', 'south'):
            info = lanes.get(lane, {})
            state.append(float(info.get('queue_length',  0)))
            state.append(float(info.get('vehicle_count', 0)))
            state.append(float(info.get('avg_speed',     0)))
            state.append(0.0)   # phase placeholder (not available from camera alone)

        # Pad to 32
        state += [0.0] * (32 - len(state))
        return state

    # ── Visualisation ─────────────────────────────────────────────────────────

    def draw_detections(self, frame: np.ndarray, result: Dict) -> np.ndarray:
        output = frame.copy()
        colors = {
            'car':        (0, 255, 0),
            'truck':      (0, 165, 255),
            'bus':        (255, 165, 0),
            'motorcycle': (255, 0, 255),
            'bicycle':    (255, 255, 0),
        }

        for vehicle in result['all_detections']:
            x1, y1, x2, y2 = vehicle['bbox']
            color = colors.get(vehicle['class_name'], (128, 128, 128))
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            label = f"#{vehicle['track_id']} {vehicle['class_name']} {vehicle['confidence']:.0%}"
            cv2.putText(output, label, (x1, max(y1 - 10, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        # Draw lane boundaries
        for lane_name, polygon in self.lanes.items():
            if polygon:
                pts = np.array(polygon, np.int32).reshape((-1, 1, 2))
                cv2.polylines(output, [pts], True, (200, 200, 200), 1)
                cx = int(sum(p[0] for p in polygon) / len(polygon))
                cy = int(sum(p[1] for p in polygon) / len(polygon))
                cv2.putText(output, lane_name.upper(), (cx - 20, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Stats overlay
        h = frame.shape[0]
        overlay_y = h - 160
        cv2.rectangle(output, (10, overlay_y), (280, h - 10), (0, 0, 0), -1)
        cv2.rectangle(output, (10, overlay_y), (280, h - 10), (255, 255, 255), 1)

        cv2.putText(output, f"Vehicles (smoothed): {result['total_vehicles']}",
                    (20, overlay_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(output, f"Raw count: {result['raw_count']}",
                    (20, overlay_y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)
        cv2.putText(output, f"FPS: {result['processing_fps']}",
                    (20, overlay_y + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        y_off = overlay_y + 100
        for lane, data in result['lanes'].items():
            if data['vehicle_count'] > 0 and y_off < h - 15:
                text = f"{lane}: {data['vehicle_count']} veh, {data['queue_length']} stopped"
                cv2.putText(output, text, (20, y_off),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
                y_off += 18

        return output

    # ── Export ────────────────────────────────────────────────────────────────

    def export_data(self, filepath: str) -> Dict:
        data = {
            'export_time':             datetime.now().isoformat(),
            'total_frames':            self.frame_count,
            'total_vehicles_detected': self.total_vehicles_detected,
            'detection_history':       list(self.detection_history),
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logging.info(f"[VehicleDetector] Exported {len(self.detection_history)} records to {filepath}")
        except Exception as e:
            logging.error(f"[VehicleDetector] Export failed: {e}")
        return data