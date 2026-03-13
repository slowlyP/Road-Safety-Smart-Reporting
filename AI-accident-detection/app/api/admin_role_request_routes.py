from flask import Blueprint, render_template, session

admin_role_request_bp = Blueprint(
    "admin_role_request",
    __name__,
    url_prefix="/admin/role-requests"
)


def is_admin():
    return session.get("role") == "admin"


@admin_role_request_bp.route("/", methods=["GET"])
def role_request_list_page():
    if not is_admin():
        return "관리자만 접근 가능합니다.", 403

    return render_template("admin/role_request_list.html")