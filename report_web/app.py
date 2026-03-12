import os
from flask import Flask, render_template
from routes.report_route import report_bp

# 1. 현재 app.py 파일이 있는 위치(c:\report_web)를 가져옵니다.
base_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Flask 설정 수정 (이중 경로 제거)
# 현재 base_dir 자체가 'c:\report_web'이므로, 그 안에 바로 templates가 있다면 아래처럼 써야 합니다.
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'), 
            static_folder=os.path.join(base_dir, 'static'))

# 만약 위 방법으로도 안 되면, 그냥 기본값을 믿고 아래처럼만 써보세요.
# app = Flask(__name__) 

app.register_blueprint(report_bp)

@app.route('/')
def index():
    return render_template('report.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)