import os
import json
import glob
import requests
from dotenv import load_dotenv
import logging
from tqdm import tqdm

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://221.155.195.6:59200")

# 데이터 폴더 기본 경로 설정
BASE_DIR = "C:/Users/wjd_w/Desktop/공모전/교육부/chat_data"

# Elasticsearch HTTP 클라이언트
class ElasticsearchHTTP:
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.bulk_headers = {"Content-Type": "application/x-ndjson", "Accept": "application/json"}

    def check_server(self):
        """서버 연결 확인"""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                info = response.json()
                version = info.get('version', {}).get('number', 'unknown')
                logger.info(f"Elasticsearch 서버 버전: {version}")
                return True
            else:
                logger.error(f"서버 연결 확인 실패: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"서버 연결 오류: {str(e)}")
            return False
    
    def index_exists(self, index_name):
        """인덱스 존재 여부 확인"""
        try:
            response = requests.head(f"{self.base_url}/{index_name}", headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"인덱스 확인 오류: {str(e)}")
            return False
    
    def create_index(self, index_name):
        """인덱스 생성"""
        try:
            if self.index_exists(index_name):
                logger.info(f"인덱스가 이미 존재합니다: {index_name}")
                return True
            
            # 매핑 설정
            mappings = {
                "mappings": {
                    "properties": {
                        "학생ID": {"type": "keyword"},
                        "상담사ID": {"type": "keyword"},
                        "학교급": {"type": "keyword"},
                        "지역": {"type": "keyword"},
                        "성별": {"type": "keyword"},
                        "상담목적": {"type": "text"},
                        "상담만족도": {"type": "integer"},
                        "상담내용": {"type": "text", "analyzer": "standard"},
                        "대화카테고리": {"type": "keyword"},
                        "자기평가": {"type": "integer"}
                    }
                }
            }
            
            response = requests.put(
                f"{self.base_url}/{index_name}",
                headers=self.headers,
                json=mappings
            )
            
            if response.status_code in (200, 201):
                logger.info(f"인덱스 생성 완료: {index_name}")
                return True
            else:
                logger.error(f"인덱스 생성 실패: HTTP {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"인덱스 생성 오류: {str(e)}")
            return False
    
    def create_student_info_index(self, index_name):
        """학생 기초정보 인덱스 생성"""
        try:
            if self.index_exists(index_name):
                logger.info(f"인덱스가 이미 존재합니다: {index_name}")
                return True
            
            # 학생 기초정보 매핑 설정
            mappings = {
                "mappings": {
                    "properties": {
                        "학생ID": {"type": "keyword"},
                        "학교급": {"type": "keyword"},
                        "학년": {"type": "keyword"},
                        "반": {"type": "keyword"},
                        "성별": {"type": "keyword"},
                        "지역": {"type": "keyword"}
                    }
                }
            }
            
            response = requests.put(
                f"{self.base_url}/{index_name}",
                headers=self.headers,
                json=mappings
            )
            
            if response.status_code in (200, 201):
                logger.info(f"학생 기초정보 인덱스 생성 완료: {index_name}")
                return True
            else:
                logger.error(f"인덱스 생성 실패: HTTP {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"인덱스 생성 오류: {str(e)}")
            return False
    
    def bulk_index(self, index_name, documents):
        """벌크 인덱싱 수행"""
        if not documents:
            logger.warning(f"업로드할 문서가 없습니다: {index_name}")
            return False
        
        try:
            # Elasticsearch 벌크 API 형식으로 변환
            bulk_data = ""
            for doc in documents:
                # 메타데이터 라인
                bulk_data += json.dumps({"index": {"_index": index_name}}) + "\n"
                # 문서 데이터 라인
                bulk_data += json.dumps(doc, ensure_ascii=False) + "\n"
            
            # 벌크 API 호출
            response = requests.post(
                f"{self.base_url}/_bulk",
                headers=self.bulk_headers,
                data=bulk_data.encode('utf-8')
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                if result.get("errors", True):
                    # 오류가 있지만 일부 성공
                    success_count = sum(1 for item in result.get("items", []) 
                                       if item.get("index", {}).get("status") < 300)
                    error_count = sum(1 for item in result.get("items", []) 
                                     if item.get("index", {}).get("status") >= 300)
                    logger.warning(f"벌크 인덱싱 부분 성공: {success_count}개 성공, {error_count}개 실패")
                    if error_count > 0 and 'items' in result:
                        # 첫 번째 오류 메시지 출력
                        error_item = next((item for item in result['items'] if item.get('index', {}).get('status', 0) >= 300), None)
                        if error_item:
                            logger.error(f"오류 예시: {error_item['index'].get('error')}")
                    return success_count > 0
                else:
                    # 모두 성공
                    logger.info(f"벌크 인덱싱 성공: {len(documents)}개 문서")
                    return True
            else:
                logger.error(f"벌크 인덱싱 실패: HTTP {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"벌크 인덱싱 오류: {str(e)}")
            return False

# JSON 파일 읽기
def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        # UTF-8 디코딩 실패 시 CP949 인코딩 시도
        try:
            with open(file_path, 'r', encoding='cp949') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"CP949 인코딩으로 JSON 파일 읽기 오류: {file_path} - {str(e)}")
            return None
    except Exception as e:
        logger.error(f"JSON 파일 읽기 오류: {file_path} - {str(e)}")
        return None

# 대화 내용 병합
def merge_utterances(utterances):
    if not utterances:
        return ""
    
    texts = []
    for u in utterances:
        speaker = "학생" if u.get('speaker_idx', '').startswith('S') else "교사"
        text = u.get('utterance', '').replace("[이모티콘]", "").strip()
        texts.append(f"{speaker}: {text}")
    
    return " ".join(texts)

# 상담 기록 문서 변환
def transform_counseling_document(doc_key, doc_value, school_type=None):
    if not isinstance(doc_value, dict):
        return []
    
    meta = doc_value.get('meta', {})
    conversations = doc_value.get('conversation', [])
    
    student_id = meta.get('student_idx')
    teacher_id = meta.get('counsellor_idx')
    counselling_date = meta.get('counselling_date')
    satisfaction = meta.get('counselling_satisfaction')
    purpose = meta.get('counselling_purpose')
    
    results = []
    for conv in conversations:
        conv_text = merge_utterances(conv.get('utterances', []))
        conv_category = conv.get('conv_category', '')
        self_eval = conv.get('self_eval', [0])[0] if conv.get('self_eval') else 0
        
        new_doc = {
            "학생ID": student_id,
            "상담사ID": teacher_id,
            "상담목적": purpose,
            "상담만족도": satisfaction,
            "상담내용": conv_text,
            "대화카테고리": conv_category,
            "자기평가": self_eval
        }
        
        if school_type:
            new_doc["학교급"] = school_type
        
        results.append(new_doc)
    
    return results

# 학생 기초정보 문서 변환
def transform_student_info_document(doc_data, school_type=None):
    if not isinstance(doc_data, dict):
        return []
    
    results = []
    for student_id, info in doc_data.items():
        if not isinstance(info, dict):
            continue
        
        new_doc = {
            "학생ID": student_id,
            "학년": info.get('grade'),
            "반": info.get('class'),
            "성별": info.get('gender'),
            "지역": info.get('region')
        }
        
        if school_type:
            new_doc["학교급"] = school_type
        
        results.append(new_doc)
    
    return results

# 주어진 디렉토리에서 JSON 파일 찾기
def find_json_files(directory):
    return glob.glob(os.path.join(directory, "**/*.json"), recursive=True)

# 폴더 구조 탐색
def scan_directory(directory):
    data_folders = []
    
    # 디렉토리가 존재하는지 확인
    if not os.path.exists(directory):
        logger.error(f"디렉토리가 존재하지 않습니다: {directory}")
        return data_folders
    
    try:
        # 디렉토리 내의 모든 하위 디렉토리 탐색
        for root, dirs, files in os.walk(directory):
            # JSON 파일이 있는 디렉토리만 추가
            if any(file.endswith('.json') for file in files):
                data_folders.append(root)
        
        logger.info(f"{len(data_folders)}개의 데이터 폴더 발견")
        return data_folders
    except Exception as e:
        logger.error(f"디렉토리 탐색 중 오류 발생: {str(e)}")
        return []

# 인덱스 이름 결정
def get_index_name(file_path):
    # 학교급에 따른 인덱스 이름 결정
    if "초등" in file_path:
        school_type = "elementary"
    elif "중등" in file_path or "중학교" in file_path:
        school_type = "middle"
    elif "고등" in file_path:
        school_type = "high"
    else:
        school_type = "common"
    
    # 상담 기록 또는 학생 기초정보에 따른 구분
    if "상담기록" in file_path:
        return f"{school_type}_school_counseling", school_type
    elif "학생기초정보" in file_path:
        return f"{school_type}_school_student_info", school_type
    elif "기술계열" in file_path:
        return f"{school_type}_school_technical", school_type
    elif "서비스계열" in file_path:
        return f"{school_type}_school_service", school_type
    elif "생산계열" in file_path:
        return f"{school_type}_school_production", school_type
    elif "사무계열" in file_path:
        return f"{school_type}_school_office", school_type
    else:
        return f"{school_type}_school", school_type

# 메인 함수 - 데이터 처리 및 Elasticsearch 업로드
def process_and_upload_data(training_mode=True):
    # Elasticsearch HTTP 클라이언트 생성
    es_http = ElasticsearchHTTP(ELASTICSEARCH_URL)
    
    # 서버 연결 확인
    if not es_http.check_server():
        logger.error("Elasticsearch 서버 연결 실패. 데이터 처리를 중단합니다.")
        return
    
    # 처리할 디렉토리 설정 (Training 또는 Validation)
    if training_mode:
        target_dir = os.path.join(BASE_DIR, "Training")
    else:
        target_dir = os.path.join(BASE_DIR, "Validation")
    
    logger.info(f"처리 시작: {target_dir}")
    
    # JSON 파일 찾기
    json_files = find_json_files(target_dir)
    logger.info(f"{len(json_files)}개의 JSON 파일 발견")
    
    for json_file in tqdm(json_files, desc="파일 처리 중"):
        # JSON 데이터 읽기
        data = read_json_file(json_file)
        if not data:
            continue
        
        # 인덱스 이름 결정
        index_name, school_type = get_index_name(json_file)
        
        # 인덱스 생성
        if "student_info" in index_name:
            es_http.create_student_info_index(index_name)
            # 학생 기초정보 문서 변환
            documents = transform_student_info_document(data, school_type)
        else:
            es_http.create_index(index_name)
            # 상담 기록 문서 변환
            documents = []
            for key, value in data.items():
                transformed_docs = transform_counseling_document(key, value, school_type)
                documents.extend(transformed_docs)
        
        # 청크 단위로 분할하여 벌크 업로드
        MAX_CHUNK_SIZE = 1000
        for i in range(0, len(documents), MAX_CHUNK_SIZE):
            chunk = documents[i:i + MAX_CHUNK_SIZE]
            es_http.bulk_index(index_name, chunk)

if __name__ == "__main__":
    try:
        logger.info(f"전처리 및 필드 축소 Elasticsearch 데이터 적재 스크립트 시작")
        logger.info(f"URL: {ELASTICSEARCH_URL}")
        
        # Training 데이터 처리
        logger.info("Training 데이터 처리 시작")
        process_and_upload_data(training_mode=True)
        
        # Validation 데이터 처리
        logger.info("Validation 데이터 처리 시작")
        process_and_upload_data(training_mode=False)
        
        logger.info("모든 데이터 처리 완료")
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {str(e)}")