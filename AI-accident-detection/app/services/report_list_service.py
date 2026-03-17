import os
from uuid import uuid4
from werkzeug.utils import secure_filename
from app.repositories.report_repository import ReportRepository


class ReportService:
    @staticmethod  # 🔹 신고 목록 조회
    def get_my_reports(user_id):
        reports = ReportRepository.find_my_reports(user_id)

        if not reports:
            return []

        result = []

        for report in reports:
            report_file = ReportRepository.find_active_file_by_report_id(report.id)

            file_type = "일반"

            if report_file and report_file.file_type:
                file_type = report_file.file_type

            result.append({
                "id": report.id,
                "title": report.title,
                "content": report.content,
                "report_type": report.report_type,
                "location_text": report.location_text,
                "status": report.status,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "-",
                "file_type": file_type
            })

        return result

    @staticmethod  # 🔹 신고 상세 조회
    def get_my_report_detail(user_id, report_id):
        report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)

        if not report:
            return None

        file_type = None
        file_url = None

        if report_file and report_file.file_path:
            file_type = report_file.file_type
            file_url = "/" + report_file.file_path.replace("\\", "/")

        return {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "report_type": report.report_type,
            "location_text": report.location_text,
            "status": report.status,
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "-",
            "file_type": file_type,
            "file_url": file_url
        }

    @staticmethod  # 🔹 신고 수정
    def update_my_report(user_id, report_id, title, location_text, content, new_file):
        report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)

        if not report:
            return False

        if report.status != "접수":
            return False

        report.title = title
        report.location_text = location_text
        report.content = content

        if new_file and new_file.filename:
            upload_dir = "static/uploads"
            os.makedirs(upload_dir, exist_ok=True)

            original_name = secure_filename(new_file.filename)
            ext = os.path.splitext(original_name)[1]  # .png 추출

            unique_name = f"{uuid4().hex}{ext}"
            save_path = os.path.join(upload_dir, unique_name)

            new_file.save(save_path)

            relative_path = save_path.replace("\\", "/")

            saved_file_type = "기타"

            if new_file.mimetype:
                if new_file.mimetype.startswith("image"):
                    saved_file_type = "이미지"
                elif new_file.mimetype.startswith("video"):
                    saved_file_type = "영상"

            old_file_path = None

            if report_file and report_file.file_path:
                old_file_path = report_file.file_path

            if report_file:
                report_file.file_path = relative_path
                report_file.file_type = saved_file_type
            else:
                ReportRepository.create_report_file(
                    report_id=report.id,
                    file_path=relative_path,
                    file_type=saved_file_type
                )

            if old_file_path and old_file_path != relative_path:
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

        ReportRepository.commit()
        return True