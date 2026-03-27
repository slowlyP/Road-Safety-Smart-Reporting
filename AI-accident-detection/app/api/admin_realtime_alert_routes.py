from flask import Blueprint, jsonify, render_template

from app.common.decorators import login_required, admin_required
from app.services.realtime_alert_service import RealtimeAlertService


admin_realtime_alert_bp = Blueprint(
    "admin_realtime_alert",
    __name__,
    url_prefix="/admin/realtime-alerts"
)


@admin_realtime_alert_bp.route("", methods=["GET"])
@login_required
@admin_required
def realtime_alert_page():
    """
    관리자 - 실시간 위험 알림 페이지
    """
    alerts = RealtimeAlertService.get_realtime_alerts(limit=50)
    unread_count = RealtimeAlertService.get_unread_count()

    return render_template(
        "admin/realtime_alert/list.html",
        alerts=alerts,
        unread_count=unread_count
    )


@admin_realtime_alert_bp.route("/list", methods=["GET"])
@login_required
@admin_required
def get_realtime_alerts():
    """
    위험/긴급 알림 목록 조회
    - JS 초기 목록 확인
    - 필요 시 수동 새로고침 용도
    """
    alerts = RealtimeAlertService.get_realtime_alerts(limit=50)
    unread_count = RealtimeAlertService.get_unread_count()

    return jsonify({
        "success": True,
        "alerts": alerts,
        "unread_count": unread_count
    }), 200


@admin_realtime_alert_bp.route("/unread-count", methods=["GET"])
@login_required
@admin_required
def get_unread_count():
    """
    미확인 위험/긴급 알림 개수 조회
    - 사이드바 badge 숫자 갱신용
    """
    unread_count = RealtimeAlertService.get_unread_count()

    return jsonify({
        "success": True,
        "unread_count": unread_count
    }), 200


@admin_realtime_alert_bp.route("/<int:alert_id>/read", methods=["PATCH", "POST"])
@login_required
@admin_required
def mark_alert_as_read(alert_id):
    """
    특정 알림 읽음 처리
    """
    alert = RealtimeAlertService.mark_as_read(alert_id)

    if not alert:
        return jsonify({
            "success": False,
            "message": "알림을 찾을 수 없습니다."
        }), 404

    unread_count = RealtimeAlertService.get_unread_count()

    return jsonify({
        "success": True,
        "message": "읽음 처리 완료",
        "alert_id": alert_id,
        "unread_count": unread_count
    }), 200


@admin_realtime_alert_bp.route("/read-all", methods=["PATCH", "POST"])
@login_required
@admin_required
def mark_all_alerts_as_read():
    """
    전체 위험/긴급 알림 읽음 처리
    """
    updated_count = RealtimeAlertService.mark_all_as_read()
    unread_count = RealtimeAlertService.get_unread_count()

    return jsonify({
        "success": True,
        "message": f"{updated_count}건 읽음 처리 완료",
        "updated_count": updated_count,
        "unread_count": unread_count
    }), 200