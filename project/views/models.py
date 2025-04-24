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
