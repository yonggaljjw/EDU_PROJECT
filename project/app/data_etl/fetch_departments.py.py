import requests
import pymysql
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
mysql_uri = os.getenv("MYSQL_URI")
api_key = os.getenv("CAREER_API_KEY")

# MySQL URI 파싱 함수
def parse_mysql_uri(uri):
    parsed = urlparse(uri.replace("mysql+pymysql", "mysql"))
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": parsed.username,
        "password": parsed.password,
        "db": parsed.path.lstrip("/")
    }

# OpenAPI에서 JSON 학과 데이터 가져오기
def fetch_departments():
    url = "https://www.career.go.kr/cnet/openapi/getOpenApi"
    params = {
        "apiKey": api_key,
        "svcType": "api",
        "svcCode": "SCHOOL",
        "contentType": "json",
        "gubun": "elem_list"
    }
    res = requests.get(url, params=params)
    return res.json()

# MySQL로 데이터 저장
def save_to_mysql(data):
    parsed = parse_mysql_uri(mysql_uri)
    conn = pymysql.connect(
        host=parsed["host"],
        port=parsed["port"],
        user=parsed["user"],
        password=parsed["password"],
        db=parsed["db"],
        charset="utf8mb4"
    )
    cur = conn.cursor()

    for item in data.get("dataSearch", {}).get("content", []):
        school_id = item.get("schoolSeq")
        school_name = item.get("schoolName")
        school_region = item.get("adres")

        cur.execute(
            "INSERT INTO departments (id, name, region) VALUES (%s, %s, %s)",
            (school_id, school_name, school_region)
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    json_data = fetch_departments()
    save_to_mysql(json_data)
