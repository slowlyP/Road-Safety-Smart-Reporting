from flask import Blueprint, render_template, session, redirect, url_for, flash

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

    # 아직 실제 detection 데이터 연결 전
    dummy_logs = []

    return render_template(
        "admin/ai/list.html",
        logs=dummy_logs
    )


@admin_ai_bp.route("/<int:detection_id>", methods=["GET"])
def detail(detection_id):
    """
    AI 탐지 상세 페이지
    """
    check = _check_admin()
    if check:
        return check

    # 아직 실제 상세 데이터 연결 전
    detection = None

    return render_template(
        "admin/ai/detail.html",
        detection=detection
    )


@admin_ai_bp.route("/summary", methods=["GET"])
def summary():
    """
    AI 요약 리포트 페이지
    """
    check = _check_admin()
    if check:
        return check

    summary_data = {
        "total_detections": 0,
        "high_confidence_count": 0,
        "low_confidence_count": 0,
    }

    return render_template(
        "admin/ai/summary.html",
        summary_data=summary_data
    )