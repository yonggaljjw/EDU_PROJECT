# 라우팅 처리하는 파일 (블루프린트 방식)

from flask import Blueprint, render_template

# 블루프린트 객체 생성
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # index.html 렌더링
    return render_template('index.html')