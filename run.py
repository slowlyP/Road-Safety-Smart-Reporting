# 가장 바깥쪽에서 서버를 실행하는 파일
# 이 파일은 말 그대로 프로그램 시작점임.


# 주된 역할
# 1. Flask 앱을 생성함.
# 2. 서버를 실행한다


from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)