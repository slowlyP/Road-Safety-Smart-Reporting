from flask import Blueprint, request, jsonify
from services.report_service import process_report_submission

# 역활 : 'report'라는 이름의 Blueprint(기능 묶음) 을 생성

report_bp = Blueprint('report', __name__)

@report_bp.route('/api/report', methods=['POST'])
def create_report():
    """
    브라우저의 JS(fetch)가 보낸 데이터를 받아 서비스를 호출합니다.
    """

    try:
        # request.form : 제목, 내용, 좌표 등의 텍스트 데이터
        form_data = request.form

        # request.files.get('files') : 업로드된 파일 데이터
        upload_file = request.files.get('files')

        # 파일 유효성 검사(방어코드)
        # 파일이 아예 없거나, 파일이름이 비어있는 경우 400 에러와 함께 중단됨
        if not upload_file or upload_file.filename == '':
            return jsonify({"error": "첨부된 파일이 없습니다."}), 400

        # [서비스 호출] 실제 저장 로직은 report_service.py에서 수행
        process_report_submission(form_data, upload_file)

        # 성공 시 브라우저에 200(성공) 응답을 보냄
        return jsonify({'message': "신고가 성공적으로 접수되었습니다."}), 200

    except Exception as e:
        # 에러 발생 시 로그를 찍고 500(서버 에러) 응답을 보냄
        print(f"Route Error: {e}")
        return jsonify({"error": "신고 접수 중 오류가 발생했습니다."}), 500
