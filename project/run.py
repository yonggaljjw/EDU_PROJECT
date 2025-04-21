# Flask 애플리케이션 실행용 진입점

from app import create_app

# Flask 앱 생성
app = create_app()

# 앱 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)