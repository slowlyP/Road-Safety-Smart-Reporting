from app.extensions import db


class RoleRequest(db.Model):
    """
    관리자 권한 신청 테이블
    """

    __tablename__ = "role_requests"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=False
    )

    request_reason = db.Column(db.Text)

    status = db.Column(
        db.Enum("대기", "승인", "거절"),
        default="대기"
    )

    reviewed_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id")
    )

    reviewed_at = db.Column(db.DateTime)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )