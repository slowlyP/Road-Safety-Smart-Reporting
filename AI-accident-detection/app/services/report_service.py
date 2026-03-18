import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Report, ReportFile, Detection, ReportStatusLog
from app.services.yolo_service import detect_image, detect_video

# DB 저장용 영문 매핑
LABEL_MAP = {
    0: "box",
    1: "bag",
    2: "tire",
    3: "rock",
    4: "debris"
}


class ReportService:
    # [설정] 허용할 확장자와 최대 용량
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.avi', '.mov'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    @staticmethod
    def process_report_submission(user_id, form_data, upload_file):
        try:
            # -------------------------------------------------------
            # 0. 파일 유효성 검증 및 타입 결정
            # -------------------------------------------------------
            if not upload_file or upload_file.filename == '':
                raise ValueError("첨부된 파일이 없습니다.")

            original_name = secure_filename(upload_file.filename)
            ext = os.path.splitext(original_name)[1].lower()

            if ext not in ReportService.ALLOWED_EXTENSIONS:
                raise ValueError(f"허용되지 않는 파일 형식입니다: {ext}")

            # 용량 체크
            upload_file.seek(0, os.SEEK_END)
            file_size = upload_file.tell()
            upload_file.seek(0)  # 검사 후 다시 처음으로 돌려놔야 저장 가능

            if file_size > ReportService.MAX_FILE_SIZE:
                raise ValueError("파일 용량은 50MB를 넘을 수 없습니다.")

            # report_type 자동 결정 (이미지/영상)
            inferred_type = '이미지' if ext in {'.jpg', '.jpeg', '.png', '.webp'} else '영상'
            # 프론트에서 넘어온 값이 없으면 자동으로 정해진 타입 사용
            final_report_type = form_data.get('report_type') or inferred_type

            # -------------------------------------------------------
            # 1. Report 기본 객체 생성
            # -------------------------------------------------------
            new_report = Report(
                user_id=user_id,
                title=form_data.get('title'),
                content=form_data.get('content'),
                report_type=final_report_type,  # [수정] inferred_type 로직 반영
                location_text=form_data.get('location_text') or '위치 정보 없음',
                latitude=float(form_data.get('latitude') or 0.0),
                longitude=float(form_data.get('longitude') or 0.0),
                status='접수',
                created_at=datetime.now()
            )
            db.session.add(new_report)
            db.session.flush()

            # -------------------------------------------------------
            # 2. 파일 물리 저장 및 DB 등록
            # -------------------------------------------------------
            stored_name = f"{uuid.uuid4().hex}{ext}"
            upload_folder = os.path.join('app', 'static', 'uploads')

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file_path = os.path.join(upload_folder, stored_name)
            upload_file.save(file_path)  # 물리 파일 저장

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

            # -------------------------------------------------------
            # 3. AI 분석 및 결과 처리 (기존 로직 유지 및 정리)
            # -------------------------------------------------------
            try:
                threshold = 0.5
                detections_data = []

                if inferred_type == '이미지':
                    detections_data = detect_image(file_path)
                else:
                    detections_data = detect_video(file_path)

                old_status = None
                new_status = "접수"
                highest_score = 0
                risk_score_map = {"rock": 4, "tire": 3, "box": 2, "bag": 2, "debris": 1}
                risk_level_names = {4: "긴급", 3: "위험", 2: "주의", 1: "낮음"}

                if detections_data and any(d.get('confidence', 0) >= threshold for d in detections_data):
                    for d in detections_data:
                        if d.get('confidence', 0) >= threshold:
                            bbox = d.get('bbox', [0, 0, 0, 0])
                            label = LABEL_MAP.get(d.get('class_id'), 'debris')
                            base_score = risk_score_map.get(label, 1)

                            # 면적 가중치 (10% 이상 시)
                            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                            if area > (640 * 640 * 0.1):
                                base_score = min(base_score + 1, 4)

                            if base_score > highest_score:
                                highest_score = base_score

                            new_det = Detection(
                                report_id=new_report.id,
                                file_id=new_file.id,
                                detected_label=label,
                                confidence=float(d.get('confidence', 0)),
                                bbox_x1=int(bbox[0]),
                                bbox_y1=int(bbox[1]),
                                bbox_x2=int(bbox[2]),
                                bbox_y2=int(bbox[3]),
                                detected_at=datetime.now(),
                                created_at=datetime.now()
                            )
                            db.session.add(new_det)

                    new_report.risk_level = risk_level_names.get(highest_score, "주의")
                    memo = f"AI 분석 결과 {new_report.risk_level} 등급 낙하물 탐지"
                else:
                    new_status = "오탐"
                    memo = "AI 분석 결과 낙하물 없음"
                    new_report.risk_level = "낮음"

                # 상태 로그 남기기
                if old_status != new_status:
                    new_report.status = new_status
                    status_log = ReportStatusLog(
                        report_id=new_report.id,
                        old_status=old_status,
                        new_status=new_status,
                        changed_by=user_id,
                        memo=memo,
                        created_at=datetime.now()
                    )
                    db.session.add(status_log)

            except Exception as ai_e:
                print(f"AI Error: {ai_e}")
                new_report.status = "접수"  # 에러 시 기본값 유지

            db.session.commit()
            return True

        except ValueError as ve:
            # 유효성 검사에서 발생한 에러 처리 (로그인 사용자에게 메시지 전달용)
            db.session.rollback()
            raise ve
        except Exception as e:
            db.session.rollback()
            print(f"Service Error: {e}")
            raise e