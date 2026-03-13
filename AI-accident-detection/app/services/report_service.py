import os
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db  # 조장님이 만든 db 객체 가져오기
from app.models import Report, ReportFile  # 조장님이 만든 모델 클래스 가져오기

# 역할 : 신고 접수 시 수행되는 실제 데이터 처리 로직
def process_report_submission(form_data, upload_file):
    try:
        # 1. Report 객체 생성 (기존 SQL INSERT 문을 대신함)
        new_report = Report(
            user_id=1,  # 테스트용
            title=form_data.get('title'),
            content=form_data.get('content'),
            report_type=form_data.get('report_type'),
            location_text=form_data.get('location_text') or '위치 정보 없음',
            latitude=float(form_data.get('latitude') or 0.0),
            longitude=float(form_data.get('longitude') or 0.0),
            status='접수'
        )

        # DB 세션에 추가
        db.session.add(new_report)
        db.session.flush()  # DB에 미리 밀어넣어서 생성된 ID(report_id)를 가져옴

        # 2. 파일이 첨부된 경우 처리
        if upload_file and upload_file.filename != '':
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{new_report.id}_{timestamp}_{secure_filename(upload_file.filename)}"

            # 저장 경로 (app 외부나 내부의 uploads 폴더 확인 필요)
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file_path = os.path.join(upload_folder, filename)
            upload_file.save(file_path)

            # ReportFile 객체 생성 및 연결
            new_file = ReportFile(
                report_id=new_report.id,
                original_name=upload_file.filename,
                stored_name=filename,
                file_path=file_path,
                file_type=form_data.get('report_type'),
                file_size=os.path.getsize(file_path)
            )
            db.session.add(new_file)

        # 3. 트랜잭션 확정 (모든 처리가 성공하면 한 번에 저장)
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()  # 에러 발생 시 모든 작업 취소
        print(f"Service Error: {e}")
        raise e