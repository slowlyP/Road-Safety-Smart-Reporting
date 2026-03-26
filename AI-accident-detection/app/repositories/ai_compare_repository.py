from app.extensions import db
from app.models import AiCompareRun, AiCompareResult


class AiCompareRepository:

    # =========================
    # Compare Run
    # =========================

    @staticmethod
    def create_compare_run(report_id, file_id, requested_by, source_type):
        run = AiCompareRun(
            report_id=report_id,
            file_id=file_id,
            requested_by=requested_by,
            source_type=source_type,
            status="대기"
        )
        db.session.add(run)
        db.session.commit()
        return run

    @staticmethod
    def update_run_status(run_id, status):
        run = AiCompareRun.query.get(run_id)
        if not run:
            return None

        run.status = status
        db.session.commit()
        return run

    @staticmethod
    def get_run_by_id(run_id):
        return AiCompareRun.query.get(run_id)

    @staticmethod
    def get_runs_by_report(report_id):
        return (
            AiCompareRun.query
            .filter_by(report_id=report_id)
            .order_by(AiCompareRun.created_at.desc())
            .all()
        )

    @staticmethod
    def get_latest_run(report_id):
        return (
            AiCompareRun.query
            .filter_by(report_id=report_id)
            .order_by(AiCompareRun.created_at.desc())
            .first()
        )

    # =========================
    # Compare Result
    # =========================

    @staticmethod
    def create_result(
        compare_run_id,
        model_name,
        optimizer_name=None,
        model_version=None,
        total_detections=0,
        avg_confidence=None,
        max_confidence=None,
        processing_time=None,
        result_image_path=None,
        result_json=None,
        status="완료",
        error_message=None
    ):
        result = AiCompareResult(
            compare_run_id=compare_run_id,
            model_name=model_name,
            optimizer_name=optimizer_name,
            model_version=model_version,
            total_detections=total_detections,
            avg_confidence=avg_confidence,
            max_confidence=max_confidence,
            processing_time=processing_time,
            result_image_path=result_image_path,
            result_json=result_json,
            status=status,
            error_message=error_message
        )
        db.session.add(result)
        db.session.commit()
        return result

    @staticmethod
    def get_results_by_run(compare_run_id):
        return (
            AiCompareResult.query
            .filter_by(compare_run_id=compare_run_id)
            .order_by(AiCompareResult.id.asc())
            .all()
        )

    @staticmethod
    def delete_results_by_run(compare_run_id):
        AiCompareResult.query.filter_by(compare_run_id=compare_run_id).delete()
        db.session.commit()