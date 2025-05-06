from flask import Blueprint,current_app, render_template, request, redirect, url_for, flash, jsonify, session
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
from views.character_prompt import build_prompt, generate_greeting # 캐릭터챗 프롬프트 불러오기
from views.models import db, CharacterChatHistory # 캐릭터 챗 대화 저장용



main_bp = Blueprint('main', __name__)


# 공통 함수: 모든 템플릿에 로그인 상태 전달
def get_template_context():
    """모든 템플릿에 공통으로 전달할 컨텍스트를 반환합니다."""
    is_logged_in = 'user_id' in session
    return {'is_logged_in': is_logged_in}

@main_bp.route('/')
def home():
    if request.args.get('force_reload'):
        return redirect(url_for('main.home'))  # 서버 쪽에서 강제 리다이렉트 처리

    profile = None
    job_detail = None

    # 세션 상태 확인
    is_logged_in = 'user_id' in session

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

    if is_logged_in:
        profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
        if profile and profile.target_career:
            job_detail = JobsInfo.query.filter_by(job=profile.target_career).first()

    return render_template(
        'index.html',
        profile=profile,
        job_detail=job_detail,
        random_schools=random_schools,
        random_jobs=random_jobs,
        is_logged_in=is_logged_in
    )

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    # 이미 로그인 되어있으면 홈으로
    if 'user_id' in session:
        return redirect(url_for('main.home'))
        
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

    return render_template('register.html', **get_template_context())


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 이미 로그인 되어있으면 홈으로
    if 'user_id' in session:
        return redirect(url_for('main.home'))
        
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

    return render_template('login.html', **get_template_context())


@main_bp.route('/logout')
def logout():
    session.clear()
    flash("로그아웃 되었습니다.")
    # 강제 새로고침 추가_로그인/아웃 리다이렉트 위함
    return redirect(url_for('main.home', force_reload=1))


@main_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))

    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
    if profile:
        return render_template('profile.html', profile=profile, **get_template_context())
    else:
        flash("아직 프로필 정보가 없습니다. 테스트를 진행해주세요.")
        return redirect(url_for('main.profile_setup'))


@main_bp.route('/profile/setup', methods=['GET', 'POST'])
def profile_setup():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))

    # 기존 프로필 확인
    existing_profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
    if existing_profile:
        # 이미 프로필이 있으면 edit 페이지로 리다이렉트
        flash("프로필이 이미 존재합니다. 수정 페이지로 이동합니다.")
        return redirect(url_for('main.profile_edit'))

    job_list = JobsInfo.query.with_entities(JobsInfo.job).distinct().order_by(JobsInfo.job).all()
    job_list = [job[0] for job in job_list if job[0]]

    next_page = request.args.get('next')  # ✅ 추가

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

        # ✅ 저장 후 next 파라미터가 있으면 그쪽으로 이동
        if next_page == 'recommend_ai':
            return redirect(url_for('main.recommend_ai'))
        else:
            return redirect(url_for('main.profile'))

    # 빈 프로필 폼 제공 (profile=None)
    return render_template('profile_setup.html', profile=None, job_list=job_list, next_page=next_page, **get_template_context())

@main_bp.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))

    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
    if not profile:
        flash("프로필이 없습니다. 먼저 작성해주세요.")
        return redirect(url_for('main.profile_setup'))

    # 직업 목록 불러오기
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

    return render_template('profile_edit.html', profile=profile, job_list=job_list, **get_template_context())


@main_bp.route('/recommend')
def recommend():
    return render_template('recommend.html', **get_template_context())

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


# 나머지 라우트 함수 (위의 패턴 적용)
@main_bp.route('/recommend/ai', methods=['GET', 'POST'])
def recommend_ai():
    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect(url_for('main.login'))

    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()

    if not profile:
        flash("AI 분석을 위해 먼저 프로필을 작성해주세요.")
        return redirect(url_for('main.profile_setup', next='recommend_ai'))

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

    return render_template("recommend_ai.html", profile=profile, questions=questions, **get_template_context())

@main_bp.route('/recommend/result')
def recommend_result():
    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect(url_for('main.login'))
        
    result_id = request.args.get('result_id')
    ai_result = AiResult.query.filter_by(id=result_id, user_id=session['user_id']).first()
    if not ai_result:
        flash("결과를 찾을 수 없습니다.")
        return redirect(url_for('main.recommend_ai'))
    return render_template('recommend_result.html', result=ai_result.result, **get_template_context())

@main_bp.route('/history')
def history():
    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect(url_for('main.login'))

    results = AiResult.query.filter_by(user_id=session['user_id']).order_by(AiResult.created_at.desc()).all()
    return render_template("history.html", results=results, **get_template_context())


