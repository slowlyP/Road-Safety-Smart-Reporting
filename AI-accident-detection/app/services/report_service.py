import os
import uuid  # 랜덤 파일명 생성을 위해 추가
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db 
from app.models import Report, ReportFile 

def process_report_submission(form_data, upload_file):
    try:
        # 1. Report 객체 생성 (reports 테이블)
        new_report = Report(
            user_id=1,  # 로그인 기능 연동 전까지 테스트용
            title=form_data.get('title'),
            content=form_data.get('content'),
            report_type=form_data.get('report_type'),
            location_text=form_data.get('location_text') or '위치 정보 없음',
            latitude=float(form_data.get('latitude') or 0.0),
            longitude=float(form_data.get('longitude') or 0.0),
            status='접수',
            created_at=datetime.now() # 등록일시 기록
        )

        db.session.add(new_report)
        db.session.flush() 

        # 2. 파일 처리 (report_files 테이블)
        if upload_file and upload_file.filename != '':
            # 설계도에 충실하게: stored_name을 랜덤하게(UUID) 생성하여 중복 방지
            original_name = secure_filename(upload_file.filename)
            ext = os.path.splitext(original_name)[1]
            stored_name = f"{uuid.uuid4().hex}{ext}" # 예: a1b2c3d4...jpg

            # 저장 경로 설정 (웹에서 접근 가능하도록 static/uploads 권장)
            upload_folder = os.path.join('app', 'static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file_path = os.path.join(upload_folder, stored_name)
            upload_file.save(file_path)

            # ReportFile 객체 생성 (설계도 속성명 100% 매칭)
            new_file = ReportFile(
                report_id=new_report.id,
                original_name=original_name,
                stored_name=stored_name,
                file_path=f"static/uploads/{stored_name}", # 웹 URL 경로
                file_type='이미지' if 'image' in upload_file.content_type else '영상',
                file_size=os.path.getsize(file_path),
                is_active=1, # 현재 사용 중 상태
                uploaded_at=datetime.now() # 업로드 시간 기록
            )
            db.session.add(new_file)

        # 3. 모든 작업이 성공하면 확정
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback() 
        print(f"Service Error: {e}")
        raise e