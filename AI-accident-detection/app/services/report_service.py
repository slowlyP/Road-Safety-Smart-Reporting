import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db 
from app.models import Report, ReportFile 

# AI 서비스 직접 호출을 위한 import (yolo_service에서 직접 가져옴옴)
from app.services.yolo_service import detect_image, detect_video 

class ReportService:
    """
    신고 관련 비즈니스 로직을 담당하는 서비스 클래스
    """

    @staticmethod
    def process_report_submission(user_id, form_data, upload_file):
        """
        사용자의 신고 제출 데이터를 받아 DB에 저장하고 파일을 처리하는 메서드
        """
        try:
            # 1. Report 객체 생성 (클래스 활용)
            new_report = Report(
                user_id= user_id,
                title=form_data.get('title'),
                content=form_data.get('content'),
                report_type=form_data.get('report_type'),
                location_text=form_data.get('location_text') or '위치 정보 없음',
                latitude=float(form_data.get('latitude') or 0.0),
                longitude=float(form_data.get('longitude') or 0.0),
                status='접수',
                created_at=datetime.now()
            )

            db.session.add(new_report)
            db.session.flush() # db에 임시 반영해서 new_report.id 확보보

            # 2. 파일 처리 로직
            if upload_file and upload_file.filename != '':
                original_name = secure_filename(upload_file.filename)
                ext = os.path.splitext(original_name)[1].lower()
                stored_name = f"{uuid.uuid4().hex}{ext}"

                upload_folder = os.path.join('app', 'static', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                file_path = os.path.join(upload_folder, stored_name)
                upload_file.save(file_path)

                # 이미지 파일의 경우 AI 분석 수행
                try:

                    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        detections = detect_image(file_path)

                        if detections:
                            # 탐지 결과 중 가장 신뢰도가 높은 첫 번째 객체 정보를 report 에 기록
                            new_report.detected_item = detections[0]['label']
                            new_report.confidence = detections[0]['confidence']

                    # 영상 파일일 경우 AI 분석 수행
                    elif ext in ['.mp4', '.avi', '.mov']:
                        video_result = detect_video(file_path)
                        # 영상도 첫 번째 탐지 결과를 저장하도록 추가
                        if video_result and len(video_result) > 0:
                            new_report.detected_item = video_result[0]['label']
                            new_report.confidence = video_result[0]['confidence']
                except Exception as ai_e:
                    # AI 분석이 실패해도 신고는 접소되도록 로그만 출력
                    print(f"AI Analysis warning:{ai_e}")



                # ReportFile 객체 생성
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

            # 3. 트랜잭션 확정
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Service Error: {e}")
            raise e