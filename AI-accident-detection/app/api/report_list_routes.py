from flask import Blueprint, session, render_template, redirect, url_for, flash, request
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
        print("🔥 에러:", e)
        return error_response(
            message="내 신고 목록 조회 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )

@report_list_bp.route("/<int:report_id>/page", methods=["GET"])
def my_report_detail_page(report_id):

    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    report = ReportService.get_my_report_detail(user_id, report_id)

    if not report:
        return redirect(url_for("report_list.my_reports_page"))

    return render_template(
        "myreport/my_report_detail.html",
        report=report
    )


@report_list_bp.route("/<int:report_id>/edit", methods=["GET"])
def edit_report_page(report_id):

    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    report = ReportService.get_my_report_detail(user_id, report_id)

    if not report:
        return redirect(url_for("report_list.my_reports_page"))

    return render_template(
        "myreport/my_report_edit.html",
        report=report
    )

@report_list_bp.route("/<int:report_id>/update", methods=["POST"])
def update_report(report_id):
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    try:
        title = request.form.get("title")
        location_text = request.form.get("location_text")
        content = request.form.get("content")
        new_file = request.files.get("new_file")

        result = ReportService.update_my_report(
            user_id=user_id,
            report_id=report_id,
            title=title,
            location_text=location_text,
            content=content,
            new_file=new_file
        )

        if result:
            flash("신고가 수정되었습니다.", "success")
        else:
            flash("수정할 수 없는 신고입니다.", "error")

        return redirect(url_for("report_list.edit_report_page", report_id=report_id))

    except Exception as e:
        print("수정 오류:", e)
        flash("수정 중 오류가 발생했습니다.", "error")
        return redirect(url_for("report_list.edit_report_page", report_id=report_id))

@report_list_bp.route("/<int:report_id>/delete", methods=["POST"])
def delete_report(report_id):

    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    return redirect(url_for("report_list.my_reports_page"))