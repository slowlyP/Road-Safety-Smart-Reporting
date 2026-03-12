"""
Flask 애플리케이션을 생성하는 파일

create_app() 함수는
Flask 앱을 생성하고
DB 및 설정을 초기화한다.
"""

from flask import Flask
from .config import Config
from .extensions import db, migrate


def create_app():
    """
    Flask 앱 생성 함수
    """

    # Flask 애플리케이션 생성
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # config.py 설정 적용
    app.config.from_object(Config)

    # -------------------------
    # DB 초기화
    # -------------------------
    db.init_app(app)

    # migration 초기화
    migrate.init_app(app, db)

    # -------------------------
    # 모델 import (Migration 인식용)
    # -------------------------
    with app.app_context():
        from . import models

    # -------------------------
    # 블루프린트 등록
    # -------------------------
    from app.api.auth_routes import auth_bp
    from app.api.main_routes import main_bp
    from app.routes.report_route import report_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)

    return app