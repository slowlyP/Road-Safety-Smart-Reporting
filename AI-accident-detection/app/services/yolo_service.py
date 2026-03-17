from ultralytics import YOLO
import cv2

# 모델 로드 (프로젝트 루트에 yolov8n.pt가 없으면 자동 다운로드됨)
model = YOLO("yolov8n.pt")

def detect_image(image_path):
    """                       # 테스트를 위한 원본 코드 주석처리 ( 나중에 주석 제거하면됨됨)
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
    """                        #==============여기까지 테스트를 위한 원본코드 주석처리

    return [{
        "class_id": 2, # LABEL_MAP 의 2번 (tire)
        "confidence": 0.98,
        "bbox": [100, 150, 400, 500]
    }]


def detect_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("영상 파일을 열 수 없습니다.")

    all_detections = [] # [수정] 모든 프레임의 탐지 결과를 하나의 리스트로 통합
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        # 10프레임마다 샘플링
        if frame_count % 10 != 0:
            continue

        results = model(frame)

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()

                # ReportService의 for문이 바로 읽을 수 있는 구조로 추가
                all_detections.append({
                    "class_id": cls_id,
                    "confidence": round(conf, 4),
                    "bbox": [round(v, 2) for v in xyxy]
                })






    cap.release()
    return all_detections # [수정] 리스트 형태로 반환하여 Service와 호환성 맞춤