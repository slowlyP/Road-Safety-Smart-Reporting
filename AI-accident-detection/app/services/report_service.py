import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db 
# [중요] 필요한 모든 모델을 임포트합니다.
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
    @staticmethod
    def process_report_submission(user_id, form_data, upload_file):
        try:
            # 1. Report 기본 객체 생성
            new_report = Report(
                user_id=user_id,
                title=form_data.get('title'),
                content=form_data.get('content'),
                report_type=form_data.get('report_type'),
                location_text=form_data.get('location_text') or '위치 정보 없음',
                latitude=float(form_data.get('latitude') or 0.0),
                longitude=float(form_data.get('longitude') or 0.0),
                status='접수', # 초기 상태
                created_at=datetime.now()
            )
            db.session.add(new_report)
            db.session.flush()

            # 2. 파일 처리 및 DB 등록
            if upload_file and upload_file.filename != '':
                original_name = secure_filename(upload_file.filename)
                ext = os.path.splitext(original_name)[1].lower()
                stored_name = f"{uuid.uuid4().hex}{ext}"
                upload_folder = os.path.join('app', 'static', 'uploads')
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                file_path = os.path.join(upload_folder, stored_name)
                upload_file.save(file_path)

                new_file = ReportFile(
                    report_id=new_report.id,
                    original_name=original_name,
                    stored_name=stored_name,
                    file_path=f"static/uploads/{stored_name}",
                    file_type='이미지' if 'image' in upload_file.content_type else '영상',
                    file_size=os.path.getsize(file_path),
                    is_active=1,
                    uploaded_at=datetime.now()
                )
                db.session.add(new_file)
                db.session.flush()

                # 3. AI 분석 및 결과 처리
                try:
                    threshold = 0.5
                    detections_data = []

                    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        detections_data = detect_image(file_path)
                    elif ext in ['.mp4', '.avi', '.mov']:
                        detections_data = detect_video(file_path)

                    # 상태 변경 추적을 위한 변수
                    old_status = None
                    new_status = "접수"

                    # 위험도 로직 추가 
                    highest_score = 0
                    risk_score_map = {"rock": 4, "tire": 3, "box": 2, "bag":2, "debris": 1}
                    risk_level_names = {4: "긴급", 3: "위험", 2: "주의", 1: "낮음"}

                    if detections_data and any(d.get('confidence', 0) >= threshold for d in detections_data):
                        # (1) Detection 상세 정보 저장
                        for d in detections_data:
                            if d.get('confidence', 0) >= threshold:
                                bbox = d.get('bbox', [0, 0, 0, 0])
                                label = LABEL_MAP.get(d.get('class_id'), 'debris')
                                # 위험도 로직 추가 ( 객체별 점수 계산)
                                # 기본 점수 + 면적 가중치( 면적이 이미지의 10% 이상이면 +1점)
                                base_score = risk_score_map.get(label, 1)

                                # 면적 계산 (YOLO 가상 크기 640x640 기준 예시)
                                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                                if area > (640 * 640 * 0.1): # 전체의 10% 초과 시
                                    base_score = min(base_score + 1, 4)

                                if base_score > highest_score:
                                    highest_score = base_score

                                new_det = Detection(
                                    report_id=new_report.id,
                                    file_id=new_file.id,
                                    detected_label=LABEL_MAP.get(d.get('class_id'), 'debris'),
                                    confidence=float(d.get('confidence', 0)),
                                    bbox_x1=int(bbox[0]),
                                    bbox_y1=int(bbox[1]),
                                    bbox_x2=int(bbox[2]),
                                    bbox_y2=int(bbox[3]),
                                    detected_at=datetime.now(),
                                    created_at=datetime.now()
                                )
                                db.session.add(new_det)
                        # 위험도 로직 추가 // 루프 종료 후 리포트 객체에 반영
                        new_report.risk_level = risk_level_names.get(highest_score, "주의")


                        # (2) Report 상태 업데이트
                        new_status = "접수"
                        memo = f"AI 분석 결과 {new_report.risk_level} 등급 낙하물 탐지"
                    else:
                        new_status = "오탐"
                        memo = "AI 분석 결과 낙하물 없음"
                        new_report.risk_level = "낮음" 

                    # (3) 상태가 변했다면 로그 남기기
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
                    new_report.status = "접수" # 에러 시 기본 상태 유지

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Service Error: {e}")
            raise e