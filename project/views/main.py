from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, UserProfile, JobsInfo, AiResult, EmploymentFull  # ✅ JobsInfo 추가
import logging
import random
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    profile = None
    job_detail = None
    random_schools = []
    random_jobs = []

    if 'user_id' in session:
        profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
        if profile and profile.target_career:
            job_detail = JobsInfo.query.filter_by(job=profile.target_career).first()
    else:
        # 전체 학교/직업 데이터 가져온 후 파이썬에서 랜덤 추출
        all_schools = EmploymentFull.query.all()
        all_jobs = JobsInfo.query.filter(JobsInfo.salery.isnot(None)).all()

        if len(all_schools) >= 3:
            random_schools = random.sample(all_schools, 3)
        else:
            random_schools = all_schools

        if len(all_jobs) >= 3:
            random_jobs = random.sample(all_jobs, 3)
        else:
            random_jobs = all_jobs

    return render_template(
        'index.html',
        profile=profile,
        job_detail=job_detail,
        random_schools=random_schools,
        random_jobs=random_jobs
    )

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


@main_bp.route('/recommend')
def recommend():
    return render_template('recommend.html')



import logging
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import openai

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)

# OpenAI 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")


# GPT 요청 함수 (질문별로 맞춤화된 프롬프트)
def get_gpt_answer(index, question_type, profile, answer):
    base_info = f"""
당신의 MBTI는 {profile.mbti},
성적 평균은 {profile.grade_avg},
관심 분야는 {profile.interest_tags},
선호 과목은 {profile.favorite_subjects},
소프트 스킬은 {profile.soft_skills},
희망 진로는 {profile.target_career},
희망 지역은 {profile.desired_region},
희망 대학 유형은 {profile.desired_university_type},
기타 활동 이력은 {profile.activities} 입니다.
"""

    if question_type == "요약":
        prompt = base_info + f"\n\n추가 질문:\n{answer}\n\n위 정보를 요약하고, 진로 방향과 관련 직업을 간결하게 정리해줘."
    elif question_type == "진로":
        prompt = base_info + "\n\n희망 진로에 필요한 자격증, 준비 전략 등을 구체적으로 제시해줘."
    elif question_type == "학과":
        prompt = base_info + "\n\n성적과 목표를 기반으로 진학 가능한 학과와 학교를 추천해줘."
    else:
        prompt = "[잘못된 질문 유형]"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 진로 전문 상담가야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        logging.error("❌ GPT 호출 실패: %s", traceback.format_exc())
        return f"[GPT 응답 오류 발생 - {question_type}]"


# 메인 라우트 함수
@main_bp.route('/recommend/ai', methods=['GET', 'POST'])
def recommend_ai():
    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect(url_for('main.login'))

    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()

    if not profile:
        flash("AI 분석을 위해 먼저 프로필을 작성해주세요.")
        return redirect(url_for('main.profile_setup'))

    questions = [
        "당신의 경험과 특성을 요약해 주세요.",
        "당신이 희망하는 진로에 맞춘 준비 전략이 궁금합니다.",
        "당신에게 적합한 학과나 대학을 추천해주세요."
    ]

    if request.method == 'POST':
        try:
            answers = [request.form.get(f"answer{i+1}") for i in range(3)]
            types = ["요약", "진로", "학과"]

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(get_gpt_answer, i, types[i], profile, answers[i])
                    for i in range(3)
                ]
                results = [f.result() for f in as_completed(futures)]

            result_text = "\n\n".join([f"Q{i+1}. {results[i]}" for i in range(3)])

            ai_result = AiResult(user_id=session['user_id'], result=result_text)
            db.session.add(ai_result)
            db.session.commit()

            return redirect(url_for('main.recommend_result', result_id=ai_result.id))

        except Exception as e:
            logging.error("❌ AI 분석 중 예외 발생: %s", traceback.format_exc())
            flash("AI 분석 중 오류가 발생했습니다.")
            return redirect(url_for('main.recommend_ai'))

    return render_template("recommend_ai.html", profile=profile, questions=questions)

@main_bp.route('/recommend/result')
def recommend_result():
    result_id = request.args.get('result_id')
    ai_result = AiResult.query.filter_by(id=result_id, user_id=session['user_id']).first()
    if not ai_result:
        flash("결과를 찾을 수 없습니다.")
        return redirect(url_for('main.recommend_ai'))
    return render_template('recommend_result.html', result=ai_result.result)

@main_bp.route('/history')
def history():
    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect(url_for('main.login'))

    results = AiResult.query.filter_by(user_id=session['user_id']).order_by(AiResult.created_at.desc()).all()
    return render_template("history.html", results=results)