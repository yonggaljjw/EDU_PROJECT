from flask import Flask, request, jsonify
import joblib
import numpy as np

# Flask 앱 생성
app = Flask(__name__)

# 저장된 KNN 모델 불러오기 (joblib)
knn_model = joblib.load("knn_model.joblib")

def recommend_jobs(aptit_name, wlb, social, satisfication, wage, knowledge, ability, model, k=3):
    """
    사용자 입력을 바탕으로 상위 k개 직업을 추천하는 함수
    """
    # 입력 데이터 생성
    input_data = pd.DataFrame({
        'aptit_name': [aptit_name],
        'wlb': [wlb],
        'social': [social],
        'satisfication': [satisfication],
        'wage': [wage],
        'knowledge': [knowledge],
        'ability': [ability]
    })
    
    # 예측 확률 계산
    proba = model.predict_proba(input_data)
    
    # 상위 k개 클래스 인덱스 추출
    top_k_indices = np.argsort(proba[0])[-k:][::-1]
    
    # 클래스 인덱스를 클래스 이름으로 변환
    classes = model.classes_
    top_k_jobs = [classes[idx] for idx in top_k_indices]
    
    # 확률과 함께 추천 직업 반환
    job_probs = [(top_k_jobs[i], proba[0][top_k_indices[i]] * 100) for i in range(len(top_k_jobs))]
    
    return job_probs

# 예측 API
@app.route("/ml_model", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        
        # 사용자 입력 데이터 추출
        aptit_name = data.get("aptit_name")
        wlb = data.get("wlb")
        social = data.get("social")
        satisfication = data.get("satisfication")
        wage = data.get("wage")
        knowledge = data.get("knowledge")
        ability = data.get("ability")
        
        # recommend_jobs 함수 호출하여 직업 추천 받기
        job_recommendations = recommend_jobs(
            aptit_name, wlb, social, satisfication, wage, 
            knowledge, ability, knn_model
        )
        
        # 결과를 JSON 형식으로 변환
        results = []
        for job, probability in job_recommendations:
            results.append({
                "job": job,
                "probability": probability
            })
        
        return jsonify({"recommendations": results})
    except Exception as e:
        return jsonify({"error": str(e)})

# 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)