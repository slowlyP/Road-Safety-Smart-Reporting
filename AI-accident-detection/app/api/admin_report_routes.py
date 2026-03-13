"""
관리자 신고 관리 라우트

이 파일은 관리자 신고 관련 요청을 처리한다.

주요 기능
- GET /admin/reports/ : 관리자 신고 목록 페이지
- GET /admin/reports/<report_id> : 관리자 신고 상세 페이지
- POST /admin/reports/<report_id>/status : 관리자 신고 상태 변경
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.admin_report_service import AdminReportService

admin_report_bp = Blueprint(
    "admin_report",
    __name__,
    url_prefix="/admin/reports"
)


@admin_report_bp.route("/", methods=["GET"])
def report_list():
    """
    관리자 신고 목록 페이지
    """
    service = AdminReportService()
    reports = service.get_report_list()

    return render_template(
        "admin/report_list.html",
        reports=reports
    )


@admin_report_bp.route("/<int:report_id>", methods=["GET"])
def report_detail(report_id):
    """
    관리자 신고 상세 페이지
    """
    service = AdminReportService()
    report = service.get_report_detail(report_id)

    return render_template(
        "admin/report_detail.html",
        report=report
    )


@admin_report_bp.route("/<int:report_id>/status", methods=["POST"])
def update_report_status(report_id):
    """
    관리자 신고 상태 변경
    """
    status = request.form.get("status")
    memo = request.form.get("memo")

    valid_status = ["접수", "확인중", "처리완료", "오탐"]

    if status not in valid_status:
        flash("잘못된 상태 값입니다.", "error")
        return redirect(url_for("admin_report.report_detail", report_id=report_id))

    changed_by = session.get("user_id")

    service = AdminReportService()

    updated = service.update_report_status(
        report_id=report_id,
        status=status,
        changed_by=changed_by,
        memo=memo
    )

    if updated is None:
        flash("기존 상태와 동일합니다.", "warning")
        return redirect(url_for("admin_report.report_detail", report_id=report_id))

    flash("신고 상태가 변경되었습니다.", "success")
    return redirect(url_for("admin_report.report_detail", report_id=report_id))