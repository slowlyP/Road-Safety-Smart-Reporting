from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename

from app.services.yolo_service import YoloService

detect_bp = Blueprint("detect", __name__)

yolo_service = YoloService()

UPLOAD_DIR = "storage/uploads"

@detect_bp.route("/detect", methods=["POST"])
def detect_image():

    file = request.files.get("file")

    if not file:
        return jsonify({"error": "파일 없음"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, filename)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file.save(filepath)

    detections = yolo_service.detect(filepath)

    return jsonify({
        "detections": detections
    })