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


def _check_admin():
    """
    관리자 접근 체크
    """
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("관리자만 접근할 수 있습니다.", "danger")
        return redirect(url_for("main.index"))

    return None


@admin_report_bp.route("/", methods=["GET"])
def report_list():
    """
    관리자 신고 목록 페이지
    - 페이징
    - 상태 필터
    - 위험도 필터
    - 검색
    """

    check = _check_admin()
    if check:
        return check

    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "", type=str)
    risk_level = request.args.get("risk_level", "", type=str)
    keyword = request.args.get("keyword", "", type=str)

    service = AdminReportService()

    try:
        result = service.get_report_list(
            page=page,
            per_page=10,
            status=status,
            risk_level=risk_level,
            keyword=keyword
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/reports/list.html",
        reports=result["reports"],
        pagination=result["pagination"],
        status=status,
        risk_level=risk_level,
        keyword=keyword
    )


@admin_report_bp.route("/<int:report_id>", methods=["GET"])
def report_detail(report_id):
    """
    관리자 신고 상세 페이지
    - 신고 기본 정보
    - 첨부 이미지 / 영상
    - AI 분석 결과
    - 상태 변경 이력
    """

    check = _check_admin()
    if check:
        return check

    service = AdminReportService()

    try:
        report_data = service.get_report_detail(report_id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("admin_report.report_list"))

    return render_template(
        "admin/reports/detail.html",
        report=report_data["report"],
        files=report_data.get("files", []),
        status_logs=report_data.get("status_logs", []),
        ai_analysis=report_data.get("ai_analysis")
    )


@admin_report_bp.route("/<int:report_id>/status", methods=["POST"])
def update_report_status(report_id):
    """
    관리자 신고 상태 변경
    """

    check = _check_admin()
    if check:
        return check

    new_status = request.form.get("status", "").strip()
    memo = request.form.get("memo", "").strip()
    admin_id = session.get("user_id")

    valid_status = ["접수", "확인중", "처리완료", "오탐"]

    if new_status not in valid_status:
        flash("잘못된 상태 값입니다.", "danger")
        return redirect(url_for("admin_report.report_detail", report_id=report_id))

    service = AdminReportService()

    try:
        updated = service.update_report_status(
            report_id=report_id,
            status=new_status,
            changed_by=admin_id,
            memo=memo
        )

        if updated is None:
            flash("기존 상태와 동일합니다.", "warning")
        else:
            flash("신고 상태가 변경되었습니다.", "success")

    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("admin_report.report_detail", report_id=report_id))