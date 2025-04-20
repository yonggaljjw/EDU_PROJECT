from flask import Flask
from config import Config
from views.models import db
from views.main import main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config.get("SECRET_KEY", "dev")

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(main_bp)
    return app
