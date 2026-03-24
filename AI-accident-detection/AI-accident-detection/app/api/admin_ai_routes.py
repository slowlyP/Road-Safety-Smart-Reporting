from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.services.admin_ai_service import AdminAIService

admin_ai_bp = Blueprint(
    "admin_ai",
    __name__,
    url_prefix="/admin/ai"
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


@admin_ai_bp.route("/", methods=["GET"])
def list():
    """
    AI 탐지 로그 목록 페이지
    """
    check = _check_admin()
    if check:
        return check

    page = request.args.get("page", 1, type=int)
    label = request.args.get("label", "").strip()
    status = request.args.get("status", "").strip()
    min_conf = request.args.get("min_conf", type=float)
    max_conf = request.args.get("max_conf", type=float)

    data = AdminAIService.get_detection_list(
        page=page,
        per_page=10,
        label=label if label else None,
        min_conf=min_conf,
        max_conf=max_conf,
        status=status if status else None
    )

    label_options = [
        {"value": "box", "label": "박스형"},
        {"value": "bag", "label": "봉투류"},
        {"value": "tire", "label": "타이어"},
        {"value": "rock", "label": "돌 / 콘크리트"},
        {"value": "debris", "label": "파편"}
    ]

    return render_template(
        "admin/ai/list.html",
        logs=data["items"],
        pagination=data["pagination"],
        label_options=label_options,
        filters={
            "label": label,
            "status": status,
            "min_conf": min_conf,
            "max_conf": max_conf
        }
    )


@admin_ai_bp.route("/<int:detection_id>", methods=["GET"])
def detail(detection_id):
    """
    AI 탐지 상세 페이지
    """
    check = _check_admin()
    if check:
        return check

    data = AdminAIService.get_detection_detail(detection_id)

    if not data:
        flash("해당 AI 탐지 데이터를 찾을 수 없습니다.", "warning")
        return redirect(url_for("admin_ai.list"))

    return render_template(
        "admin/ai/detail.html",
        detection=data["detection"],
        report=data["report"],
        file=data["file"],
        is_false_positive=data["is_false_positive"]
    )


@admin_ai_bp.route("/summary", methods=["GET"])
def summary():
    """
    AI 요약 리포트 페이지
    """
    check = _check_admin()
    if check:
        return check

    data = AdminAIService.get_summary_page_data()

    return render_template(
        "admin/ai/summary.html",
        summary=data["summary"],
        label_stats=data["label_stats"],
        daily_trend=data["daily_trend"],
        confidence_distribution=data["confidence_distribution"],
        recent_false_positives=data["recent_false_positives"]
    )