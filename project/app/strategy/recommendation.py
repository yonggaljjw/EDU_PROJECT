#  진로/입시 추천 전략 비즈니스 로직 준비 중

def generate_strategy(data):
    interest = data.get("interest")
    score = data.get("score")
    location = data.get("location")

    if interest == "engineering" and score >= 90:
        return {"recommended_major": "Computer Science", "university": "KAIST"}
    elif interest == "business":
        return {"recommended_major": "Business Administration", "university": "Korea University"}
    else:
        return {"recommended_major": "Liberal Arts", "university": "Chung-Ang University"}
