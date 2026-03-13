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

        current_user_id = session.get('user_id')
        # API 보안 체크
        if not current_user_id:
            return jsonify({"error": "로그인이 필요한 서비스 입니다."}), 401

        try:
            form_data = request.form
            upload_file = request.files.get('files')

            if not upload_file or upload_file.filename == '':
                return jsonify({"error": "첨부된 파일이 없습니다."}), 400

            # 클래스 기반으로 바뀐 서비스를 호출합니다.
            ReportService.process_report_submission(form_data, upload_file)
            # 클래스 기반 서비스 호출
            ReportService.process_report_submission(current_user_id, form_data, upload_file)

            return jsonify({'message': "신고가 성공적으로 접수되었습니다."}), 200

        except Exception as e:
            print(f"Route Error: {e}")
            return jsonify({"error": "신고 접수 중 오류가 발생했습니다."}), 500
            return jsonify({"error": "신고 접수 중 오류가 발생했습니다."}), 500
