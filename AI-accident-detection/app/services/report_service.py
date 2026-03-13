import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db 
from app.models import Report, ReportFile 

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
            db.session.flush()

            # 2. 파일 처리 로직
            if upload_file and upload_file.filename != '':
                original_name = secure_filename(upload_file.filename)
                ext = os.path.splitext(original_name)[1]
                stored_name = f"{uuid.uuid4().hex}{ext}"

                upload_folder = os.path.join('app', 'static', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                file_path = os.path.join(upload_folder, stored_name)
                upload_file.save(file_path)

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