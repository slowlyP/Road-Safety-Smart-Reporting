from datetime import datetime
import os
import uuid
import time
import traceback

from app.extensions import db
from app.models import Report, ReportFile
from app.repositories.ai_compare_repository import AiCompareRepository
from ai.inference.compare_inference import run_model_inference
from ai.utils.draw_bbox import draw_bboxes

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


class AdminAICompareService:
    """
    관리자 비교분석 서비스
    - 신고 기준 비교 실행
    - 비교 이력 조회
    - 특정 실행 결과 조회
    """

    MODEL_CONFIGS = [
        {
            "model_name": "YOLOv8",
            "optimizer_name": "SGD",
            "display_name": "YOLOv8 (SGD)",
            "model_version": "best_yolov8_sgd.pt",
        },
        {
            "model_name": "RT-DETR",
            "optimizer_name": "AdamW",
            "display_name": "RT-DETR (AdamW)",
            "model_version": "best_rtdetr_adamw.pt",
        },
        {
            "model_name": "YOLOv8-p2",
            "optimizer_name": None,
            "display_name": "YOLOv8-p2",
            "model_version": "best_yolov8_p2.pt",
        },
    ]

    @staticmethod
    def get_report(report_id):
        return Report.query.get(report_id)

    @staticmethod
    def get_active_file(report_id):
        return (
            ReportFile.query
            .filter_by(report_id=report_id, is_active=1)
            .first()
        )

    @classmethod
    def run_compare_analysis(cls, report_id, requested_by=None):
        report = cls.get_report(report_id)
        if not report:
            raise ValueError("신고 정보를 찾을 수 없습니다.")

        report_file = cls.get_active_file(report_id)
        if not report_file:
            raise ValueError("분석할 활성 파일이 없습니다.")

        source_type = report_file.file_type

        compare_run = AiCompareRepository.create_compare_run(
            report_id=report.id,
            file_id=report_file.id,
            requested_by=requested_by,
            source_type=source_type
        )

        compare_run.status = "진행중"
        compare_run.started_at = datetime.now()
        db.session.commit()

        success_count = 0
        fail_count = 0

        for model_config in cls.MODEL_CONFIGS:
            try:
                print("=" * 60)
                print("MODEL_NAME:", model_config["model_name"])
                print("MODEL_VERSION:", model_config["model_version"])

                result_data = cls.execute_model_analysis(
                    report=report,
                    report_file=report_file,
                    model_config=model_config
                )

                AiCompareRepository.create_result(
                    compare_run_id=compare_run.id,
                    model_name=result_data["model_name"],
                    optimizer_name=result_data.get("optimizer_name"),
                    model_version=result_data.get("model_version"),
                    total_detections=result_data.get("total_detections", 0),
                    avg_confidence=result_data.get("avg_confidence"),
                    max_confidence=result_data.get("max_confidence"),
                    processing_time=result_data.get("processing_time"),
                    result_image_path=result_data.get("result_image_path"),
                    result_json=result_data.get("result_json"),
                    status=result_data.get("status", "완료"),
                    error_message=result_data.get("error_message")
                )
                success_count += 1


            except Exception as e:

                fail_count += 1

                error_detail = f"{type(e).__name__}: {e}"

                print(f"[비교분석 오류] {model_config['model_name']}: {error_detail}")

                print(traceback.format_exc())

                AiCompareRepository.create_result(

                    compare_run_id=compare_run.id,

                    model_name=model_config["model_name"],

                    optimizer_name=model_config.get("optimizer_name"),

                    model_version=model_config.get("model_version"),

                    total_detections=0,

                    avg_confidence=None,

                    max_confidence=None,

                    processing_time=None,

                    result_image_path=None,

                    result_json=None,

                    status="실패",

                    error_message=error_detail

                )

        compare_run.finished_at = datetime.now()

        if success_count > 0:
            compare_run.status = "완료"
        else:
            compare_run.status = "실패"

        db.session.commit()
        return compare_run

    @classmethod
    def execute_model_analysis(cls, report, report_file, model_config):
        model_name = model_config["model_name"]
        optimizer_name = model_config["optimizer_name"]
        model_version = model_config["model_version"]

        model_path = os.path.join(BASE_DIR, "ai", "models", model_version)
        original_path = os.path.join(BASE_DIR, report_file.file_path)

        if not os.path.exists(original_path):
            original_path = os.path.join(BASE_DIR, "app", report_file.file_path)

        print("====== DEBUG START ======")
        print("DB file_path:", report_file.file_path)
        print("BASE_DIR:", BASE_DIR)
        print("MODEL_PATH:", model_path)
        print("IMAGE_PATH:", original_path)
        print("MODEL_EXISTS:", os.path.exists(model_path))
        print("IMAGE_EXISTS:", os.path.exists(original_path))
        print("====== DEBUG END ======")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"모델 파일이 없습니다: {model_path}")

        if not os.path.exists(original_path):
            raise FileNotFoundError(f"원본 파일이 없습니다: {original_path}")

        if report_file.file_type != "이미지":
            raise ValueError("현재 비교분석 bbox 처리는 이미지 파일만 지원합니다.")

        start_time = time.time()

        detections = run_model_inference(
            model_name=model_name,
            model_path=model_path,
            image_path=original_path
        )

        elapsed_time = round(time.time() - start_time, 4)

        filename = f"{model_name}_{uuid.uuid4().hex}.jpg"

        save_path = os.path.join(BASE_DIR, "app", "static", "uploads", "compare", filename)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        draw_bboxes(
            image_path=original_path,
            detections=detections,
            save_path=save_path
        )

        db_path = f"uploads/compare/{filename}"

        total = len(detections)
        if total > 0:
            avg_conf = sum(d["confidence"] for d in detections) / total
            max_conf = max(d["confidence"] for d in detections)
        else:
            avg_conf = None
            max_conf = None

        class_counts = {}
        for d in detections:
            class_counts[d["label"]] = class_counts.get(d["label"], 0) + 1

        return {
            "model_name": model_name,
            "optimizer_name": optimizer_name,
            "model_version": model_version,
            "total_detections": total,
            "avg_confidence": round(avg_conf, 4) if avg_conf is not None else None,
            "max_confidence": round(max_conf, 4) if max_conf is not None else None,
            "processing_time": elapsed_time,
            "result_image_path": db_path,
            "result_json": {
                "class_counts": class_counts,
                "detections": detections
            },
            "status": "완료",
            "error_message": None
        }

    @staticmethod
    def get_compare_runs_by_report(report_id):
        return AiCompareRepository.get_runs_by_report(report_id)

    @staticmethod
    def get_compare_run_detail(compare_run_id):
        compare_run = AiCompareRepository.get_run_by_id(compare_run_id)
        if not compare_run:
            return None

        results = AiCompareRepository.get_results_by_run(compare_run_id)

        return {
            "compare_run": compare_run,
            "results": results
        }

    @classmethod
    def get_latest_compare_detail_by_report(cls, report_id):
        latest_run = AiCompareRepository.get_latest_run(report_id)
        if not latest_run:
            return None

        return cls.get_compare_run_detail(latest_run.id)