from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, UserProfile, JobsInfo  # ✅ JobsInfo 추가

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    profile = None
    job_detail = None

    if 'user_id' in session:
        profile = UserProfile.query.filter_by(user_id=session['user_id']).first()

        if profile and profile.target_career:
            job_detail = JobsInfo.query.filter_by(job=profile.target_career).first()

    return render_template('index.html', profile=profile, job_detail=job_detail)


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')

        if not username or not email or not password:
            flash('모든 필드를 입력해주세요.')
            return redirect(url_for('main.register'))

        if User.query.filter_by(email=email).first():
            flash('이미 등록된 이메일입니다.')
            return redirect(url_for('main.register'))

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


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("존재하지 않는 이메일입니다.")
            return redirect(url_for('main.login'))

        if not check_password_hash(user.password_hash, password):
            flash("비밀번호가 일치하지 않습니다.")
            return redirect(url_for('main.login'))

        session['user_id'] = user.id
        session['username'] = user.username
        flash(f"{user.username}님 환영합니다!")
        return redirect(url_for('main.home'))

    return render_template('login.html')


@main_bp.route('/logout')
def logout():
    session.clear()
    flash("로그아웃 되었습니다.")
    return redirect(url_for('main.home'))


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

    # ✅ 직업 목록 불러오기
    job_list = JobsInfo.query.with_entities(JobsInfo.job).distinct().order_by(JobsInfo.job).all()
    job_list = [job[0] for job in job_list if job[0]]

    if request.method == 'POST':
        profile = UserProfile(
            user_id=session['user_id'],
            mbti=request.form.get('mbti'),
            grade_avg=request.form.get('grade_avg'),
            interest_tags=request.form.get('interest_tags'),
            favorite_subjects=request.form.get('favorite_subjects'),
            soft_skills=request.form.get('soft_skills'),
            target_career=request.form.get('target_career'),
            desired_region=request.form.get('desired_region'),
            desired_university_type=request.form.get('desired_university_type'),
            activities=request.form.get('activities'),
        )
        db.session.add(profile)
        db.session.commit()
        flash("프로필이 저장되었습니다.")
        return redirect(url_for('main.profile'))

    return render_template('profile_setup.html', job_list=job_list)


@main_bp.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))

    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
    if not profile:
        flash("프로필이 없습니다. 먼저 작성해주세요.")
        return redirect(url_for('main.profile_setup'))

    # ✅ 직업 목록 불러오기
    job_list = JobsInfo.query.with_entities(JobsInfo.job).distinct().order_by(JobsInfo.job).all()
    job_list = [job[0] for job in job_list if job[0]]

    if request.method == 'POST':
        profile.mbti = request.form.get('mbti')
        profile.grade_avg = request.form.get('grade_avg')
        profile.interest_tags = request.form.get('interest_tags')
        profile.favorite_subjects = request.form.get('favorite_subjects')
        profile.soft_skills = request.form.get('soft_skills')
        profile.target_career = request.form.get('target_career')
        profile.desired_region = request.form.get('desired_region')
        profile.desired_university_type = request.form.get('desired_university_type')
        profile.activities = request.form.get('activities')

        db.session.commit()
        flash("프로필이 수정되었습니다.")
        return redirect(url_for('main.profile'))

    return render_template('profile_edit.html', profile=profile, job_list=job_list)
