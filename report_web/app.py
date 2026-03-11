from flask import Flask, render_template
import os

# 현재 app.py가 있는 폴더 위치를 파악합니다.
app = Flask(__name__, 
            template_folder='templates',  # app.py가 report_web 폴더 안에 있다면 'templates'만 써도 됩니다.
            static_folder='static')

@app.route('/')
def index():
    # 이 부분에서 에러가 났던 것입니다.
    return render_template('report.html')

if __name__ == '__main__':
    app.run(debug=True)