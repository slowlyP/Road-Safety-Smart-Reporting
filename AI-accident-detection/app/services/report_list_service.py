import os
from uuid import uuid4
from werkzeug.utils import secure_filename
from app.repositories.report_repository import ReportRepository


class ReportService:
    @staticmethod
    def get_my_reports(user_id):                                        # 🔹 내 신고 목록 조회
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

    @staticmethod
    def get_my_report_detail(user_id, report_id):                        # 🔹 내 신고 상세 조회
        report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)
        if not report:
            return None

        file_type = None
        file_url = None
        has_detection = False

        if report_file and report_file.file_path:
            file_type = report_file.file_type
            file_url = "/" + report_file.file_path.replace("\\", "/")
            has_detection = ReportRepository.has_detection_by_file_id(report_file.id)

        return {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "report_type": report.report_type,
            "location_text": report.location_text,
            "status": report.status,
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "-",
            "file_type": file_type,
            "file_url": file_url,
            "has_detection": has_detection
        }

    @staticmethod                                                        # 🔹 내 신고 수정
    def update_my_report(user_id, report_id, title, location_text, content, new_file, delete_file):
        report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)

        if not report:
            return False

        if report.status != "접수":
            return False

        report.title = title
        report.location_text = location_text
        report.content = content

        # 기존 파일 삭제 요청 처리
        if delete_file == "Y" and report_file:
            has_detection = ReportRepository.has_detection_by_file_id(report_file.id)

            # 분석 이력이 있으면 파일 삭제 불가
            if has_detection:
                return False

            old_file_path = report_file.file_path

            if old_file_path and os.path.exists(old_file_path):
                os.remove(old_file_path)

            ReportRepository.deactivate_report_file(report_file)
            report_file = None

        # 새 파일 업로드 처리
        if new_file and new_file.filename:
            upload_dir = "static/uploads"
            os.makedirs(upload_dir, exist_ok=True)

            original_name = secure_filename(new_file.filename)
            ext = os.path.splitext(original_name)[1]
            stored_name = f"{uuid4().hex}{ext}"
            save_path = os.path.join(upload_dir, stored_name)

            new_file.save(save_path)

            relative_path = save_path.replace("\\", "/")
            file_size = os.path.getsize(save_path)

            if new_file.mimetype and new_file.mimetype.startswith("image"):
                saved_file_type = "이미지"
            elif new_file.mimetype and new_file.mimetype.startswith("video"):
                saved_file_type = "영상"
            else:
                if os.path.exists(save_path):
                    os.remove(save_path)
                return False

            old_file_path = None

            if report_file and report_file.file_path:
                has_detection = ReportRepository.has_detection_by_file_id(report_file.id)

                # 분석 이력이 있으면 기존 파일 교체 불가
                if has_detection:
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    return False

                old_file_path = report_file.file_path
                ReportRepository.deactivate_report_file(report_file)

            ReportRepository.create_report_file(
                report_id=report.id,
                original_name=original_name,
                stored_name=stored_name,
                file_path=relative_path,
                file_type=saved_file_type,
                file_size=file_size
            )

            if old_file_path and os.path.exists(old_file_path):
                os.remove(old_file_path)

        ReportRepository.commit()
        return True

    @staticmethod
    def delete_my_report(user_id, report_id):                         # 🔹 내 신고 삭제
        report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)

        if not report:
            return False

        if report.status != "접수":
            return False

        # 첨부파일은 분석 이력 여부와 관계없이 비활성화 처리
        if report_file:
            has_detection = ReportRepository.has_detection_by_file_id(report_file.id)

            if has_detection:
                ReportRepository.deactivate_report_file(report_file)
            else:
                if report_file.file_path and os.path.exists(report_file.file_path):
                    os.remove(report_file.file_path)

                ReportRepository.deactivate_report_file(report_file)

        # 신고는 소프트 삭제 처리
        ReportRepository.delete_report(report)
        ReportRepository.commit()

        return True