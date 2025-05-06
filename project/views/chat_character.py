# 캐릭터 챗봇 메인 코드

import os
import openai
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from views.character_prompt import character_prompts, build_prompt

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# Elasticsearch 설정
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
es = Elasticsearch(ELASTICSEARCH_URL)

# 검색할 인덱스명 설정
COUNSELING_INDEX = "elementary_school_counseling"  # 기본값 (필요에 따라 변경)

def search_similar_conversations(student_question, top_k=5):
    """
    Elasticsearch에서 학생 질문과 유사한 상담 기록 검색

    Args:
        student_question (str): 학생 질문
        top_k (int): 검색할 결과 수

    Returns:
        list: 검색된 상담 기록 텍스트 리스트
    """
    query = {
        "size": top_k,
        "query": {
            "match": {
                "상담내용": {
                    "query": student_question
                }
            }
        }
    }
    
    response = es.search(index=COUNSELING_INDEX, body=query)
    hits = response["hits"]["hits"]
    results = [hit["_source"]["상담내용"] for hit in hits]
    
    return results

def generate_character_response(character_name, student_question):
    """
    캐릭터 설정을 반영해 답변 생성

    Args:
        character_name (str): "hanul", "jihan", "isol" 중 하나
        student_question (str): 학생 질문

    Returns:
        str: 생성된 답변
    """
    # 유사 상담 기록 검색
    retrieved_conversations = search_similar_conversations(student_question)

    # 최종 프롬프트 생성
    prompt = build_prompt(character_name, student_question, retrieved_conversations)

    # OpenAI GPT 호출
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 또는 "gpt-3.5-turbo" 사용 가능
        messages=[
            {"role": "system", "content": "너는 학생 상담을 도와주는 친절한 조언자야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    answer = response['choices'][0]['message']['content'].strip()
    return answer

# (선택) 테스트용 메인 실행
if __name__ == "__main__":
    character_name = "하늘"  # 테스트할 캐릭터 ("하늘", "지한", "이솔")
    student_question = "저는 꿈이 없는데 어떻게 진로를 정해야 할까요?"
    
    reply = generate_character_response(character_name, student_question)
    print("\n[캐릭터 답변]\n", reply)
