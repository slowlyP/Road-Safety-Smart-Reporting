"""
Flask 서버 실행 파일
"""

# Flask 앱 생성
from app import create_app

app = create_app()

# 간단한 서버 테스트용 라우터
@app.route("/")
def home():
    return "Server Running"

# 서버 실행
if __name__ == "__main__":
    app.run(debug=True)