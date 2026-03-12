from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os

from app.services.yolo_service import detect_image, detect_video

detect_bp = Blueprint("detect", __name__, url_prefix="/detect")

UPLOAD_DIR = "storage/uploads"

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}

def get_file_ext(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

@detect_bp.route("/analyze", methods=["POST"])
def analyze_file():
    file = request.files.get("file")

    if not file or file.filename == "":
        return jsonify({"success": False, "message": "업로드 파일이 없습니다."}), 400

    ext = get_file_ext(file.filename)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, filename)
    file.save(file_path)

    try:
        if ext in IMAGE_EXTENSIONS:
            detections = detect_image(file_path)
            return jsonify({
                "success": True,
                "file_type": "image",
                "filename": filename,
                "detections": detections
            })

        elif ext in VIDEO_EXTENSIONS:
            result = detect_video(file_path)
            return jsonify({
                "success": True,
                "file_type": "video",
                "filename": filename,
                "result": result
            })

        else:
            return jsonify({
                "success": False,
                "message": "지원하지 않는 파일 형식입니다."
            }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"분석 중 오류 발생: {str(e)}"
        }), 500