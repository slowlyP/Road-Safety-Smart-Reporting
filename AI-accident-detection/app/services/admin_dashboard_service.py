"""
관리자 대시보드 서비스

역할
- 관리자 대시보드 통계 데이터 조회
"""

from sqlalchemy import func

from app.extensions import db
from app.models.user_model import User
from app.models.report_model import Report


class AdminDashboardService:

    def get_dashboard_stats(self):
        """
        관리자 대시보드 통계 조회
        """

        # 총 회원 수
        total_users = (
            db.session.query(func.count(User.id))
            .scalar()
        )

        # 총 신고 수
        total_reports = (
            db.session.query(func.count(Report.id))
            .filter(Report.deleted_at.is_(None))
            .scalar()
        )

        # 위험도 통계
        risk_stats = (
            db.session.query(
                Report.risk_level,
                func.count(Report.id)
            )
            .filter(Report.deleted_at.is_(None))
            .group_by(Report.risk_level)
            .all()
        )

        risk_result = {r[0]: r[1] for r in risk_stats}

        # 상태 통계
        status_stats = (
            db.session.query(
                Report.status,
                func.count(Report.id)
            )
            .filter(Report.deleted_at.is_(None))
            .group_by(Report.status)
            .all()
        )

        status_result = {s[0]: s[1] for s in status_stats}

        # 최근 신고
        recent_reports = (
            Report.query
            .filter(Report.deleted_at.is_(None))
            .order_by(Report.created_at.desc())
            .limit(5)
            .all()
        )

        recent_result = []

        for r in recent_reports:
            recent_result.append({
                "id": r.id,
                "title": r.title,
                "risk_level": r.risk_level,
                "status": r.status,
                "created_at": r.created_at
            })

        return {
            "total_users": total_users,
            "total_reports": total_reports,
            "risk_stats": risk_result,
            "status_stats": status_result,
            "recent_reports": recent_result
        }