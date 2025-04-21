from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from .models import db, User, UserProfile
from werkzeug.security import check_password_hash
from flask import session  # 세션 저장용

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        # 유효성 검사
        if not username or not email or not password:
            flash('모든 필드를 입력해주세요.')
            return redirect(url_for('main.register'))

        # 이메일 중복 체크
        if User.query.filter_by(email=email).first():
            flash('이미 등록된 이메일입니다.')
            return redirect(url_for('main.register'))

        # 비밀번호 해시화 및 저장
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        flash('회원가입이 완료되었습니다! 로그인 해주세요.')
        return redirect(url_for('main.home'))

    return render_template('register.html')


@main_bp.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))

    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()

    if not profile:
        flash("프로필이 없습니다. 먼저 작성해주세요.")
        return redirect(url_for('main.profile_setup'))

    if request.method == 'POST':
        profile.mbti = request.form['mbti']
        profile.interest_tags = request.form['interest_tags']
        profile.favorite_subjects = request.form['favorite_subjects']
        profile.strength_subjects = request.form['strength_subjects']
        profile.desired_region = request.form['desired_region']
        profile.target_career = request.form['target_career']
        profile.activities = request.form['activities']

        db.session.commit()
        flash("프로필이 수정되었습니다.")
        return redirect(url_for('main.profile'))

    return render_template('profile_edit.html', profile=profile)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("존재하지 않는 이메일입니다.")
            return redirect(url_for('main.login'))

        if not check_password_hash(user.password_hash, password):
            flash("비밀번호가 일치하지 않습니다.")
            return redirect(url_for('main.login'))

        # 로그인 성공 → 세션에 저장
        session['user_id'] = user.id
        session['username'] = user.username
        flash(f"{user.username}님 환영합니다!")
        return redirect(url_for('main.home'))

    return render_template('login.html')


@main_bp.route('/logout')
def logout():
    session.clear()  # ✅ 모든 세션 정보 제거
    flash("로그아웃 되었습니다.")
    return redirect(url_for('main.home'))  # 홈으로 리디렉트


@main_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))

    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()

    if profile:
        return render_template('profile.html', profile=profile)
    else:
        flash("아직 프로필 정보가 없습니다. 테스트를 진행해주세요.")
        return redirect(url_for('main.profile_setup'))


@main_bp.route('/profile/setup', methods=['GET', 'POST'])
def profile_setup():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        profile = UserProfile(
            user_id=session['user_id'],
            mbti=request.form['mbti'],
            interest_tags=request.form['interest_tags'],
            favorite_subjects=request.form['favorite_subjects'],
            strength_subjects=request.form['strength_subjects'],
            desired_region=request.form['desired_region'],
            target_career=request.form['target_career'],
            activities=request.form['activities']
        )
        db.session.add(profile)
        db.session.commit()
        flash("프로필이 저장되었습니다.")
        return redirect(url_for('main.profile'))

    return render_template('profile_setup.html')




