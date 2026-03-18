"""
Flask 서버 실행 파일
"""

# Flask 앱 생성
from app import create_app
from app.extensions import db                  # DB연결 테스트 확인용
from sqlalchemy import text


app = create_app()

with app.app_context():
    try:
        db.session.execute(text("SELECT 1"))
        print("✅ DB 연결 성공")
    except Exception as e:
        print("❌ DB 연결 실패:", e)

# 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000,debug=True)