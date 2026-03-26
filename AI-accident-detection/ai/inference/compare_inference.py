import os
from ultralytics import YOLO, RTDETR

# 모델 캐싱
_model_cache = {}


def load_model(model_name, model_path):
    key = f"{model_name}:{model_path}"

    if key in _model_cache:
        return _model_cache[key]

    if model_name == "RT-DETR":
        model = RTDETR(model_path)
    else:
        model = YOLO(model_path)

    _model_cache[key] = model
    return model


def run_model_inference(model_name, model_path, image_path):
    """
    model_name: YOLOv8 / RT-DETR / YOLOv8-p2
    model_path: ai/models/*.pt
    image_path: static/uploads/xxx.jpg
    """
    print("INFERENCE_MODEL:", model_name)
    print("INFERENCE_MODEL_PATH:", model_path)
    print("INFERENCE_IMAGE_PATH:", image_path)

    model = load_model(model_name, model_path)

    results = model.predict(
        source=image_path,
        conf=0.25,
        save=False,
        verbose=True
    )

    detections = []

    if not results:
        return detections

    result = results[0]

    if not hasattr(result, "boxes") or result.boxes is None:
        return detections

    names = result.names if hasattr(result, "names") else model.names

    for box in result.boxes:
        try:
            cls = int(box.cls[0]) if box.cls is not None else -1
            label = names.get(cls, f"class_{cls}")

            confidence = float(box.conf[0]) if box.conf is not None else 0.0
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            detections.append({
                "label": label,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2]
            })
        except Exception as e:
            print("BOX PARSE ERROR:", e)
            continue

    return detections