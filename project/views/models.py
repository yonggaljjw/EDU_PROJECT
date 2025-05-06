from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()  # ✅ 단 한 번만 선언

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    mbti = db.Column(db.String(4))
    grade_avg = db.Column(db.Float)
    interest_tags = db.Column(db.Text)
    favorite_subjects = db.Column(db.Text)
    soft_skills = db.Column(db.Text)
    target_career = db.Column(db.String(100))
    desired_region = db.Column(db.String(50))
    desired_university_type = db.Column(db.String(50))
    activities = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship('UserProfile', backref='user', uselist=False)


class JobsInfo(db.Model):
    __tablename__ = 'jobs_info'

    id = db.Column(db.Integer, primary_key=True)
    profession = db.Column(db.String(255))
    summary = db.Column(db.Text)
    similarJob = db.Column(db.String(255))
    salery = db.Column(db.String(100))
    jobdicSeq = db.Column(db.String(100))
    equalemployment = db.Column(db.String(100))
    totalCount = db.Column(db.String(100))
    aptd_type_code = db.Column(db.String(100))
    prospect = db.Column(db.String(100))
    job_ctg_code = db.Column(db.String(100))
    job_code = db.Column(db.String(100))
    job = db.Column(db.String(255))
    possibility = db.Column(db.String(100))


class SchoolEmploymentStats(db.Model):
    __tablename__ = 'school_employment_stats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    survey_date = db.Column(db.String(20))
    education_level = db.Column(db.String(50))
    school_name = db.Column(db.String(100))
    school_code = db.Column(db.BigInteger)
    school_status = db.Column(db.String(20))
    branch_type = db.Column(db.String(20))
    region = db.Column(db.String(20))
    establish_type = db.Column(db.String(20))
    course_type = db.Column(db.String(50))
    major_category = db.Column(db.String(50))
    mid_category = db.Column(db.String(50))
    minor_category = db.Column(db.String(50))
    major_code = db.Column(db.String(20))
    major_name = db.Column(db.String(100))
    graduates_total = db.Column(db.Integer)
    graduates_male = db.Column(db.Integer)
    graduates_female = db.Column(db.Integer)
    employment_rate_total = db.Column(db.Float)
    employment_rate_male = db.Column(db.Float)
    employment_rate_female = db.Column(db.Float)

class AiResult(db.Model):
    __tablename__ = 'ai_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    result = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class EmploymentFull(db.Model):
    __tablename__ = 'employment_full'

    id = db.Column(db.Integer, primary_key=True)
    survey_date = db.Column(db.String(20))
    edu_level = db.Column(db.String(50))
    school_name = db.Column(db.String(100))
    school_code = db.Column(db.String(20))
    school_status = db.Column(db.String(50))
    campus_type = db.Column(db.String(50))
    region = db.Column(db.String(50))
    establishment_type = db.Column(db.String(50))
    course_type = db.Column(db.String(50))
    major_group = db.Column(db.String(50))
    mid_major = db.Column(db.String(100))
    sub_major = db.Column(db.String(100))
    dept_code = db.Column(db.String(50))
    dept_name = db.Column(db.String(100))
    degree_type = db.Column(db.String(50))
    graduates_total = db.Column(db.Integer)
    graduates_male = db.Column(db.Integer)
    graduates_female = db.Column(db.Integer)
    emp_rate_total = db.Column(db.Float)
    emp_rate_male = db.Column(db.Float)
    emp_rate_female = db.Column(db.Float)
    employed_total = db.Column(db.Integer)
    employed_male = db.Column(db.Integer)
    employed_female = db.Column(db.Integer)
    취업자_교외취업자_계 = db.Column(db.Integer)
    취업자_교외취업자_남 = db.Column(db.Integer)
    취업자_교외취업자_여 = db.Column(db.Integer)
    취업자_교내취업자_계 = db.Column(db.Integer)
    취업자_교내취업자_남 = db.Column(db.Integer)
    취업자_교내취업자_여 = db.Column(db.Integer)
    취업자_해외취업자_계 = db.Column(db.Integer)
    취업자_해외취업자_남 = db.Column(db.Integer)
    취업자_해외취업자_여 = db.Column(db.Integer)
    취업자_농림어업종사자_계 = db.Column(db.Integer)
    취업자_농림어업종사자_남 = db.Column(db.Integer)
    취업자_농림어업종사자_여 = db.Column(db.Integer)
    취업자_개인창작활동종사자_계 = db.Column(db.Integer)
    취업자_개인창작활동종사자_남 = db.Column(db.Integer)
    취업자_개인창작활동종사자_여 = db.Column(db.Integer)
    취업자_1인창_사_업자_계 = db.Column("취업자_1인창(사)업자_계", db.Integer)
    취업자_1인창_사_업자_남 = db.Column("취업자_1인창(사)업자_남", db.Integer)
    취업자_1인창_사_업자_여 = db.Column("취업자_1인창(사)업자_여", db.Integer)
    취업자_프리랜서_계 = db.Column(db.Integer)
    취업자_프리랜서_남 = db.Column(db.Integer)
    취업자_프리랜서_여 = db.Column(db.Integer)
    advance_rate_total = db.Column(db.Float)
    advance_rate_male = db.Column(db.Float)
    advance_rate_female = db.Column(db.Float)
    advanced_total = db.Column(db.Integer)
    advanced_male = db.Column(db.Integer)
    advanced_female = db.Column(db.Integer)

# class CharacterChatState(db.Model):
#     __tablename__ = 'character_chat_state'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     character_name = db.Column(db.String(50), nullable=False)
#     speech_permission = db.Column(db.Boolean, default=False)
#     updated_at = db.Column(db.DateTime)
    
#     user = db.relationship('User', backref=db.backref('chat_states', lazy=True))


class CharacterChatHistory(db.Model):
    __tablename__ = 'character_chat_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # ✅ users.id 참조
    character_name = db.Column(db.String(50), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    character_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('chat_histories', lazy=True))
