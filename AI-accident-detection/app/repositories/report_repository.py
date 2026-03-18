from app.models.report_model import Report


class ReportRepository:
    @staticmethod
    def find_my_reports(user_id):
        return (
            Report.query
            .filter(
                Report.user_id == user_id,
                Report.deleted_at.is_(None)
            )
            .order_by(Report.created_at.desc())
            .all()
        )