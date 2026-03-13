"""
Flask 애플리케이션을 생성하는 파일
"""

from flask import Flask, session
from .config import Config
from .extensions import db, migrate


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    app.config.from_object(Config)

    # DB 초기화
    db.init_app(app)

    # migration 초기화
    migrate.init_app(app, db)

    # 모델 로딩
    with app.app_context():
        from . import models

    # -----------------------------
    # 템플릿 공통 변수 주입
    # -----------------------------
    @app.context_processor
    def inject_user_state():
        is_logged_in = "user_id" in session
        is_admin = session.get("role") == "admin"

        return {
            "is_logged_in": is_logged_in,
            "is_admin": is_admin
        }

    # -----------------------------
    # 블루프린트 등록
    # -----------------------------
    from app.api.auth_routes import auth_bp
    from app.api.main_routes import main_bp
    from app.api.report_route import report_bp
    from app.api.detect_routes import detect_bp
    from app.api.admin_dashboard_routes import admin_dashboard_bp
    from app.api.admin_report_routes import admin_report_bp
    from app.api.admin_user_routes import admin_user_bp
    from app.api.report_list_routes import report_list_bp
    from app.api.admin_role_request_routes import admin_role_request_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(detect_bp)
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(admin_report_bp)
    app.register_blueprint(admin_user_bp)
    app.register_blueprint(admin_role_request_bp)

    app.register_blueprint(report_list_bp)

    return app