from flask import Blueprint, session, render_template, redirect, url_for, flash, request
from app.services.report_list_service import ReportService
from app.common.response import success_response, error_response
from app.repositories.user_repository import UserRepository

# 신고 목록 관련 블루프린트
report_list_bp = Blueprint("report_list", __name__, url_prefix="/reports")


@report_list_bp.route("/my-page", methods=["GET"])
def my_reports_page():  # 내 신고 목록 페이지 + 사용자 정보 화면 렌더링
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    db_user = UserRepository.get_user_by_id(user_id)

    user = {
        "name": db_user.name,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "created_at": db_user.created_at
    }

    return render_template("myreport/my_reports.html", user=user)


@report_list_bp.route("/my", methods=["GET"])
def get_my_reports():  # 내 신고 목록 페이징 조회 API
    try:
        user_id = session.get("user_id")
        if not user_id:
            return error_response(
                message="로그인이 필요합니다.",
                status_code=401
            )

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 5, type=int)

        reports = ReportService.get_my_reports_paginated(
            user_id=user_id,
            page=page,
            per_page=per_page
        )

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
def my_report_detail_page(report_id):  # 내 신고 상세 페이지 렌더링
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
def edit_report_page(report_id):  # 내 신고 수정 페이지 렌더링
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
def update_report(report_id):  # 내 신고 수정 요청 처리
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    try:
        title = request.form.get("title")
        location_text = request.form.get("location_text")
        content = request.form.get("content")
        new_file = request.files.get("new_file")
        delete_file = request.form.get("delete_file", "N")

        result = ReportService.update_my_report(
            user_id=user_id,
            report_id=report_id,
            title=title,
            location_text=location_text,
            content=content,
            new_file=new_file,
            delete_file=delete_file
        )

        if isinstance(result, tuple) and len(result) >= 1:
            success = bool(result[0])
            message = result[1] if len(result) >= 2 else ""
        else:
            success = bool(result)
            message = ""

        if success:
            flash(message or "신고가 수정되었습니다.", "success")
            return redirect(url_for("report_list.my_report_detail_page", report_id=report_id))

        flash(message or "수정 중 오류가 발생했습니다.", "error")
        return redirect(url_for("report_list.edit_report_page", report_id=report_id))

    except Exception as e:
        print("수정 오류:", e)
        flash("수정 중 오류가 발생했습니다.", "error")
        return redirect(url_for("report_list.edit_report_page", report_id=report_id))


@report_list_bp.route("/<int:report_id>/delete", methods=["POST"])
def delete_report(report_id):  # 내 신고 삭제 요청 처리
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    try:
        result = ReportService.delete_my_report(user_id, report_id)

        if result:
            flash("삭제되었습니다.", "success")
        else:
            flash("삭제할 수 없는 신고입니다.", "error")

    except Exception as e:
        print("삭제 오류:", e)
        flash("삭제 중 오류가 발생했습니다.", "error")

    return redirect(url_for("report_list.my_reports_page"))