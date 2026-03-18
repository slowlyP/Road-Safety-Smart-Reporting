from app.extensions import db


class Detection(db.Model):
    """
    AI 낙하물 탐지 결과
    """

    __tablename__ = "detections"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    report_id = db.Column(
        db.BigInteger,
        db.ForeignKey("reports.id"),
        nullable=False
    )

    file_id = db.Column(
        db.BigInteger,
        db.ForeignKey("report_files.id"),
        nullable=False
    )

    detected_label = db.Column(db.String(100), nullable=False)

    confidence = db.Column(
        db.Numeric(5, 2),
        nullable=False
    )

    bbox_x1 = db.Column(db.Integer, nullable=False)

    bbox_y1 = db.Column(db.Integer, nullable=False)

    bbox_x2 = db.Column(db.Integer, nullable=False)

    bbox_y2 = db.Column(db.Integer, nullable=False)

    detected_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )
    @property
    def label_kor(self):
        # DB에 저장된 영문 클래스 네임을 한글로 매핑
        label_map = {
            "box": "박스형",
            "bag": "봉투류",
            "tire": "타이어",
            "rock": "낙석",
            "debris": "나머지 파편"
        }
        # 만약 매핑에 없으면 영문 그대로 표시
        return label_map.get(self.detected_label, self.detected_label)