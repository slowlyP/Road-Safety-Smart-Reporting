import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Detection, Report, ReportFile, ReportStatusLog
from app.services.yolo_service import detect_image, detect_video

# DB 저장용 영문 매핑 (우리가 정의한 5가지 낙하물)
LABEL_MAP = {
    0: "box",
    1: "bag",
    2: "tire",
    3: "rock",
    4: "debris",
}


class ReportService:
    # [설정] 허용할 확장자와 최대 용량
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".avi", ".mov"}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    @staticmethod
    def process_report_submission(user_id, form_data, upload_file):
        """
        신고 접수(Report/ReportFile 저장) + AI 분석(Detection 저장)까지 수행.
        성공 시 신고 요약 정보를 dict로 반환.
        """
        try:
            # -------------------------------------------------------
            # 0. 기본 입력 검증 (제목 빈값 방어)
            # -------------------------------------------------------
            title = (form_data.get("title") or "").strip()
            if not title:
                raise ValueError("제목은 필수입니다.")

            if not upload_file or upload_file.filename == "":
                raise ValueError("첨부된 파일이 없습니다.")

            original_name = secure_filename(upload_file.filename)
            ext = os.path.splitext(original_name)[1].lower()

            if ext not in ReportService.ALLOWED_EXTENSIONS:
                raise ValueError(f"허용되지 않는 파일 형식입니다: {ext}")

            # -------------------------------------------------------
            # 0-1. 파일 용량 체크 (서비스 레벨)
            # -------------------------------------------------------
            upload_file.seek(0, os.SEEK_END)
            file_size = upload_file.tell()
            upload_file.seek(0)

            if file_size > ReportService.MAX_FILE_SIZE:
                raise ValueError("파일 용량은 50MB를 넘을 수 없습니다.")

            inferred_type = "이미지" if ext in {".jpg", ".jpeg", ".png", ".webp"} else "영상"
            final_report_type = form_data.get("report_type") or inferred_type

            # 위도/경도 방어 파싱 (잘못된 값이면 기본값 적용)
            try:
                latitude = float(form_data.get("latitude") or 37.5665)
                longitude = float(form_data.get("longitude") or 126.9780)
            except (ValueError, TypeError):
                latitude = 37.5665
                longitude = 126.9780

            # -------------------------------------------------------
            # 1. Report 기본 객체 생성
            # -------------------------------------------------------
            new_report = Report(
                user_id=user_id,
                title=title,
                content=form_data.get("content"),
                report_type=final_report_type,
                location_text=form_data.get("location_text") or "위치 정보 없음",
                latitude=latitude,
                longitude=longitude,
                status="접수",
                created_at=datetime.now(),
            )
            db.session.add(new_report)
            db.session.flush()

            # -------------------------------------------------------
            # 2. 파일 물리 저장 및 DB 등록 (요청하신 상대 경로 유지)
            # -------------------------------------------------------
            stored_name = f"{uuid.uuid4().hex}{ext}"
            upload_folder = os.path.join('static', 'uploads')
            
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file_path = os.path.join(upload_folder, stored_name)
            upload_file.save(file_path)

            new_file = ReportFile(
                report_id=new_report.id,
                original_name=original_name,
                stored_name=stored_name,
                file_path=f"static/uploads/{stored_name}",
                file_type=inferred_type,
                file_size=file_size,
                is_active=True,
                uploaded_at=datetime.now(),
            )
            db.session.add(new_file)
            db.session.flush()

            # -------------------------------------------------------
            # 3. AI 분석 및 결과 처리 (필터링 강화 버전)
            # -------------------------------------------------------
            try:
                threshold = 0.5
                detections_data = []

                if inferred_type == "이미지":
                    detections_data = detect_image(file_path)
                else:
                    detections_data = detect_video(file_path)

                old_status = None
                new_status = "접수"
                highest_score = 0
                risk_score_map = {"rock": 4, "tire": 3, "box": 2, "bag": 2, "debris": 1}
                risk_level_names = {4: "긴급", 3: "위험", 2: "주의", 1: "낮음"}

                # [필터링] 우리가 정의한 낙하물 클래스만 담기 (배, 비행기 등 제외)
                valid_detections = []
                for d in (detections_data or []):
                    conf = d.get("confidence", 0)
                    if conf >= threshold:
                        label = LABEL_MAP.get(d.get("class_id"))
                        if label:
                            valid_detections.append((d, label))

                # 진짜 낙하물이 있을 때만 '접수' 및 DB 저장
                if valid_detections:
                    for d, label in valid_detections:
                        bbox = d.get("bbox", [0, 0, 0, 0])
                        base_score = risk_score_map.get(label, 1)

                        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                        if area > (640 * 640 * 0.1):
                            base_score = min(base_score + 1, 4)

                        if base_score > highest_score:
                            highest_score = base_score

                        new_det = Detection(
                            report_id=new_report.id,
                            file_id=new_file.id,
                            detected_label=label,
                            confidence=float(d.get("confidence", 0)),
                            bbox_x1=int(bbox[0]),
                            bbox_y1=int(bbox[1]),
                            bbox_x2=int(bbox[2]),
                            bbox_y2=int(bbox[3]),
                            detected_at=datetime.now(),
                            created_at=datetime.now(),
                        )
                        db.session.add(new_det)

                    new_report.risk_level = risk_level_names.get(highest_score, "주의")
                    memo = f"AI 분석 결과 {new_report.risk_level} 등급 낙하물 탐지"
                else:
                    # 아무것도 없으면 '오탐' 처리
                    new_status = "오탐"
                    memo = "AI 분석 결과 낙하물 없음 (기타 사물 제외)"
                    new_report.risk_level = "낮음"

                if old_status != new_status:
                    new_report.status = new_status
                    status_log = ReportStatusLog(
                        report_id=new_report.id,
                        old_status=old_status,
                        new_status=new_status,
                        changed_by=user_id,
                        memo=memo,
                        created_at=datetime.now(),
                    )
                    db.session.add(status_log)

            except Exception as ai_e:
                print(f"AI Error: {ai_e}")
                new_report.status = "접수"

            db.session.commit()

            # 상세 정보 반환 (프론트엔드 후속 처리용)
            return {
                "report_id": new_report.id,
                "status": new_report.status,
                "risk_level": new_report.risk_level,
            }

        except ValueError as ve:
            db.session.rollback()
            raise ve
        except Exception as e:
            db.session.rollback()
            print(f"Service Error: {e}")
            raise e