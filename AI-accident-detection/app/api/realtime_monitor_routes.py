from flask import Blueprint, jsonify, render_template, current_app

from app.services.realtime_monitor_service import RealtimeMonitorService

realtime_monitor_bp = Blueprint(
    "realtime_monitor",
    __name__,
    url_prefix="/realtime-monitor"
)


@realtime_monitor_bp.route("", methods=["GET"])
def realtime_monitor_page():
    """
    탐지 현황 메인 페이지
    - 프론트 상단 메뉴에서 진입하는 독립 페이지
    """
    google_maps_api_key = current_app.config.get("GOOGLE_MAPS_API_KEY", "")
    summary = RealtimeMonitorService.get_summary_cards()
    risk_list = RealtimeMonitorService.get_recent_risk_list(limit=20)

    return render_template(
        "main/realtime_monitor.html",
        google_maps_api_key=google_maps_api_key,
        summary=summary,
        risk_list=risk_list
    )


@realtime_monitor_bp.route("/summary", methods=["GET"])
def get_summary():
    """
    상단 요약 카드 데이터 API
    """
    data = RealtimeMonitorService.get_summary_cards()

    return jsonify({
        "success": True,
        "data": data
    }), 200


@realtime_monitor_bp.route("/map-points", methods=["GET"])
def get_map_points():
    """
    지도 마커 데이터 API
    """
    items = RealtimeMonitorService.get_map_points()

    return jsonify({
        "success": True,
        "items": items
    }), 200


@realtime_monitor_bp.route("/risk-list", methods=["GET"])
def get_risk_list():
    """
    실시간 위험 리스트 데이터 API
    """
    items = RealtimeMonitorService.get_recent_risk_list(limit=20)

    return jsonify({
        "success": True,
        "items": items
    }), 200