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
            
            # 변수 초기화
            original_name, stored_name, save_path, inferred_type, file_size = None, None, None, None, None

            # 1. 새 파일 검증 및 물리적 저장
            if is_file_changed:
                original_name = secure_filename(new_file.filename)
                ext = os.path.splitext(original_name)[1].lower()
                
                new_file.seek(0, os.SEEK_END)
                file_size = new_file.tell()
                new_file.seek(0)

                inferred_type = '이미지' if ext in {'.jpg', '.jpeg', '.png', '.webp'} else '영상'
                stored_name = f"{uuid.uuid4().hex}{ext}"
                upload_dir = os.path.join("app", "static", "uploads")
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, stored_name)
                
                new_file.save(save_path)
                print(f"[DEBUG] 파일 저장 완료: {save_path}")

                if inferred_type == '영상':
                    cap = cv2.VideoCapture(save_path)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    duration = frame_count / fps if fps > 0 else 0
                    cap.release()
                    if duration > 30:
                        os.remove(save_path)
                        return False, "영상은 30초 이내만 가능합니다."


            # 2. 기존 데이터 정리
            if delete_file == "Y" or is_file_changed:
                # [추가] 외래 키 제약 조건 해결을 위한 선행 작업
                # 삭제하려는 Detection ID들을 먼저 조회합니다.
                old_detections = Detection.query.filter_by(report_id=report.id).all()
                old_ids = [d.id for d in old_detections]

                if old_ids:
                    # 방법 A: 연결된 알림(Alerts)을 삭제 (가장 확실한 방법)
                    # 만약 Alert 모델이 정의되어 있다면 Alert.query를 사용하고, 
                    # 없다면 아래처럼 직접 SQL 실행문(text)을 사용합니다.
                    from sqlalchemy import text
                    db.session.execute(
                        text("DELETE FROM alerts WHERE detection_id IN :ids"),
                        {"ids": old_ids}
                    )
                    
                    # 만약 관리자 알림 기록을 남겨둬야 한다면 삭제 대신 NULL로 업데이트할 수도 있습니다.
                    # db.session.execute(
                    #     text("UPDATE alerts SET detection_id = NULL WHERE detection_id IN :ids"),
                    #     {"ids": old_ids}
                    # )

                # 이제 제약 조건이 해제되었으므로 Detection 삭제 가능
                Detection.query.filter_by(report_id=report.id).delete()
                db.session.flush()

                if report_file:
                    old_path = os.path.join("app", "static", report_file.file_path.replace("static/", ""))
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    ReportRepository.deactivate_report_file(report_file)

            # 3. 새 파일 DB 등록 및 AI 재분석
            if is_file_changed:
                report.report_type = inferred_type
                db_file_path = f"static/uploads/{stored_name}"
                
                new_file_obj = ReportRepository.create_report_file(
                    report_id=report.id,
                    original_name=original_name,
                    stored_name=stored_name,
                    file_path=db_file_path,
                    file_type=inferred_type,
                    file_size=file_size
                )
                db.session.flush()

                try:
                    print(f"[DEBUG] >>> AI 재분석 진입 완료. 경로: {save_path}") # 진입 확인
                    
                    # 분석 시작
                    detections = detect_image(save_path) if inferred_type == '이미지' else detect_video(save_path)
                    
                    print(f"[DEBUG] >>> AI 분석 종료. 탐지된 물체 수: {len(detections) if detections else 0}") # 종료 확인

                    # ... (이후 DB 저장 로직)

                    # 위험도 판별용 변수 설정
                    highest_score = 0
                    risk_map = {"rock": 4, "tire": 3, "box": 2, "bag": 2}
                    risk_names = {4: "긴급", 3: "위험", 2: "주의", 1: "낮음"}

                    if detections and len(detections) > 0:
                        print(f"[DEBUG] 탐지 결과 있음: {len(detections)}개")
                        for d in detections:
                            label = LABEL_MAP.get(d.get('class_id'))
                            if label:
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
                        print(f"[DEBUG] 탐지 결과 없음 (오탐)")
                        report.status = "오탐"
                        report.risk_level = "낮음"

                    # 상태 변경 로그 기록
                    db.session.add(ReportStatusLog(
                        report_id=report.id,
                        old_status=old_status,
                        new_status=report.status,
                        changed_by=user_id,
                        memo="수정 시 파일 교체로 인한 AI 재분석",
                        created_at=datetime.now()
                    ))

                except Exception as ai_e:
                    print(f"🔥 AI 분석 중 오류 발생: {ai_e}")
                    report.status = "분석실패"

            # 4. 최종 DB 반영
            ReportRepository.commit()
            return True, "수정이 완료되었습니다."

        except Exception as e:
            db.session.rollback()
            print(f"🔥 서버 오류: {e}")
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