@main_bp.route('/vision/plan', methods=['GET', 'POST'])
def vision_plan():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        goal = request.form.get('goal')
        age = int(request.form.get('age'))
        year = request.form.get('year')
        army = request.form.get('army')

        # ✅ 군 복무 반영 로직
        if age < 18 or '고등학교' in year:
            army_info = "군 복무는 현재 고려하지 않아도 됩니다."
        else:
            if army == "군 복무 예정":
                army_info = "군 복무 예정이므로 복무 기간(약 1년 6개월~2년)은 온라인 학습, 자격증 준비 등에 활용하세요."
            else:
                army_info = "군 복무 계획이 없으므로 바로 진학 또는 취업 준비를 하세요."

        # ✅ GPT 프롬프트 구성
        prompt = f"""
당신은 학생 맞춤형 커리어 플랜을 현실적으로 설계하는 전문가입니다.

[사용자 정보]
- 목표: {goal}
- 현재 나이: {age}세
- 현재 학년/상태: {year}
- 군 복무 관련: {army_info}

[요청사항]
- 학생의 현재 학년과 나이를 반영하여 현실적이고 자연스러운 커리어 플랜을 세우세요.
- 중학생은 기초 학습 위주, 고등학생은 비교과 활동과 진학 준비를, 대학생 이상은 전공 심화 및 취업 준비를 중심으로 계획하세요.
- 군 복무가 필요한 경우에는 적절한 시기에 반영하세요.
- **1년 차: ~**, **2년 차: ~** 이런 식으로 연차별 구분해서 작성하세요.
- 1년 차부터 5년 차까지 연차별 목표를 자연스러운 문단 설명 형식으로 제시하세요.
- 전체 분량은 간결하게 7~9문장 이내로 작성하세요.
"""

        import openai
        import re

        openai.api_key = os.getenv("OPENAI_API_KEY")

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "너는 현실적이고 간결한 문단형 커리어 플랜 전문가야."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=700
            )
            plan_text = response['choices'][0]['message']['content']
            plan_lines = plan_text.split('\n')
            plan_steps = [re.sub(r'\*\*(.*?)\*\*', r'\1', line.strip()) for line in plan_lines if line.strip()]
        except Exception as e:
            plan_steps = [f"AI 호출 중 오류가 발생했습니다: {str(e)}"]

        # ✅ 세션에 저장 후 결과 페이지로 이동
        session['plan_steps'] = plan_steps
        session['goal'] = goal
        return redirect(url_for('main.vision_plan_result'))

    return render_template('vision_plan.html', **get_template_context())
@main_bp.route('/vision/plan/result', methods=['GET'])
def vision_plan_result():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))

    # ✅ 세션에서 pop으로 읽어오고 제거
    plan_steps = session.pop('plan_steps', None)
    goal = session.pop('goal', None)

    if not plan_steps or not goal:
        flash("잘못된 접근입니다.")
        return redirect(url_for('main.vision_plan'))

    return render_template(
        'vision_plan_result.html',
        plan_steps=plan_steps,
        goal=goal,
        **get_template_context()
    )




# 캐릭터 챗
# 💬 캐릭터 코드 ↔ 한글 이름 매핑
character_name_mapping = {
    "hanul": "하늘",
    "jihan": "지한",
    "isol": "이솔"
}

# 캐릭터 선택 화면
@main_bp.route('/chat/character/select')
def select_character():
    if 'user_id' not in session:
        flash("로그인 후 이용해주세요.")
        return redirect(url_for('main.login'))
    
    return render_template('character_select.html', **get_template_context())

# 캐릭터 채팅 화면 열기
@main_bp.route('/chat/character/chat', methods=['GET'])
def character_chat():
    character_code = request.args.get('character')  # 이제 'hanul', 'jihan' 같은 코드가 옴
    character_display_name = character_name_mapping.get(character_code, "알 수 없는 캐릭터")
    return render_template('character_chat.html', character_code=character_code, character_display_name=character_display_name, **get_template_context())


# LLM 호출 함수
def call_llm_api(prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 학생 고민 상담을 돕는 캐릭터야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=200
    )
    return response['choices'][0]['message']['content'].strip()

# 캐릭터 첫 인사말 API
@main_bp.route('/chat/character/get_greeting', methods=['POST'])
def get_character_greeting():
    data = request.json
    character_code = data.get('character', '')

    greeting = generate_greeting(character_code)

    return jsonify({"greeting": greeting})


