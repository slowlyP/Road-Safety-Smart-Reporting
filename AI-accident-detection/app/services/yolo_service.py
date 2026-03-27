import os
from ultralytics import YOLO
import cv2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "ai", "models", "best.pt")

print("MODEL_PATH:", MODEL_PATH)

model = YOLO(MODEL_PATH)


def detect_image(image_path):
    results = model(image_path)
    detections = []

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            xyxy = box.xyxy[0].tolist()

            detections.append({
                "class_id": cls_id,
                "confidence": round(conf, 4),
                "bbox": [round(v, 2) for v in xyxy]
            })

    return detections


def detect_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("영상 파일을 열 수 없습니다.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    all_detections = []
    frame_count = 0
    sample_interval = 5  # 1이면 매 프레임, 2면 2프레임마다

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % sample_interval != 0:
            continue

        time_sec = frame_count / fps

        results = model(frame, conf=0.25, imgsz=832)

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()

                all_detections.append({
                    "class_id": cls_id,
                    "confidence": round(conf, 4),
                    "bbox": [round(v, 2) for v in xyxy],
                    "frame_no": frame_count,
                    "time_sec": round(time_sec, 2),
                    "frame_width": frame_width,
                    "frame_height": frame_height
                })

    cap.release()
    return all_detections