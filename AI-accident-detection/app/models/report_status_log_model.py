from app.extensions import db


class ReportStatusLog(db.Model):
    """
    신고 상태 변경 이력
    """

    __tablename__ = "report_status_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    report_id = db.Column(
        db.BigInteger,
        db.ForeignKey("reports.id"),
        nullable=False
    )

    old_status = db.Column(
        db.Enum("접수", "확인중", "처리완료", "오탐")
    )

    new_status = db.Column(
        db.Enum("접수", "확인중", "처리완료", "오탐")
    )

    changed_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id")
    )

    memo = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )