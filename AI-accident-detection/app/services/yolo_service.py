import os
import cv2
from ultralytics import YOLO, RTDETR

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

IMAGE_MODEL_PATH = os.path.join(BASE_DIR, "ai", "models", "best_image.pt")   # RT-DETR
VIDEO_MODEL_PATH = os.path.join(BASE_DIR, "ai", "models", "best_video.pt")   # YOLOv8

print("IMAGE_MODEL_PATH:", IMAGE_MODEL_PATH)
print("VIDEO_MODEL_PATH:", VIDEO_MODEL_PATH)

# 모델 캐싱
_model_cache = {}


def get_model(model_type):
    if model_type in _model_cache:
        return _model_cache[model_type]

    if model_type == "image":
        model = RTDETR(IMAGE_MODEL_PATH)   # 이미지 = RT-DETR
    elif model_type == "video":
        model = YOLO(VIDEO_MODEL_PATH)     # 영상 = YOLOv8
    else:
        raise ValueError(f"지원하지 않는 모델 타입입니다: {model_type}")

    _model_cache[model_type] = model
    return model


def detect_image(image_path):
    model = get_model("image")
    results = model.predict(
        source=image_path,
        conf=0.25,
        save=False,
        verbose=False
    )

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
    model = get_model("video")

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
    sample_interval = 5

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % sample_interval != 0:
            continue

        time_sec = frame_count / fps

        results = model.predict(
            source=frame,
            conf=0.25,
            imgsz=832,
            save=False,
            verbose=False
        )

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