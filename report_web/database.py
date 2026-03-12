import pymysql

def get_db_connection():
    return pymysql.connect(
        host = '192.168.0.161',
        user = 'admin1',
        password = '1234',
        db = 'ai_accident_detection',
        charset = 'utf8mb4',
        cursorclass = pymysql.cursors.DictCursor
    )