from flask import Blueprint, session, render_template, redirect, url_for
from app.services.auth_service import AuthService
from app.services.report_service import ReportService
from app.common.response import success_response, error_response

report_bp = Blueprint("report", __name__, url_prefix="/reports")


@report_bp.route("/my-page", methods=["GET"])
def my_reports_page():
    user_id = session.get("user_id")

    # 로그인 기능 아직 없으므로 개발용 임시 user
    if not user_id:
        user_id = 1

    #if not user_id:
    #    return error_response(
    #        message="로그인이 필요합니다.",
    #        status_code=401
    #    )

    user = AuthService.get_user_info(user_id)
    return render_template("my_reports.html", user=user)


@report_bp.route("/my", methods=["GET"])
def get_my_reports():
    try:
        user_id = session.get("user_id")
        # 로그인 기능 아직 없으므로 개발용 임시 user
        if not user_id:
            user_id = 1

        #if not user_id:
        #    return error_response(
        #        message="로그인이 필요합니다.",
        #        status_code=401
        #    )

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