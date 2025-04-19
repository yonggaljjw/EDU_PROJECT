# Flask 앱을 생성하는 팩토리 함수

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

# SQLAlchemy ORM 객체 생성
db = SQLAlchemy()

def create_app():
    # Flask 앱 인스턴스 생성
    app = Flask(__name__)
    
    # 환경 설정 적용
    app.config.from_object(Config)

    # DB 초기화
    db.init_app(app)

    # 블루프린트 등록 (라우팅)
    from views.main import main_bp
    app.register_blueprint(main_bp)

    return app

