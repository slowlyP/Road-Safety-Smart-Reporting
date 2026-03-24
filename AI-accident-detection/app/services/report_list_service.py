import os
import cv2
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Report, ReportFile, Detection, ReportStatusLog
from app.repositories.report_repository import ReportRepository
from app.services.yolo_service import detect_image, detect_video

LABEL_MAP = {0: "bag", 1: "box", 2: "rock", 3: "tire"}


class ReportService:
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.avi', '.mov'}
    MAX_FILE_SIZE = 50 * 1024 * 1024

    @staticmethod
    def get_my_reports(user_id):
        reports = ReportRepository.find_my_reports(user_id)
        if not reports:
            return []

        result = []
        for report in reports:
            report_file = ReportRepository.find_active_file_by_report_id(report.id)
            file_type = "일반"
            if report_file and report_file.file_type:
                file_type = report_file.file_type

            result.append({
                "id": report.id,
                "title": report.title,
                "content": report.content,
                "report_type": report.report_type,
                "location_text": report.location_text,
                "status": report.status,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "-",
                "file_type": file_type
            })
        return result

    @staticmethod
    def get_my_report_detail(user_id, report_id):
        report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)
        if not report:
            return None

        file_type = None
        file_url = None
        has_detection = False

        if report_file and report_file.file_path:
            file_type = report_file.file_type
            normalized_path = report_file.file_path.replace("\\", "/")
            file_url = "/" + normalized_path if normalized_path.startswith("static/") else "/static/" + normalized_path
            has_detection = ReportRepository.has_detection_by_file_id(report_file.id)

        return {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "report_type": report.report_type,
            "location_text": report.location_text,
            "status": report.status,
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "-",
            "file_type": file_type,
            "file_url": file_url,
            "has_detection": has_detection
        }

    @staticmethod
    def update_my_report(user_id, report_id, title, location_text, content, new_file, delete_file):
        try:
            report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)
            if not report:
                return False, "해당 신고 내역을 찾을 수 없습니다."

            old_status = report.status

            report.title = (title or "").strip()
            if not report.title:
                return False, "제목은 필수 입력 사항입니다."

            report.location_text = location_text or "위치 정보 없음"
            report.content = content or ""

            is_file_changed = (new_file is not None and new_file.filename.strip() != '')

            original_name = None
            ext = None
            file_size = None
            inferred_type = None
            stored_name = None
            save_path = None


            # 1. 새 파일이 있으면 먼저 검증
            if is_file_changed:
                original_name = secure_filename(new_file.filename)
                ext = os.path.splitext(original_name)[1].lower()
                print(f"[DEBUG] 업로드 시도된 파일명: {original_name}, 확장자: {ext}") # 삽입

                allowed_ext = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.avi', '.mov'}
                if ext not in allowed_ext:
                    print(f"[DEBUG] 확장자 제한 걸림: {ext}") # 삽입
                    return False, f"지원하지 않는 파일 형식입니다: {ext}"

                new_file.seek(0, os.SEEK_END)
                file_size = new_file.tell()
                new_file.seek(0)
                print(f"[DEBUG] 파일 크기: {round(file_size / 1024 / 1024, 2)}MB") # 삽입

                if file_size > 50 * 1024 * 1024:
                    print(f"[DEBUG] 용량 제한 걸림: {file_size}") # 삽입
                    return False, "용량 초과! (50MB 제한)"

                inferred_type = '이미지' if ext in {'.jpg', '.jpeg', '.png', '.webp'} else '영상'
                print(f"[DEBUG] 판별된 타입: {inferred_type}") # 삽입

                # 임시 저장
                stored_name = f"{uuid.uuid4().hex}{ext}"
                upload_dir = os.path.join("app", "static", "uploads")
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, stored_name)

                new_file.save(save_path)
                print(f"[DEBUG] 파일 임시 저장 완료: {save_path}") # 삽입

                if inferred_type == '영상':
                    print(f"[DEBUG] 영상 길이 분석 시작...") # 삽입
                    cap = cv2.VideoCapture(save_path)

                    if not cap.isOpened():
                        print(f"[DEBUG] VideoCapture 오픈 실패!") # 삽입
                        cap.release()
                        os.remove(save_path)
                        return False, "유효하지 않은 영상 파일입니다."

                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

                    if fps <= 0:
                        print(f"[DEBUG] FPS 값 오류: {fps}") # 삽입
                        cap.release()
                        os.remove(save_path)
                        return False, "영상 정보를 읽을 수 없습니다. (fps 오류)"

                    duration = frame_count / fps
                    print(f"[DEBUG] 분석 결과 - FPS: {fps}, Frames: {frame_count}, Duration: {duration}초") # 삽입
                    cap.release()

                    if duration > 30:
                        print(f"[DEBUG] 영상 길이 제한 걸림: {duration}초") # 삽입
                        os.remove(save_path)
                        return False, f"영상은 30초 이내만 가능합니다. (현재 {round(duration, 1)}초)"

            # 2. 검증 통과 후 기존 데이터 정리
            if delete_file == "Y" or is_file_changed:
                Detection.query.filter_by(report_id=report.id).delete()

                if report_file:
                    old_path = os.path.join("app", "static", report_file.file_path.replace("static/", ""))
                    if os.path.exists(old_path):
                        os.remove(old_path)

                    ReportRepository.deactivate_report_file(report_file)
                    report_file = None

            # 3. 새 파일 DB 저장
            if is_file_changed:

                report.report_type = inferred_type
                
                new_file_obj = ReportRepository.create_report_file(
                    report_id=report.id,
                    original_name=original_name,
                    stored_name=stored_name,
                    file_path=f"static/uploads/{stored_name}",
                    file_type=inferred_type,
                    file_size=file_size
                )

                db.session.flush()

                try:
                    detections = detect_image(save_path) if inferred_type == '이미지' else detect_video(save_path)

                    highest_score = 0
                    risk_map = {"rock": 4, "tire": 3, "box": 2, "bag": 2}
                    risk_names = {4: "긴급", 3: "위험", 2: "주의", 1: "낮음"}

                    if detections:
                        for d in detections:
                            if d.get('class_id') in LABEL_MAP:
                                label = LABEL_MAP[d['class_id']]
                                highest_score = max(highest_score, risk_map.get(label, 1))

                                db.session.add(Detection(
                                    report_id=report.id,
                                    file_id=new_file_obj.id,
                                    detected_label=label,
                                    confidence=float(d.get('confidence', 0)),
                                    bbox_x1=int(d['bbox'][0]),
                                    bbox_y1=int(d['bbox'][1]),
                                    bbox_x2=int(d['bbox'][2]),
                                    bbox_y2=int(d['bbox'][3]),
                                    created_at=datetime.now()
                                ))

                        report.status = "접수"
                        report.risk_level = risk_names.get(highest_score, "주의")
                    else:
                        report.status = "오탐"
                        report.risk_level = "낮음"

                    db.session.add(ReportStatusLog(
                        report_id=report.id,
                        old_status=old_status,
                        new_status=report.status,
                        changed_by=user_id,
                        memo="수정 시 파일 교체로 인한 AI 재분석",
                        created_at=datetime.now()
                    ))

                except Exception as ai_e:
                    print(f"AI Error: {ai_e}")

            ReportRepository.commit()
            return True, "수정이 완료되었습니다."

        except Exception as e:
            db.session.rollback()
            return False, f"서버 오류: {str(e)}"

    @staticmethod
    def delete_my_report(user_id, report_id):
        try:
            report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)

            if not report:
                return False

            if report_file:
                full_path = os.path.join("app", "static", report_file.file_path.replace("static/", ""))
                if os.path.exists(full_path):
                    os.remove(full_path)

                ReportRepository.deactivate_report_file(report_file)

            Detection.query.filter_by(report_id=report.id).delete()
            ReportRepository.delete_report(report)
            ReportRepository.commit()

            return True

        except Exception:
            db.session.rollback()
            return False