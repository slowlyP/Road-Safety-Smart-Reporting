<<<<<<< HEAD
from flask import Blueprint, request, jsonify, render_template # render_template 추가
from app.services.report_service import process_report_submission

# 역할: 'report'라는 이름의 Blueprint 생성
report_bp = Blueprint('report', __name__)

# --- [여기 추가된 부분] 사용자가 주소를 치고 들어왔을 때 페이지를 보여주는 함수 ---
@report_bp.route('/report/create', methods=['GET'])
def create_report_page():
    """
    브라우저 주소창에 /report/create를 입력하면 
    신고 등록 HTML 페이지를 보여줍니다.
    """
    return render_template('report/create.html')


# --- 기존에 작성하신 데이터 처리 함수 ---
@report_bp.route('/api/report', methods=['POST'])
def create_report():
    """
    브라우저의 JS(fetch)가 보낸 데이터를 받아 서비스를 호출합니다.
    """
    try:
        form_data = request.form
        upload_file = request.files.get('files')

        if not upload_file or upload_file.filename == '':
            return jsonify({"error": "첨부된 파일이 없습니다."}), 400

        process_report_submission(form_data, upload_file)

        return jsonify({'message': "신고가 성공적으로 접수되었습니다."}), 200

    except Exception as e:
        print(f"Route Error: {e}")
        return jsonify({"error": "신고 접수 중 오류가 발생했습니다."}), 500
=======
from flask import Blueprint, request, jsonify, render_template
from app.services.report_service import ReportService # 수정된 클래스 기반 서비스 임포트

# Blueprint 생성
report_bp = Blueprint('report', __name__)

class ReportRoute:
    """
    신고 관련 HTTP 요청(Route)을 처리하는 클래스
    """

    @staticmethod
    @report_bp.route('/report/create', methods=['GET'])
    def create_report_page():
        """
        신고 등록 HTML 페이지를 렌더링합니다.
        """
        return render_template('report/create.html')

    @staticmethod
    @report_bp.route('/api/report', methods=['POST'])
    def create_report():
        """
        신고 데이터를 접수받아 처리합니다.
        """
        try:
            form_data = request.form
            upload_file = request.files.get('files')

            if not upload_file or upload_file.filename == '':
                return jsonify({"error": "첨부된 파일이 없습니다."}), 400

            # 클래스 기반으로 바뀐 서비스를 호출합니다.
            ReportService.process_report_submission(form_data, upload_file)

            return jsonify({'message': "신고가 성공적으로 접수되었습니다."}), 200

        except Exception as e:
            print(f"Route Error: {e}")
            return jsonify({"error": "신고 접수 중 오류가 발생했습니다."}), 500
>>>>>>> c6b7862f85caed1a819865166490fc94f379d5dd
