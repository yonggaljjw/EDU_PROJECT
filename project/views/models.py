from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

 
    # 1:1 관계 설정
    profile = db.relationship('UserProfile', backref='user', uselist=False)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mbti = db.Column(db.String(4))
    interest_tags = db.Column(db.Text)
    favorite_subjects = db.Column(db.Text)
    strength_subjects = db.Column(db.Text)
    desired_region = db.Column(db.String(50))
    target_career = db.Column(db.String(100))
    activities = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
