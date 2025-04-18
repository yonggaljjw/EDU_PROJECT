# 환경설정 클래스를 정의하는 파일

import os
from dotenv import load_dotenv

# .env 파일 로딩
load_dotenv()

class Config:
    # MySQL 데이터베이스 설정
    SQLALCHEMY_DATABASE_URI = os.getenv("MYSQL_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Elasticsearch 설정 (직접 연결할 경우 사용 가능)
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
