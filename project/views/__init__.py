from flask import Flask
from config import Config
from views.models import db  # 💡 models.py의 db 그대로 가져와야 함
from views.main import main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = 'dev'  #
    db.init_app(app)

    # blueprint 등록
    app.register_blueprint(main_bp)

    # 앱 시작 전에 테이블이 없으면 자동 생성
    with app.app_context():
        db.create_all()

    return app
