from flask import Blueprint,current_app, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, UserProfile, JobsInfo, AiResult, EmploymentFull  # ✅ JobsInfo 추가
import logging
import random
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai
from elasticsearch import Elasticsearch
from views.character_prompt import build_prompt



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




# 로깅 설정
logging.basicConfig(level=logging.DEBUG)

# OpenAI 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")


# GPT 요청 함수 (질문별로 맞춤화된 프롬프트)

# Elasticsearch 클라이언트
es = Elasticsearch([os.getenv("ELASTICSEARCH_URL")])
index_name = "ncs_skills"

def get_ncs_rag_context(query_text, top_k=5):
    # 1. 쿼리 임베딩 생성
    embedding = openai.Embedding.create(
        input=query_text,
        model="text-embedding-3-small")['data'][0]['embedding']

    # 2. ES 벡터 유사도 검색
    knn_query = {
        "field": "total_vector",
        "query_vector": embedding,
        "k": top_k,
        "num_candidates": 100
    }

    response = es.search(
        index=index_name,
        knn=knn_query,
        source=["compUnitName", "skills", "knowledge", "performance_criteria"]
    )
    docs = [hit["_source"] for hit in response["hits"]["hits"]]

    # 3. 프롬프트용 텍스트로 정리
    context = "\n\n".join([
        f"직무명: {d.get('compUnitName','')}\n- 기술: {d.get('skills','')}\n- 지식: {d.get('knowledge','')}\n- 수행기준: {d.get('performance_criteria','')}"
        for d in docs
    ])
    return context

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

    # RAG: NCS 직무능력 유사 문서 검색
    rag_context = get_ncs_rag_context(answer if question_type == "요약" else profile.target_career)

    print(rag_context)
    if question_type == "요약":
        prompt = (
            base_info
            + f"\n\n[유사 직무능력 정보]\n{rag_context}"
            + f"\n\n추가 질문:\n{answer}\n\n위 정보를 요약하고, 진로 방향과 관련 직업을 간결하게 정리해줘."
        )
    elif question_type == "진로":
        prompt = (
            base_info
            + f"\n\n[유사 직무능력 정보]\n{rag_context}"
            + "\n\n희망 진로에 필요한 자격증, 준비 전략 등을 구체적으로 제시해줘."
        )
    elif question_type == "학과":
        prompt = (
            base_info
            + f"\n\n[유사 직무능력 정보]\n{rag_context}"
            + "\n\n성적과 목표를 기반으로 진학 가능한 학과와 학교를 추천해줘."
        )
    else:
        prompt = "[잘못된 질문 유형]"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 진로 전문 상담가야. 아래의 유사 직무능력 정보도 반드시 참고해서 답변해."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
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

import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
import easyocr

@main_bp.route('/recommend/pdf', methods=['GET', 'POST'])
def recommend_pdf():
    if request.method == 'POST':
        file = request.files.get('report_file')
        if not file or not file.filename.endswith('.pdf'):
            flash("PDF 파일만 업로드 가능합니다.")
            return redirect(url_for('main.recommend_pdf'))

        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # ✅ 1. PDF → 이미지 변환 및 EasyOCR 추출
            pdf_doc = fitz.open(file_path)
            reader = easyocr.Reader(['ko', 'en'], gpu=False)
            extracted_text = ""

            max_pages = min(len(pdf_doc), 5)  # 최대 5페이지까지만 분석
            for i in range(max_pages):
                page = pdf_doc.load_page(i)
                pix = page.get_pixmap(dpi=300)
                img_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_page_{i}.png")
                pix.save(img_path)

                text_list = reader.readtext(img_path, detail=0, paragraph=True)
                extracted_text += "\n".join(text_list) + "\n"

                os.remove(img_path)

            pdf_doc.close()

            # ✅ 2. 키워드 기반 문장 필터링
            keywords = ["진로", "희망", "활동", "성향", "특징", "세부능력", "성적", "자기", "목표", "장래"]
            lines = extracted_text.splitlines()
            filtered = [line.strip() for line in lines if any(k in line for k in keywords) and len(line.strip()) > 15]
            trimmed_text = "\n".join(filtered[:15])  # 최대 15문장

            if not trimmed_text.strip():
                result = "📭 분석할 수 있는 정보가 충분하지 않습니다. 진로/활동/성향 등의 정보가 포함된 스캔된 생활기록부를 업로드해주세요."
                return render_template("recommend_pdf_result.html", result=result)

            # ✅ 3. GPT 분석 프롬프트 구성
            prompt = f"""
다음은 한 학생의 스캔된 생활기록부에서 OCR을 통해 추출한 내용입니다:

{trimmed_text}

이 학생의 성향, 강점, 흥미, 활동을 바탕으로 다음 내용을 구체적으로 작성해주세요:
1. 학생의 성격 및 강점 요약
2. 적합한 진로 방향 및 그 이유
3. 추천 학과 및 전공
4. 향후 진학 또는 직업 준비 전략
"""

            openai.api_key = os.getenv("OPENAI_API_KEY")
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "너는 진로 설계 전문가야."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            result = response['choices'][0]['message']['content']
            return render_template("recommend_pdf_result.html", result=result)

        except Exception as e:
            traceback.print_exc()
            flash("⚠️ 분석 중 오류가 발생했습니다. 다시 시도해주세요.")
            return redirect(url_for('main.recommend_pdf'))

    return render_template("recommend_pdf.html")


# 캐릭터 챗
# 캐릭터 선택 화면
@main_bp.route('/chat/character/select')
def select_character():
    return render_template('character_select.html')  # 캐릭터 선택하는 페이지

# 캐릭터 채팅 화면
@main_bp.route('/chat/character/chat', methods=['GET'])
def character_chat():
    character_name = request.args.get('character')
    return render_template('character_chat.html', character_name=character_name)

# 캐릭터에게 메시지 보내는 API
@main_bp.route('/chat/character/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    character_name = data.get('character')
    question = data.get('question')
    retrieved_conversations = data.get('retrieved_conversations', [])  # 선택적으로 넘길 수도 있음

    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")

        prompt = build_prompt(character_name, question, retrieved_conversations)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 학생 고민 상담 전문 캐릭터야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        return jsonify({"response": response['choices'][0]['message']['content']})

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500