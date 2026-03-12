# 환경변수(.env)를 읽기 위한 라이브러리
import os
from dotenv import load_dotenv

# .env 파일을 읽어 환경 변수로 등록
load_dotenv()

class Config:
    '''
    Flask 전체 설정을 관리하는 클래스
    '''

    # Flask 세션 암포화 키
    # .env에 SECRET_KEY가 있으면 그 값을 사용
    # 없으면 fallback-secret-key 사용
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")

    # 데이터 베이스 연결 정보
    # DB 서버 주소
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")

    # DB 포트
    DB_PORT = os.environ.get("DB_PORT", "3306")

    # DB 사용자
    DB_USER = os.environ.get("DB_USER", "root")

    # DB 비밀번호
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

    # DB 이름
    DB_NAME = os.environ.get("DB_NAME", "ai_accident_detection")

    # SQLAlchemy가 사용하는 데이터베이스 연결 주소
    # mysql+pymysql://유저:비밀번호@주소:포트/DB이름
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )

    # SQLAlchemy 불필요한 이벤트 추적 비활성화 (성능 향상)
    SQLALCHEMY_TRACK_MODIFICATIONS = False