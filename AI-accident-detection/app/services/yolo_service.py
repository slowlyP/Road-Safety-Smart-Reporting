from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

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

    frame_count = 0
    sampled_frames = 0
    total_detections = 0
    frame_results = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # 너무 무거우니까 10프레임마다 1번만 분석
        if frame_count % 10 != 0:
            continue

        sampled_frames += 1

        results = model(frame)

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

        total_detections += len(detections)

        frame_results.append({
            "frame_no": frame_count,
            "detection_count": len(detections),
            "detections": detections
        })

    cap.release()

    return {
        "total_frames": frame_count,
        "sampled_frames": sampled_frames,
        "total_detections": total_detections,
        "frames": frame_results
    }