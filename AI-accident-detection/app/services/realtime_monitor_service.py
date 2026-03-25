from datetime import datetime

from app.repositories.realtime_monitor_repository import RealtimeMonitorRepository


class RealtimeMonitorService:
    """
    탐지 현황 독립 페이지용 서비스
    """

    @staticmethod
    def _safe_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _format_datetime(dt):
        if not dt:
            return "-"
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _time_ago(dt):
        if not dt:
            return "-"

        now = datetime.now()
        diff = now - dt
        total_seconds = int(diff.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}초 전"

        minutes = total_seconds // 60
        if minutes < 60:
            return f"{minutes}분 전"

        hours = minutes // 60
        if hours < 24:
            return f"{hours}시간 전"

        days = hours // 24
        return f"{days}일 전"

    @staticmethod
    def get_summary_cards():
        """
        상단 카드 데이터
        """
        return RealtimeMonitorRepository.get_summary_data()

    @staticmethod
    def get_map_points():
        """
        지도 마커용 데이터 가공
        """
        rows = RealtimeMonitorRepository.get_map_points()

        result = []
        seen_report_ids = set()

        for row in rows:
            # detection outer join 으로 report가 중복될 수 있으니 1건만 사용
            if row.report_id in seen_report_ids:
                continue
            seen_report_ids.add(row.report_id)

            result.append({
                "report_id": row.report_id,
                "title": row.title or "제목 없음",
                "location_text": row.location_text or "위치 정보 없음",
                "latitude": RealtimeMonitorService._safe_float(row.latitude),
                "longitude": RealtimeMonitorService._safe_float(row.longitude),
                "risk_level": row.risk_level or "주의",
                "status": row.status or "-",
                "detected_label": row.detected_label or "미확인",
                "confidence": round(RealtimeMonitorService._safe_float(row.confidence), 2),
                "created_at": RealtimeMonitorService._format_datetime(row.created_at),
                "time_ago": RealtimeMonitorService._time_ago(row.created_at)
            })

        return result

    @staticmethod
    def get_recent_risk_list(limit=20):
        """
        우측/하단 리스트용 데이터 가공
        """
        rows = RealtimeMonitorRepository.get_recent_risk_list(limit=limit)

        result = []
        seen_report_ids = set()

        for row in rows:
            if row.report_id in seen_report_ids:
                continue
            seen_report_ids.add(row.report_id)

            result.append({
                "report_id": row.report_id,
                "title": row.title or "제목 없음",
                "location_text": row.location_text or "위치 정보 없음",
                "risk_level": row.risk_level or "주의",
                "status": row.status or "-",
                "detected_label": row.detected_label or "미확인",
                "confidence": round(RealtimeMonitorService._safe_float(row.confidence), 2),
                "created_at": RealtimeMonitorService._format_datetime(row.created_at),
                "time_ago": RealtimeMonitorService._time_ago(row.created_at)
            })

        return result