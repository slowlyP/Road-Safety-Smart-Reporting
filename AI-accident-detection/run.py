"""
Flask 서버 실행 파일
"""

# Flask 앱 생성
from app import create_app
from app.extensions import db, socketio     # extensions에 추가한 소켓 객체
from sqlalchemy import text                 # DB연결 테스트 확인용


app = create_app()

with app.app_context():
    try:
        db.session.execute(text("SELECT 1"))
        print("✅ DB 연결 성공")
    except Exception as e:
        print("❌ DB 연결 실패:", e)


# 실시간 알림을 위한 소켓 연동으로 변경
if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )