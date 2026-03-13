"""
관리자 신고 관리 서비스

역할
- 관리자 신고 목록 조회
- 관리자 신고 상세 조회
- 관리자 신고 상태 변경
"""

from datetime import datetime

from app.extensions import db
from app.models.report_model import Report
from app.models.report_status_log_model import ReportStatusLog


class AdminReportService:

    def get_report_list(self):
        """
        관리자 신고 목록 조회
        """
        reports = (
            Report.query
            .filter(Report.deleted_at.is_(None))
            .order_by(Report.created_at.desc())
            .all()
        )

        result = []

        for r in reports:
            result.append({
                "id": r.id,
                "title": r.title,
                "risk_level": r.risk_level,
                "status": r.status,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""
            })

        return result

    def get_report_detail(self, report_id):
        """
        관리자 신고 상세 조회
        """
        report = Report.query.get_or_404(report_id)

        return {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "risk_level": report.risk_level,
            "status": report.status,
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else ""
        }

    def update_report_status(self, report_id, status, changed_by=None, memo=None):
        """
        관리자 신고 상태 변경
        """
        report = Report.query.get_or_404(report_id)

        old_status = report.status

        if old_status == status:
            return None

        report.status = status
        report.updated_at = datetime.now()

        status_log = ReportStatusLog(
            report_id=report.id,
            old_status=old_status,
            new_status=status,
            changed_by=changed_by,
            memo=memo,
            created_at=datetime.now()
        )

        db.session.add(status_log)
        db.session.commit()

        return report