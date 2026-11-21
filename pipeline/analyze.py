"""Look at real footage and choose WHERE to cut and WHERE to frame.

best_start():  finds the steadiest, sharpest, well-lit stretch of a video (skipping the
               first/last second, where intros, logos and end screens usually are).
face_focus():  finds people's faces so the vertical crop keeps them in frame.
"""
from pathlib import Path

import cv2
import numpy as np

_face = None


def _faces(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    global _face
    if _face is None:
        _face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    h = gray.shape[0]
    found = _face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(h // 14, h // 14))
    return [tuple(map(int, f)) for f in found]


def _sample(path: Path, every: float = 0.5, width: int = 480):
    """Yield (time, small grayscale frame)."""
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, int(round(fps * every)))
    for idx in range(0, frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        small = cv2.resize(frame, (width, int(h * width / w)))
        yield idx / fps, cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    cap.release()


def duration(path: Path) -> float:
    cap = cv2.VideoCapture(str(path))
    d = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    cap.release()
    return d


def best_start(path: Path, length: float, prefer_faces: bool = True) -> float:
    """Start time of the best `length`-second stretch."""
    samples = list(_sample(path))
    if len(samples) < 3:
        return 0.0
    total = samples[-1][0]
    scores, prev = [], None
    for t, g in samples:
        sharp = min(cv2.Laplacian(g, cv2.CV_64F).var() / 300.0, 1.0)
        bright = 1.0 - min(abs(float(g.mean()) - 120) / 120, 1.0)
        motion = 0.0 if prev is None else float(np.abs(g.astype(np.int16) - prev).mean()) / 40.0
        shaky = max(0.0, motion - 0.6)  # some motion is good, whip-pans and cuts are not
        face = 0.5 if prefer_faces and _faces(g) else 0.0
        edge = 0.0 if 1.0 <= t <= total - 1.0 else -1.0  # avoid intros / end screens
        scores.append((t, sharp + bright + face - 2 * shaky + edge))
        prev = g.astype(np.int16)
    best_t, best = 0.0, -1e9
    for t, _ in scores:
        if t + length > total + 0.01 and t > 0:
            break
        window = [s for tt, s in scores if t <= tt < t + length]
        if window and (avg := sum(window) / len(window)) > best:
            best_t, best = t, avg
    return round(best_t, 2)


def face_focus(path: Path, start: float = 0.0, length: float = 3.0, image: bool = False) -> float:
    """Horizontal position (0..1) to centre the vertical crop on; 0.5 if no faces."""
    centers, weights = [], []
    if image:
        img = cv2.imread(str(path))
        if img is None:
            return 0.5
        h, w = img.shape[:2]
        g = cv2.cvtColor(cv2.resize(img, (480, int(h * 480 / w))), cv2.COLOR_BGR2GRAY)
        grays = [g]
    else:
        grays = [g for t, g in _sample(path, every=0.5) if start <= t <= start + length]
    for g in grays:
        w = g.shape[1]
        for (x, y, fw, fh) in _faces(g):
            centers.append((x + fw / 2) / w)
            weights.append(fw * fh)  # bigger (closer) faces matter more
    if not centers:
        return 0.5
    return round(float(np.average(centers, weights=weights)), 3)


def aspect(path: Path, image: bool = False) -> float:
    """Width / height of the media."""
    if image:
        img = cv2.imread(str(path))
        return img.shape[1] / img.shape[0] if img is not None else 1.0
    cap = cv2.VideoCapture(str(path))
    a = (cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 16) / (cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 9)
    cap.release()
    return a
