import cv2
import numpy as np
from typing import Optional
from collections import defaultdict


def compute_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0


class Tracker:
    def __init__(self, iou_threshold: float = 0.3, max_lost: int = 5):
        self.iou_threshold = iou_threshold
        self.max_lost = max_lost
        self.tracks = {}
        self.next_id = 1
        self.track_history = defaultdict(list)
        self.lost_count = defaultdict(int)

    def update(self, detections: list, frame: np.ndarray) -> list:
        if not detections:
            self._mark_all_lost()
            return self._get_active()

        if self.tracks:
            matched, unmatched_dets, unmatched_tracks = self._match(detections)

            for det_idx, track_idx in matched:
                self._update_track(track_idx, detections[det_idx])
                self.lost_count[track_idx] = 0

            for track_idx in unmatched_tracks:
                self.lost_count[track_idx] += 1

            for det_idx in unmatched_dets:
                self._create_track(detections[det_idx])
        else:
            for det in detections:
                self._create_track(det)

        expired = [tid for tid, count in self.lost_count.items() if count > self.max_lost]
        for tid in expired:
            self._remove_track(tid)

        return self._get_active()

    def _match(self, detections: list) -> tuple:
        track_ids = list(self.tracks.keys())
        track_boxes = [self.tracks[tid]["bbox"] for tid in track_ids]
        det_boxes = [d["bbox"] for d in detections]

        iou_matrix = np.zeros((len(det_boxes), len(track_boxes)))
        for i, dbox in enumerate(det_boxes):
            for j, tbox in enumerate(track_boxes):
                iou_matrix[i, j] = compute_iou(dbox, tbox)

        matched = []
        used_tracks = set()
        used_dets = set()

        flat_indices = np.argsort(iou_matrix.ravel())[::-1]
        for flat_idx in flat_indices:
            det_idx = flat_idx // len(track_boxes)
            track_idx = flat_idx % len(track_boxes)
            if det_idx in used_dets or track_idx in used_tracks:
                continue
            if iou_matrix[det_idx, track_idx] < self.iou_threshold:
                break
            matched.append((det_idx, track_idx))
            used_dets.add(det_idx)
            used_tracks.add(track_idx)

        unmatched_dets = [i for i in range(len(detections)) if i not in used_dets]
        unmatched_tracks = [i for i in range(len(track_ids)) if i not in used_tracks]
        return matched, unmatched_dets, unmatched_tracks

    def _create_track(self, detection: dict):
        tid = self.next_id
        self.next_id += 1
        self.tracks[tid] = {
            "bbox": detection["bbox"],
            "confidence": detection["confidence"],
            "class_id": detection["class_id"],
            "class_name": detection.get("class_name", "unknown"),
        }
        self.lost_count[tid] = 0
        cx = (detection["bbox"][0] + detection["bbox"][2]) / 2
        cy = (detection["bbox"][1] + detection["bbox"][3]) / 2
        self.track_history[tid].append((cx, cy))

    def _update_track(self, track_idx: int, detection: dict):
        tid = list(self.tracks.keys())[track_idx]
        self.tracks[tid]["bbox"] = detection["bbox"]
        self.tracks[tid]["confidence"] = detection["confidence"]
        self.tracks[tid]["class_id"] = detection["class_id"]
        self.tracks[tid]["class_name"] = detection.get("class_name", "unknown")
        cx = (detection["bbox"][0] + detection["bbox"][2]) / 2
        cy = (detection["bbox"][1] + detection["bbox"][3]) / 2
        self.track_history[tid].append((cx, cy))
        if len(self.track_history[tid]) > 30:
            self.track_history[tid].pop(0)

    def _remove_track(self, track_id: int):
        if track_id in self.tracks:
            del self.tracks[track_id]
        if track_id in self.lost_count:
            del self.lost_count[track_id]

    def _mark_all_lost(self):
        for tid in list(self.lost_count.keys()):
            self.lost_count[tid] += 1

    def _get_active(self) -> list:
        results = []
        for tid, data in self.tracks.items():
            if self.lost_count.get(tid, 0) <= self.max_lost:
                results.append({
                    "track_id": tid,
                    "bbox": data["bbox"],
                    "confidence": data["confidence"],
                    "class_id": data["class_id"],
                    "class_name": data["class_name"],
                })
        return results

    def get_track_history(self, track_id: int) -> list:
        return self.track_history.get(track_id, [])

    def get_direction(self, track_id: int) -> Optional[tuple]:
        history = self.get_track_history(track_id)
        if len(history) < 2:
            return None
        p1 = history[-2]
        p2 = history[-1]
        return (p2[0] - p1[0], p2[1] - p1[1])

    def reset(self):
        self.tracks.clear()
        self.track_history.clear()
        self.lost_count.clear()
        self.next_id = 1
