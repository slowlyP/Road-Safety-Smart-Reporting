"""
Flask 애플리케이션을 생성하는 파일
"""

from flask import Flask, session
from werkzeug.exceptions import RequestEntityTooLarge

from .config import Config
from .extensions import db, migrate, socketio
from app.common.response import error_response


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # -------------------------------------------------
    # 앱 설정 로드
    # -------------------------------------------------
    app.config.from_object(Config)

    # -------------------------------------------------
    # 전역 업로드 용량 초과(413) 처리
    # - Config.MAX_CONTENT_LENGTH를 초과하면 여기로 떨어짐
    # -------------------------------------------------
    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(e):
        return error_response(
            message="업로드 가능한 최대 용량(50MB)을 초과했습니다.",
            status_code=413
        )

    # -------------------------------------------------
    # Flask 확장 초기화
    # -------------------------------------------------
    # DB 초기화
    db.init_app(app)

    # migration 초기화
    migrate.init_app(app, db)

    # 소켓 초기화
    socketio.init_app(app)

    # -------------------------------------------------
    # 모델 로딩
    # - SQLAlchemy가 모델을 인식할 수 있도록 앱 컨텍스트 안에서 import
    # -------------------------------------------------
    with app.app_context():
        from . import models

    # -----------------------------
    # 템플릿 공통 변수 주입
    # -----------------------------
    @app.context_processor
    def inject_user_state():
        """
        모든 템플릿에서 로그인 상태 / 관리자 여부를 공통으로 사용하기 위한 값 주입

        base.html 에서 사용 예:
        {% if is_logged_in and is_admin %}
            실시간 알림 CSS / JS / 오디오 / 토스트 영역 로드
        {% endif %}
        """
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
    from app.api.admin_routes import admin_bp
    from app.api.admin_report_routes import admin_report_bp
    from app.api.admin_user_routes import admin_user_bp
    from app.api.admin_ai_routes import admin_ai_bp
    from app.api.report_list_routes import report_list_bp
    from app.api.admin_realtime_alert_routes import admin_realtime_alert_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_report_bp)
    app.register_blueprint(admin_user_bp)
    app.register_blueprint(admin_ai_bp)
    app.register_blueprint(report_list_bp)
    app.register_blueprint(admin_realtime_alert_bp)

    # -----------------------------
    # 소켓 이벤트 등록
    # - import만 해도 이벤트 핸들러가 등록되도록 구성
    # -----------------------------
    from app.socket_events import admin_realtime_alert_socket  # noqa: F401

    return app