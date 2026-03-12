import os
from datetime import datetime
from werkzeug.utils import secure_filename
from database import get_db_connection

# 역할 : 신고 접수 시 수행되는 실제 데이터 처리 로직
# 1. 정보를 DB에 저장하고 2. 파일을 서버 폴더에 물리적으로 저장

def process_report_submission(form_data, upload_file):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # [수정] 컬럼은 8개인데 %s가 부족했던 부분을 8개로 수정함
        # [수정] 변수명 오타 수정: slq_report -> sql_report
        sql_report = """
            INSERT INTO reports (user_id, title, content, report_type, location_text, latitude, longitude, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # [수정] status 값인 '접수'를 포함하여 총 8개의 파라미터 전달
        cursor.execute(sql_report, (
            1, # 테스트용 user_id
            form_data.get('title'),
            form_data.get('content'),
            form_data.get('report_type'),
            form_data.get('location_text') or '위치 정보 없음', # 텍스트가 없으면 문구 대체
            form_data.get('latitude') or 0.0,  # 빈 문자열('')이면 0.0 (숫자형) 대입
            form_data.get('longitude') or 0.0, # 빈 문자열('')이면 0.0 (숫자형) 대입
            '접수'
        ))
        
        report_id = cursor.lastrowid # 생성된 신고 ID 가져오기

        # 파일이 첨부된 경우 물리적 저장 및 DB 기록
        if upload_file and upload_file.filename != '':
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            # secure_filename으로 안전한 파일명 생성
            filename = f"{report_id}_{timestamp}_{secure_filename(upload_file.filename)}"

            # 저장경로 설정 (루트의 uploads 폴더)
            file_path = os.path.join('uploads', filename)
            upload_file.save(file_path)

            # report_files 테이블에 파일 정보 저장
            sql_file = """
                INSERT INTO report_files (report_id, original_name, stored_name, file_path, file_type, file_size)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            # 실제 저장된 파일의 크기를 계산
            file_size = os.path.getsize(file_path)
            
            cursor.execute(sql_file, (
                report_id,
                upload_file.filename,
                filename,
                file_path,
                form_data.get('report_type'),
                file_size
            ))
        
        conn.commit() # 트랜잭션 확정
        return True

    except Exception as e:
        conn.rollback() # 에러 발생 시 되돌리기
        print(f"Service Error: {e}")
        raise e # 발생한 에러를 route로 던져서 처리하게 함
    finally:
        conn.close() # DB 연결 종료