"""
관리자 대시보드 라우트
"""

from flask import Blueprint, render_template

from app.services.admin_dashboard_service import AdminDashboardService


admin_dashboard_bp = Blueprint(
    "admin_dashboard",
    __name__,
    url_prefix="/admin/dashboard"
)


@admin_dashboard_bp.route("/", methods=["GET"])
def dashboard():
    """
    관리자 대시보드 페이지
    """

    service = AdminDashboardService()

    stats = service.get_dashboard_stats()

    return render_template(
        "admin/dashboard.html",
        stats=stats
    )