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
    app = Flask(__name__)

    # config.py 설정 적용
    app.config.from_object(Config)

    # DB 연결 초기화
    db.init_app(app)

    # migration 초기화
    migrate.init_app(app, db)

    # 모델 import
    # 모델을 여기서 import 해야
    # Flask-Migrate가 테이블을 인식한다
    with app.app_context():
        from app.models import User

    return app