from flask import Blueprint, jsonify, render_template, current_app, request

from app.services.realtime_monitor_service import RealtimeMonitorService

realtime_monitor_bp = Blueprint(
    "realtime_monitor",
    __name__,
    url_prefix="/realtime-monitor"
)


def _get_days_param(default=180):
    return request.args.get("days", default=default, type=int)


def _get_limit_param(default):
    return request.args.get("limit", default=default, type=int)


@realtime_monitor_bp.route("", methods=["GET"])
def realtime_monitor_page():
    google_maps_api_key = current_app.config.get("GOOGLE_MAPS_API_KEY", "")
    days = _get_days_param(default=180)

    summary = RealtimeMonitorService.get_summary_cards(days=days)
    risk_list = RealtimeMonitorService.get_recent_risk_list(limit=20, days=days)

    return render_template(
        "main/realtime_monitor.html",
        google_maps_api_key=google_maps_api_key,
        summary=summary,
        risk_list=risk_list,
        default_days=days
    )


@realtime_monitor_bp.route("/summary", methods=["GET"])
def get_summary():
    days = _get_days_param(default=180)
    data = RealtimeMonitorService.get_summary_cards(days=days)

    return jsonify({
        "success": True,
        "data": data,
        "days": days
    }), 200


@realtime_monitor_bp.route("/map-points", methods=["GET"])
def get_map_points():
    days = _get_days_param(default=180)
    limit = _get_limit_param(default=300)

    items = RealtimeMonitorService.get_map_points(limit=20, days=days)

    return jsonify({
        "success": True,
        "items": items,
        "days": days,
        "limit": limit
    }), 200


@realtime_monitor_bp.route("/risk-list", methods=["GET"])
def get_risk_list():
    days = _get_days_param(default=180)
    limit = _get_limit_param(default=20)

    items = RealtimeMonitorService.get_recent_risk_list(limit=20, days=days)

    return jsonify({
        "success": True,
        "items": items,
        "days": days,
        "limit": limit
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