# 캐릭터 메시지 보내는 API
@main_bp.route('/chat/character/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    character_code = data.get('character')  # 'hanul', 'jihan', 'isol'
    question = data.get('question')
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "로그인이 필요합니다."}), 401

    try:
        # 지한 캐릭터의 경우, 이전 대화 기록을 확인하여 반말 허락 여부 확인
        speech_style_permission = False
        conversation_history = []
        
        if character_code == "jihan":
            # 최근 대화 이력 가져오기
            recent_chats = CharacterChatHistory.query.filter_by(
                user_id=user_id,
                character_name=character_code
            ).order_by(CharacterChatHistory.timestamp.desc()).limit(10).all()
            
            # 대화 이력을 시간순으로 정렬
            recent_chats.reverse()
            
            # 대화 이력 구성
            for chat in recent_chats:
                conversation_history.append(f"지한: {chat.character_response}")
                conversation_history.append(f"학생: {chat.user_message}")
                
                # 반말 허락 여부 검사
                if "반말" in chat.character_response and ("괜찮" in chat.user_message or 
                                                        "좋" in chat.user_message or 
                                                        "해도 돼" in chat.user_message):
                    speech_style_permission = True
        
        # 최근 대화 기록 (검색된 상담 기록 대신 실제 대화 기록 활용)
        retrieved_conversations = conversation_history[-6:] if conversation_history else []
        
        # 지한 캐릭터의 반말 상태를 프롬프트에 추가
        prompt = build_prompt(character_code, question, retrieved_conversations)
        
        if character_code == "jihan" and speech_style_permission:
            prompt += "\n\n[중요] 학생이 이미 반말을 허락했습니다. 반말을 사용하세요."
        
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 학생 고민 상담 전문 캐릭터야. 각 캐릭터의 말투와 성격을 정확히 유지해."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        character_response = response['choices'][0]['message']['content']

        # 프롬프트 노출 방지를 위한 후처리
        filtered_lines = []
        for line in character_response.split('\n'):
            if not any(keyword in line.lower() for keyword in 
                    ['[캐릭터', '[말투', '[응답', '[지시', '[중요', '[상담', '규칙']):
                filtered_lines.append(line)
        
        character_response = '\n'.join(filtered_lines).strip()

        # 대화 이력 저장
        chat_log = CharacterChatHistory(
            user_id=user_id,
            character_name=character_code,
            user_message=question,
            character_response=character_response
        )
        db.session.add(chat_log)
        db.session.commit()

        return jsonify({"response": character_response})

    except Exception as e:
        logging.error("❌ 캐릭터 메시지 송수신 실패: %s", traceback.format_exc())
        return jsonify({"error": "서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."}), 500

# 캐릭터 대화 히스토리 조회 화면
@main_bp.route('/chat/character/history/<character_name>', methods=['GET'])
def character_chat_history(character_name):
    # 최근 50개까지만 조회 (너가 원하는 만큼 조정 가능)
    histories = CharacterChatHistory.query.filter_by(character_name=character_name).order_by(CharacterChatHistory.timestamp.asc()).limit(50).all()
    return render_template('character_history.html', character_name=character_name, histories=histories, **get_template_context())



# 게시글 데이터
community_data = {
    "경영학": [
        "🔔 [모집] 2025 상반기 경영학 세미나 참가자 모집",
        "🔔 [스터디] 경영 전략 케이스 스터디 팀원 모집",
        "🔔 [정보] 국내 MBA 과정 설명회 일정 공유",
        "🔔 [모집] 2025 취업 대비 경영학 모의면접반 모집",
        "🔔 [소식] 경영학과 신입생 오리엔테이션 일정 발표"
    ],
    "데이터 분석": [
        "🔔 [공모전] 제 7회 교육부 데이터 분석 공모전 개최",
        "🔔 [모집] 파이썬 데이터 분석 스터디 (초급반)",
        "🔔 [모집] SQL 데이터 처리 실습 그룹원 모집",
        "🔔 [뉴스] 2025년 빅데이터 산업 트렌드 리포트 발간",
        "🔔 [정보] Kaggle 대회 초보자 가이드 정리"
    ],
    "예술고": [
        "🔔 [모집] 26년 00 예고 보컬 연습팀 멤버 찾습니다",
        "🔔 [공지] 예고 입시 대비 포트폴리오 설명회 개최",
        "🔔 [모집] 미술대학 입시 대비 모의면접반 참여자 모집",
        "🔔 [소식] 2025 전국 청소년 연극제 참가 안내",
        "🔔 [모집] 무용 전공 예비고1 워크숍 프로그램 오픈"
    ]
}

@main_bp.route('/community')
def community():
    return render_template('community.html', **get_template_context())