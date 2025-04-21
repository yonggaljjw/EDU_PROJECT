# 진로 추천 기능

from flask import Blueprint, request, jsonify
from app.strategy.recommendation import generate_strategy

strategy_bp = Blueprint('strategy', __name__)

@strategy_bp.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    result = generate_strategy(data)
    return jsonify(result)
