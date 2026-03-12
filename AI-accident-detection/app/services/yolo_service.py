from ultralytics import YOLO

class YoloService:

    def __init__(self):
        # 서버 시작시 한번만 로드
        self.model = YOLO("yolov8n.pt")

    def detect(self, image_path):

        results = self.model(image_path)

        detections = []

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()

                detections.append({
                    "class_id": cls,
                    "confidence": conf,
                    "bbox": xyxy
                })

        return detections