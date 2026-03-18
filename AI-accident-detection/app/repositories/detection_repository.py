from sqlalchemy import func, case
from app.extensions import db
from app.models import Detection, Report, ReportFile


class DetectionRepository:
    """
    AI 탐지 결과 전용 Repository

    역할
    - AI 탐지 목록 조회
    - AI 탐지 상세 조회
    - AI 통계 데이터 집계
    """

    @staticmethod
    def find_detection_list(page=1, per_page=10, label=None, min_conf=None, max_conf=None, status=None):
        """
        AI 탐지 로그 목록 조회

        필터
        - label        : 탐지 라벨명
        - min_conf     : 최소 confidence
        - max_conf     : 최대 confidence
        - status       : 연결된 신고 상태
        """

        query = (
            db.session.query(
                Detection.id.label("detection_id"),
                Detection.detected_label,
                Detection.confidence,
                Detection.detected_at,
                Report.id.label("report_id"),
                Report.title.label("report_title"),
                Report.risk_level,
                Report.status,
                ReportFile.file_type,
                ReportFile.file_path
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
        )

        if label:
            query = query.filter(Detection.detected_label == label)

        if min_conf is not None:
            query = query.filter(Detection.confidence >= min_conf)

        if max_conf is not None:
            query = query.filter(Detection.confidence <= max_conf)

        if status:
            query = query.filter(Report.status == status)

        query = query.order_by(Detection.detected_at.desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def find_detection_detail(detection_id):
        """
        AI 탐지 상세 조회
        """

        return (
            db.session.query(
                Detection,
                Report,
                ReportFile
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Detection.id == detection_id)
            .first()
        )

    @staticmethod
    def count_all_detections():
        """
        전체 탐지 건수
        """
        return db.session.query(func.count(Detection.id)).scalar() or 0

    @staticmethod
    def get_average_confidence():
        """
        평균 confidence
        """
        avg_conf = db.session.query(func.avg(Detection.confidence)).scalar()
        return round(float(avg_conf), 2) if avg_conf else 0.0

    @staticmethod
    def count_false_positives():
        """
        오탐 건수
        기준:
        - detection 존재
        - 연결된 report.status == '오탐'
        """
        return (
            db.session.query(func.count(Detection.id))
            .join(Report, Detection.report_id == Report.id)
            .filter(Report.status == "오탐")
            .scalar()
            or 0
        )

    @staticmethod
    def get_label_statistics():
        """
        라벨별 탐지 건수
        """
        rows = (
            db.session.query(
                Detection.detected_label,
                func.count(Detection.id).label("count")
            )
            .group_by(Detection.detected_label)
            .order_by(func.count(Detection.id).desc())
            .all()
        )

        return rows

    @staticmethod
    def get_daily_detection_statistics(limit=7):
        """
        최근 N일 탐지 추이
        MySQL 기준: DATE(detected_at)
        """
        rows = (
            db.session.query(
                func.date(Detection.detected_at).label("date"),
                func.count(Detection.id).label("count")
            )
            .group_by(func.date(Detection.detected_at))
            .order_by(func.date(Detection.detected_at).desc())
            .limit(limit)
            .all()
        )

        return list(reversed(rows))

    @staticmethod
    def get_confidence_distribution():
        """
        confidence 구간별 분포

        구간:
        - 0~49
        - 50~69
        - 70~84
        - 85~100
        """

        rows = (
            db.session.query(
                case(
                    (Detection.confidence < 50, "0~49"),
                    (Detection.confidence < 70, "50~69"),
                    (Detection.confidence < 85, "70~84"),
                    else_="85~100"
                ).label("range"),
                func.count(Detection.id).label("count")
            )
            .group_by("range")
            .order_by("range")
            .all()
        )

        return rows

    @staticmethod
    def find_recent_false_positive_cases(limit=5):
        """
        최근 오탐 사례 조회
        """
        rows = (
            db.session.query(
                Detection.id.label("detection_id"),
                Detection.detected_label,
                Detection.confidence,
                Detection.detected_at,
                Report.id.label("report_id"),
                Report.title.label("report_title"),
                Report.status,
                ReportFile.file_type,
                ReportFile.file_path
            )
            .join(Report, Detection.report_id == Report.id)
            .outerjoin(ReportFile, Detection.file_id == ReportFile.id)
            .filter(Report.status == "오탐")
            .order_by(Detection.detected_at.desc())
            .limit(limit)
            .all()
        )

        return rows