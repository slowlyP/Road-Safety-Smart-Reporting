from app.models import Report, ReportFile
from app.extensions import db


class ReportRepository:

    # 🔹 내 신고 목록 조회
    @staticmethod
    def find_my_reports(user_id):
        return Report.query.filter_by(user_id=user_id)\
            .order_by(Report.created_at.desc())\
            .all()

    # 🔹 신고 상세 조회
    @staticmethod
    def find_my_report_detail(user_id, report_id):
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()

        if not report:
            return None, None

        report_file = ReportFile.query.filter_by(
            report_id=report.id,
            is_active=1
        ).first()

        return report, report_file

    @staticmethod
    def find_active_file_by_report_id(report_id):
        return ReportFile.query.filter_by(
            report_id=report_id,
            is_active=1
        ).first()

    @staticmethod
    def create_report_file(report_id, file_path, file_type):
        report_file = ReportFile(
            report_id=report_id,
            file_path=file_path,
            file_type=file_type
        )
        db.session.add(report_file)
        return report_file

    @staticmethod
    def commit():
        db.session.commit()