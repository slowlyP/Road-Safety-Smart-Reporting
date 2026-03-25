from datetime import datetime, timedelta

from sqlalchemy import func, case, distinct

from app.extensions import db
from app.models import Report, Detection


class RealtimeMonitorRepository:
    """
    탐지 현황(독립 페이지) 전용 Repository

    역할
    - 상단 요약 카드용 통계 조회
    - 지도 마커용 데이터 조회
    - 실시간 위험 리스트 조회
    """

    TARGET_RISK_LEVELS = ["주의", "위험", "긴급"]
    ACTIVE_STATUSES = ["접수", "확인중"]

    @staticmethod
    def count_current_risk_zones():
        """
        현재 위험 구간 수
        - 접수/확인중 상태
        - 주의/위험/긴급 위험도
        - location_text 기준 중복 제거
        """
        return (
            db.session.query(func.count(distinct(Report.location_text)))
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(RealtimeMonitorRepository.ACTIVE_STATUSES))
            .filter(Report.risk_level.in_(RealtimeMonitorRepository.TARGET_RISK_LEVELS))
            .filter(Report.location_text.isnot(None))
            .filter(Report.location_text != "")
            .scalar()
        ) or 0

    @staticmethod
    def count_today_reports():
        """
        오늘 접수 건수
        """
        today = datetime.now().date()

        return (
            db.session.query(func.count(Report.id))
            .filter(Report.deleted_at.is_(None))
            .filter(func.date(Report.created_at) == today)
            .scalar()
        ) or 0

    @staticmethod
    def count_emergency_last_24h():
        """
        최근 24시간 긴급 건수
        """
        since_time = datetime.now() - timedelta(hours=24)

        return (
            db.session.query(func.count(Report.id))
            .filter(Report.deleted_at.is_(None))
            .filter(Report.risk_level == "긴급")
            .filter(Report.created_at >= since_time)
            .scalar()
        ) or 0

    @staticmethod
    def count_hotspots(days=7, min_count=2):
        """
        사고 다발 구간 수
        - 최근 days일 동안
        - 같은 location_text 에서 min_count 이상 발생
        """
        since_time = datetime.now() - timedelta(days=days)

        rows = (
            db.session.query(
                Report.location_text,
                func.count(Report.id).label("cnt")
            )
            .filter(Report.deleted_at.is_(None))
            .filter(Report.created_at >= since_time)
            .filter(Report.location_text.isnot(None))
            .filter(Report.location_text != "")
            .group_by(Report.location_text)
            .having(func.count(Report.id) >= min_count)
            .all()
        )

        return len(rows)

    @staticmethod
    def get_summary_data():
        """
        상단 카드용 종합 데이터
        """
        return {
            "current_risk_zones": RealtimeMonitorRepository.count_current_risk_zones(),
            "today_reports": RealtimeMonitorRepository.count_today_reports(),
            "emergency_last_24h": RealtimeMonitorRepository.count_emergency_last_24h(),
            "hotspots": RealtimeMonitorRepository.count_hotspots(days=7, min_count=2)
        }

    @staticmethod
    def get_map_points(limit=300):
        """
        지도 마커용 데이터

        기준
        - deleted_at 없는 데이터
        - 좌표 존재
        - 현재 위험 상태(접수/확인중)
        - 위험도: 주의/위험/긴급
        """
        rows = (
            db.session.query(
                Report.id.label("report_id"),
                Report.title.label("title"),
                Report.location_text.label("location_text"),
                Report.latitude.label("latitude"),
                Report.longitude.label("longitude"),
                Report.risk_level.label("risk_level"),
                Report.status.label("status"),
                Report.created_at.label("created_at"),
                Detection.detected_label.label("detected_label"),
                Detection.confidence.label("confidence")
            )
            .outerjoin(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.status.in_(RealtimeMonitorRepository.ACTIVE_STATUSES))
            .filter(Report.risk_level.in_(RealtimeMonitorRepository.TARGET_RISK_LEVELS))
            .filter(Report.latitude.isnot(None))
            .filter(Report.longitude.isnot(None))
            .order_by(Report.created_at.desc())
            .limit(limit)
            .all()
        )

        return rows

    @staticmethod
    def get_recent_risk_list(limit=20):
        """
        실시간 위험 리스트

        정렬
        - 긴급 > 위험 > 주의
        - 같은 위험도 내 최신순
        """
        risk_order = case(
            (Report.risk_level == "긴급", 3),
            (Report.risk_level == "위험", 2),
            (Report.risk_level == "주의", 1),
            else_=0
        )

        rows = (
            db.session.query(
                Report.id.label("report_id"),
                Report.title.label("title"),
                Report.location_text.label("location_text"),
                Report.risk_level.label("risk_level"),
                Report.status.label("status"),
                Report.created_at.label("created_at"),
                Detection.detected_label.label("detected_label"),
                Detection.confidence.label("confidence")
            )
            .outerjoin(Detection, Detection.report_id == Report.id)
            .filter(Report.deleted_at.is_(None))
            .filter(Report.risk_level.in_(RealtimeMonitorRepository.TARGET_RISK_LEVELS))
            .order_by(risk_order.desc(), Report.created_at.desc())
            .limit(limit)
            .all()
        )

        return rows