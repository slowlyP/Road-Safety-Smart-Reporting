import os
import uuid
import cv2
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Report, ReportFile, Detection, ReportStatusLog
from app.services.yolo_service import detect_image, detect_video

LABEL_MAP = {
    0: "bag",
    1: "box",
    2: "rock",
    3: "tire"
}


class ReportService:
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.avi', '.mov'}
    MAX_FILE_SIZE = 50 * 1024 * 1024

    @staticmethod
    def process_report_submission(user_id, form_data, upload_file):
        try:
            title = (form_data.get('title') or '').strip()
            if not title:
                raise ValueError("제목은 필수입니다.")

            if not upload_file or upload_file.filename == '':
                raise ValueError("첨부된 파일이 없습니다.")

            original_name = secure_filename(upload_file.filename)
            ext = os.path.splitext(original_name)[1].lower()

            if ext not in ReportService.ALLOWED_EXTENSIONS:
                raise ValueError(f"허용되지 않는 파일 형식입니다: {ext}")

            upload_file.seek(0, os.SEEK_END)
            file_size = upload_file.tell()
            upload_file.seek(0)

            if file_size > ReportService.MAX_FILE_SIZE:
                raise ValueError(f"파일 용량은 50MB를 넘을 수 없습니다. (현재: {round(file_size / 1024 / 1024, 2)}MB)")

            inferred_type = '이미지' if ext in {'.jpg', '.jpeg', '.png', '.webp'} else '영상'
            final_report_type = form_data.get('report_type') or inferred_type

            try:
                latitude = float(form_data.get('latitude') or 0.0)
                longitude = float(form_data.get('longitude') or 0.0)
            except (ValueError, TypeError):
                latitude = 0.0
                longitude = 0.0

            new_report = Report(
                user_id=user_id,
                title=title,
                content=form_data.get('content'),
                report_type=final_report_type,
                location_text=form_data.get('location_text') or '위치 정보 없음',
                latitude=latitude,
                longitude=longitude,
                status='접수',
                created_at=datetime.now()
            )
            db.session.add(new_report)
            db.session.flush()

            stored_name = f"{uuid.uuid4().hex}{ext}"
            upload_folder = os.path.join('app', 'static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file_path = os.path.join(upload_folder, stored_name)
            upload_file.save(file_path)

            if inferred_type == '영상':
                cap = cv2.VideoCapture(file_path)
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    if fps > 0:
                        duration = frame_count / fps
                        cap.release()
                        if duration > 30:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            raise ValueError(f"영상 길이는 30초를 초과할 수 없습니다. (현재: {round(duration, 1)}초)")
                    else:
                        cap.release()

            new_file = ReportFile(
                report_id=new_report.id,
                original_name=original_name,
                stored_name=stored_name,
                file_path=f"static/uploads/{stored_name}",
                file_type=inferred_type,
                file_size=file_size,
                is_active=1,
                uploaded_at=datetime.now()
            )
            db.session.add(new_file)
            db.session.flush()

            try:
                threshold = 0.5
                detections_data = detect_image(file_path) if inferred_type == '이미지' else detect_video(file_path)

                old_status = None
                new_status = "접수"
                highest_score = 0

                risk_score_map = {"rock": 4, "tire": 3, "box": 2, "bag": 2}
                risk_level_names = {4: "긴급", 3: "위험", 2: "주의", 1: "낮음"}

                valid_detections = [
                    d for d in (detections_data or [])
                    if d.get('confidence', 0) >= threshold and d.get('class_id') in LABEL_MAP
                ]

                if valid_detections:
                    for d in valid_detections:
                        bbox = d.get('bbox', [0, 0, 0, 0])
                        label = LABEL_MAP[d['class_id']]
                        base_score = risk_score_map.get(label, 1)

                        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                        if area > (640 * 640 * 0.1):
                            base_score = min(base_score + 1, 4)

                        if base_score > highest_score:
                            highest_score = base_score

                        db.session.add(Detection(
                            report_id=new_report.id,
                            file_id=new_file.id,
                            detected_label=label,
                            confidence=float(d.get('confidence', 0)),
                            bbox_x1=int(bbox[0]),
                            bbox_y1=int(bbox[1]),
                            bbox_x2=int(bbox[2]),
                            bbox_y2=int(bbox[3]),
                            frame_no=d.get('frame_no'),
                            time_sec=float(d.get('time_sec')) if d.get('time_sec') is not None else None,
                            frame_width=d.get('frame_width'),
                            frame_height=d.get('frame_height'),
                            detected_at=datetime.now(),
                            created_at=datetime.now()
                        ))

                    new_report.risk_level = risk_level_names.get(highest_score, "주의")
                    memo = f"AI 분석 결과 {new_report.risk_level} 등급 낙하물 탐지"
                else:
                    new_status = "오탐"
                    memo = "AI 분석 결과 낙하물 없음"
                    new_report.risk_level = "낮음"

                if old_status != new_status:
                    new_report.status = new_status
                    db.session.add(ReportStatusLog(
                        report_id=new_report.id,
                        old_status=old_status,
                        new_status=new_status,
                        changed_by=user_id,
                        memo=memo,
                        created_at=datetime.now()
                    ))

            except Exception as ai_e:
                print(f"AI Error: {ai_e}")
                new_report.status = "접수"

            db.session.commit()
            return True

        except ValueError as ve:
            db.session.rollback()
            raise ve
        except Exception as e:
            db.session.rollback()
            raise e