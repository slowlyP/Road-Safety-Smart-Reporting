from flask import Blueprint, jsonify, render_template, current_app

from app.services.realtime_monitor_service import RealtimeMonitorService

realtime_monitor_bp = Blueprint(
    "realtime_monitor",
    __name__,
    url_prefix="/realtime-monitor"
)


@realtime_monitor_bp.route("", methods=["GET"])
def realtime_monitor_page():
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
    data = RealtimeMonitorService.get_summary_cards()

    return jsonify({
        "success": True,
        "data": data
    }), 200


@realtime_monitor_bp.route("/map-points", methods=["GET"])
def get_map_points():
    items = RealtimeMonitorService.get_map_points()

    return jsonify({
        "success": True,
        "items": items
    }), 200


@realtime_monitor_bp.route("/risk-list", methods=["GET"])
def get_risk_list():
    items = RealtimeMonitorService.get_recent_risk_list(limit=20)

    return jsonify({
        "success": True,
        "items": items
    }), 200


@realtime_monitor_bp.route("/detail/<int:report_id>", methods=["GET"])
def get_report_detail(report_id):
    detail = RealtimeMonitorService.get_report_detail(report_id)

    if not detail:
        return jsonify({
            "success": False,
            "message": "해당 사고 상세 정보를 찾을 수 없습니다."
        }), 404

    return jsonify({
        "success": True,
        "data": detail
    }), 200