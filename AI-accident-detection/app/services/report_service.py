from app.repositories.report_repository import ReportRepository


class ReportService:
    @staticmethod
    def get_my_reports(user_id):
        reports = ReportRepository.find_my_reports(user_id)

        result = []
        for report in reports:
            result.append({
                "id": report.id,
                "title": report.title,
                "content": report.content,
                "report_type": report.report_type,
                "location_text": report.location_text,
                "risk_level": report.risk_level,
                "status": report.status,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else None
            })

        return result
