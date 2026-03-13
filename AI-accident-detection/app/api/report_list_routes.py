from flask import Blueprint, session, render_template
from app.services.report_list_service import ReportService
from app.common.response import success_response, error_response

report_list_bp = Blueprint("report_list", __name__, url_prefix="/reports")


@report_list_bp.route("/my-page", methods=["GET"])
def my_reports_page():
    user = {
        "name": session.get("user_name"),
        "username": session.get("user_uid"),
        "email": session.get("user_email"),
        "role": session.get("user_role"),
        "created_at": None
    }
    return render_template("myreport/my_reports.html", user=user)


@report_list_bp.route("/my", methods=["GET"])
def get_my_reports():
    try:
        user_id = session.get("user_id")

        if not user_id:
            return error_response(
                message="로그인이 필요합니다.",
                status_code=401
            )

        reports = ReportService.get_my_reports(user_id)

        return success_response(
            message="내 신고 목록 조회 성공",
            data=reports,
            status_code=200
        )

    except Exception as e:
        return error_response(
            message="내 신고 목록 조회 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )