from app.repositories.detection_repository import DetectionRepository


class AdminAIService:
    """
    관리자 AI 분석 서비스

    역할
    - AI 탐지 로그 목록 가공
    - AI 탐지 상세 데이터 가공
    - AI 통계 / 차트 데이터 가공
    - AI 요약 보고서 데이터 생성
    """

    @staticmethod
    def get_detection_list(page=1, per_page=10, label=None, min_conf=None, max_conf=None, status=None):
        """
        AI 탐지 로그 목록 조회
        """

        pagination = DetectionRepository.find_detection_list(
            page=page,
            per_page=per_page,
            label=label,
            min_conf=min_conf,
            max_conf=max_conf,
            status=status
        )

        items = []
        for row in pagination.items:
            items.append({
                "detection_id": row.detection_id,
                "report_id": row.report_id,
                "report_title": row.report_title,
                "detected_label": row.detected_label,
                "confidence": float(row.confidence) if row.confidence is not None else 0.0,
                "risk_level": row.risk_level,
                "status": row.status,
                "file_type": row.file_type or "-",
                "file_path": row.file_path,
                "detected_at": row.detected_at.strftime("%Y-%m-%d %H:%M") if row.detected_at else "-"
            })

        return {
            "items": items,
            "pagination": pagination
        }

    @staticmethod
    def get_detection_detail(detection_id):
        """
        AI 탐지 상세 조회
        """
        result = DetectionRepository.find_detection_detail(detection_id)

        if not result:
            return None

        detection, report, report_file = result

        return {
            "detection": {
                "id": detection.id,
                "report_id": detection.report_id,
                "file_id": detection.file_id,
                "detected_label": detection.detected_label,
                "confidence": float(detection.confidence) if detection.confidence is not None else 0.0,
                "bbox_x1": detection.bbox_x1,
                "bbox_y1": detection.bbox_y1,
                "bbox_x2": detection.bbox_x2,
                "bbox_y2": detection.bbox_y2,
                "detected_at": detection.detected_at.strftime("%Y-%m-%d %H:%M") if detection.detected_at else "-"
            },
            "report": {
                "id": report.id,
                "title": report.title,
                "content": report.content,
                "report_type": report.report_type,
                "location_text": report.location_text,
                "risk_level": report.risk_level,
                "status": report.status,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "-"
            },
            "file": {
                "id": report_file.id if report_file else None,
                "file_type": report_file.file_type if report_file else None,
                "file_path": report_file.file_path if report_file else None,
                "original_name": report_file.original_name if report_file else None
            } if report_file else None,
            "is_false_positive": True if report.status == "오탐" else False
        }

    @staticmethod
    def get_ai_summary():
        """
        AI 요약 통계
        """
        total_detections = DetectionRepository.count_all_detections()
        avg_confidence = DetectionRepository.get_average_confidence()
        false_positives = DetectionRepository.count_false_positives()

        false_positive_rate = 0.0
        if total_detections > 0:
            false_positive_rate = round((false_positives / total_detections) * 100, 2)

        return {
            "total_detections": total_detections,
            "avg_confidence": avg_confidence,
            "false_positives": false_positives,
            "false_positive_rate": false_positive_rate
        }

    @staticmethod
    def get_label_statistics():
        """
        라벨별 탐지 건수
        """
        rows = DetectionRepository.get_label_statistics()

        labels = []
        counts = []

        for row in rows:
            labels.append(row.detected_label or "미분류")
            counts.append(row.count)

        return {
            "labels": labels,
            "counts": counts
        }

    @staticmethod
    def get_daily_detection_trend(limit=7):
        """
        일자별 탐지 추이
        """
        rows = DetectionRepository.get_daily_detection_statistics(limit=limit)

        dates = []
        counts = []

        for row in rows:
            dates.append(str(row.date))
            counts.append(row.count)

        return {
            "dates": dates,
            "counts": counts
        }

    @staticmethod
    def get_confidence_distribution():
        """
        confidence 구간별 분포
        """
        rows = DetectionRepository.get_confidence_distribution()

        range_order = ["0~49", "50~69", "70~84", "85~100"]
        range_map = {key: 0 for key in range_order}

        for row in rows:
            range_map[row.range] = row.count

        return {
            "ranges": list(range_map.keys()),
            "counts": list(range_map.values())
        }

    @staticmethod
    def get_recent_false_positive_cases(limit=5):
        """
        최근 오탐 사례
        """
        rows = DetectionRepository.find_recent_false_positive_cases(limit=limit)

        result = []
        for row in rows:
            result.append({
                "detection_id": row.detection_id,
                "report_id": row.report_id,
                "report_title": row.report_title,
                "detected_label": row.detected_label,
                "confidence": float(row.confidence) if row.confidence is not None else 0.0,
                "status": row.status,
                "file_type": row.file_type or "-",
                "file_path": row.file_path,
                "detected_at": row.detected_at.strftime("%Y-%m-%d %H:%M") if row.detected_at else "-"
            })

        return result

    @staticmethod
    def get_summary_page_data():
        """
        summary.html 전용 통합 데이터
        """
        summary = AdminAIService.get_ai_summary()
        label_stats = AdminAIService.get_label_statistics()
        daily_trend = AdminAIService.get_daily_detection_trend(limit=7)
        confidence_distribution = AdminAIService.get_confidence_distribution()
        recent_false_positives = AdminAIService.get_recent_false_positive_cases(limit=5)

        return {
            "summary": summary,
            "label_stats": label_stats,
            "daily_trend": daily_trend,
            "confidence_distribution": confidence_distribution,
            "recent_false_positives": recent_false_positives
        }