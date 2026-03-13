"""
관리자 회원 관리 라우트
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.services.admin_user_service import AdminUserService


admin_user_bp = Blueprint(
    "admin_user",
    __name__,
    url_prefix="/admin/users"
)


@admin_user_bp.route("/")
def user_list():
    """
    관리자 회원 목록 페이지
    """

    service = AdminUserService()

    users = service.get_user_list()

    return render_template(
        "admin/user_list.html",
        users=users
    )


@admin_user_bp.route("/<int:user_id>/role", methods=["POST"])
def update_user_role(user_id):
    """
    회원 권한 변경
    """

    role = request.form.get("role")

    service = AdminUserService()

    service.update_user_role(user_id, role)

    flash("회원 권한이 변경되었습니다.", "success")

    return redirect(url_for("admin_user.user_list"))


@admin_user_bp.route("/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    """
    관리자 회원 삭제 (soft delete)

    처리 흐름
    1. 관리자 회원 삭제 요청
    2. AdminUserService 호출
    3. deleted_at 업데이트
    4. 회원 목록 페이지 이동
    """

    service = AdminUserService()

    service.delete_user(user_id)

    flash("회원이 삭제되었습니다.", "success")

    return redirect(url_for("admin_user.user_list"))