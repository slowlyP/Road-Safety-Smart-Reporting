from datetime import datetime

from app.extensions import db, socketio
from app.repositories.realtime_alert_repository import RealtimeAlertRepository


class RealtimeAlertService:
    """
    실시간 위험 알림 서비스

    역할
    - 위험/긴급 알림 목록 가공
    - 미확인 개수 가공
    - 읽음 처리
    - 전체 읽음 처리
    - AI 탐지 결과 기반 알림 생성 + 소켓 전송
    """

    ALERT_MESSAGE_MAP = {
        "위험": "⚠️ 위험 낙하물 탐지! 빠른 조치가 필요합니다.",
        "긴급": "🚨 긴급 낙하물 탐지! 즉시 확인이 필요합니다."
    }

    # -------------------------------------------------------
    # 파일 경로 정규화
    # -------------------------------------------------------
    @staticmethod
    def _normalize_file_path(file_path):
        """
        DB에 저장된 file_path를 브라우저에서 바로 쓸 수 있게 정리

        예:
        static/uploads/xxx.png  -> /static/uploads/xxx.png
        /static/uploads/xxx.png -> /static/uploads/xxx.png
        """
        if not file_path:
            return ""

        normalized = file_path.replace("\\", "/").strip()

        if not normalized.startswith("/"):
            normalized = f"/{normalized}"

        return normalized

    # -------------------------------------------------------
    # 알림 목록 조회
    # -------------------------------------------------------
    @staticmethod
    def get_realtime_alerts(limit=50):
        """
        위험/긴급 알림 목록 조회
        """
        rows = RealtimeAlertRepository.find_realtime_alerts(limit=limit)

        result = []
        for row in rows:
            result.append({
                "alert_id": row.alert_id,
                "report_id": row.report_id,
                "detection_id": row.detection_id,
                "alert_level": row.alert_level,
                "message": row.message,
                "is_read": bool(row.is_read),

                "report_title": row.report_title,
                "location_text": row.location_text or "-",
                "risk_level": row.risk_level or "-",

                "detected_label": row.detected_label or "-",
                "confidence": float(row.confidence) if row.confidence is not None else 0.0,

                "file_type": row.file_type or "-",
                "file_path": RealtimeAlertService._normalize_file_path(row.file_path),
                "original_name": row.original_name or "-",

                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if row.created_at else "-"
            })

        return result

    # -------------------------------------------------------
    # 미확인 개수
    # -------------------------------------------------------
    @staticmethod
    def get_unread_count():
        """
        미확인 위험/긴급 알림 개수 조회
        """
        return RealtimeAlertRepository.count_unread_alerts()

    # -------------------------------------------------------
    # 읽음 처리
    # -------------------------------------------------------
    @staticmethod
    def mark_as_read(alert_id):
        """
        특정 알림 읽음 처리
        """
        alert = RealtimeAlertRepository.find_alert_by_id(alert_id)

        if not alert:
            return None

        return RealtimeAlertRepository.mark_as_read(alert)

    @staticmethod
    def mark_all_as_read():
        """
        전체 위험/긴급 알림 읽음 처리
        """
        return RealtimeAlertRepository.mark_all_as_read()

    # -------------------------------------------------------
    # 핵심: 알림 생성
    # -------------------------------------------------------
    @staticmethod
    def create_realtime_alert(report, detection, report_file):
        """
        AI 탐지 결과를 바탕으로 실시간 알림 생성

        ✔ 호출 위치
        - report_service.py 내부
        - detection 생성 이후

        ✔ 흐름
        1. alert DB row 생성
        2. 프론트로 보낼 payload 생성
        3. (emit은 여기서 하지 않음)
        """

        if not report or not detection:
            return None

        # ✔ 위험/긴급만 허용
        if report.risk_level not in ["위험", "긴급"]:
            return None

        message = RealtimeAlertService.ALERT_MESSAGE_MAP.get(
            report.risk_level,
            "위험 알림이 발생했습니다."
        )

        # -------------------------------------------------------
        # DB 알림 생성
        # -------------------------------------------------------
        new_alert = RealtimeAlertRepository.create_alert(
            report_id=report.id,
            detection_id=detection.id,
            alert_level=report.risk_level,
            message=message
        )

        # -------------------------------------------------------
        # 프론트 전달용 payload 생성
        # -------------------------------------------------------
        payload = {
            "alert_id": new_alert.id,
            "report_id": report.id,
            "detection_id": detection.id,
            "alert_level": report.risk_level,
            "message": message,

            "report_title": report.title,
            "location_text": report.location_text or "-",
            "risk_level": report.risk_level,

            "detected_label": detection.detected_label,
            "confidence": float(detection.confidence)
            if detection.confidence is not None else 0.0,

            "file_type": getattr(report_file, "file_type", "-") if report_file else "-",
            "file_path": RealtimeAlertService._normalize_file_path(
                getattr(report_file, "file_path", "")
            ) if report_file else "",

            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_read": False
        }

        return {
            "alert": new_alert,
            "payload": payload
        }

    # -------------------------------------------------------
    # 핵심: 소켓 emit
    # -------------------------------------------------------
    @staticmethod
    def emit_realtime_alert(payload):
        """
        실시간 알림 소켓 전송

        ✔ 반드시 DB commit 이후 호출
        """
        if not payload:
            return

        socketio.emit(
            "new_realtime_alert",   # 프론트 JS 이벤트명
            payload,
            room="admin_room",
            namespace="/admin/realtime-alert"
        )

    # -------------------------------------------------------
    # (선택) 헬퍼 메서드
    # -------------------------------------------------------
    @staticmethod
    def create_and_emit_after_commit(report, detection, report_file):
        """
        구조 이해용 헬퍼

        실제 사용 추천 흐름:
        1. create_realtime_alert()
        2. db.session.commit()
        3. emit_realtime_alert()

        👉 이 메서드는 지금 안 써도 됨
        """
        alert_result = RealtimeAlertService.create_realtime_alert(
            report=report,
            detection=detection,
            report_file=report_file
        )

        if not alert_result:
            return None

        return alert_result