from flask import Blueprint, render_template, session

admin_ai_bp = Blueprint(
    "admin_ai",
    __name__,
    url_prefix="/admin/ai-analysis"
)


def is_admin():
    return session.get("role") == "admin"


@admin_ai_bp.route("/", methods=["GET"])
def ai_analysis_list_page():
    """
    관리자 AI 분석 목록 페이지
    """
    if not is_admin():
        return "관리자만 접근 가능합니다.", 403

    return render_template("admin/ai_analysis_list.html")