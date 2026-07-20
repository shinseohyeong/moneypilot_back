# ==========================================
# 파일 위치 :
# moneypilot_back/app/parser/vision_parser.py
# 역할 : OpenAI Vision으로 카드 거래명세서 파싱
# ==========================================
from openai import OpenAI
import json
import base64
from pathlib import Path
import os
from fastapi import HTTPException

client = OpenAI()

PROMPT = """
이 파일은 {card_name}카드 거래명세서입니다.

모든 거래내역을 아래 JSON 배열 형식으로 반환하세요.

[
  {
    "transaction_date": "2026-01-10",
    "merchant_name": "스타벅스",
    "amount": 6500,
    "description": "일시불",
    "category": "카페",
    "expense_type": "VARIABLE",
    "is_recurring": false
  }
]

규칙

1. 누락된 거래를 임의로 생성하지 마세요.
2. amount는 반드시 숫자(integer)만 반환하세요.
3. transaction_date는 반드시 YYYY-MM-DD 형식 문자열로 반환하세요.
4. description은 반드시 문자열입니다.
5. JSON 배열만 출력하세요.
6. ```json 같은 마크다운은 출력하지 마세요.

카테고리(category) 규칙

다음 중 하나만 선택하세요.

- 식비
- 카페
- 교통
- 쇼핑
- 생활
- 의료
- 문화
- 교육
- 통신
- 주거
- 금융
- 여행
- 기타

가맹점 이름을 보고 가장 적절한 카테고리를 추론하세요.

예시

스타벅스 → 카페
메가커피 → 카페
이디야 → 카페
맥도날드 → 식비
버거킹 → 식비
배달의민족 → 식비
쿠팡 → 쇼핑
11번가 → 쇼핑
올리브영 → 생활
다이소 → 생활
GS25 → 생활
CU → 생활
지하철 → 교통
버스 → 교통
SRT → 교통
KTX → 교통
넷플릭스 → 문화
CGV → 문화
교보문고 → 교육

expense_type 규칙

다음 둘 중 하나만 반환하세요.

- FIXED
- VARIABLE

다음과 같은 경우 FIXED로 판단합니다.

- 통신요금
- 관리비
- 월세
- 보험료
- 정기구독
- OTT
- 인터넷
- 헬스장
- 정기결제

그 외 대부분의 소비는 VARIABLE입니다.

is_recurring 규칙

반복적으로 발생하는 지출이면 true,
일반적인 일회성 소비면 false입니다.

예시

넷플릭스 → true
유튜브 프리미엄 → true
멜론 → true
통신요금 → true
보험료 → true
관리비 → true
월세 → true
헬스장 → true

스타벅스 → false
맥도날드 → false
쿠팡 → false
올리브영 → false
다이소 → false

판단이 어려우면

category = "기타"
expense_type = "VARIABLE"
is_recurring = false

를 사용하세요.
"""

# ==========================================
# 파일 base64 인코딩
# ==========================================
def encode_file(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(
                f.read()
            ).decode("utf-8")

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="파일을 찾을 수 없습니다."
        )

# ==========================================
# Vision 입력 생성
# ==========================================
def make_file_content(file_path: str):
    suffix = Path(file_path).suffix.lower()
    file_base64 = encode_file(file_path)
    if suffix in [".png", ".jpg", ".jpeg"]:
        return {
            "type": "input_image",
            "image_url": f"data:image/{suffix[1:]};base64,{file_base64}"
        }

    elif suffix == ".pdf":
        return {
            "type": "input_file",
            "filename": Path(file_path).name,
            "file_data": f"data:application/pdf;base64,{file_base64}"
        }
    
    elif suffix in [".xlsx", ".xls", ".csv"]:
        return {
            "type": "input_file",
            "filename": Path(file_path).name,
            "file_data": (
                "data:application/octet-stream;base64,"
                + file_base64
            )
        }

    raise HTTPException(
        status_code=400,
        detail="지원하지 않는 파일 형식입니다."
    )

# ==========================================
# Vision으로 카드 거래명세서 파싱
# ==========================================
def vision_parser(file_path: str):
    try:
        response = client.responses.create(
            model=os.getenv(
                "OPENAI_MODEL",
                "gpt-4o"
            ),
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": PROMPT
                        },
                        make_file_content(file_path)
                    ]
                }
            ]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Vision API 호출 실패 : {str(e)}"
        )

    result = (
        response.output_text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        return json.loads(result)

    except json.JSONDecodeError:

        print(result)

        raise HTTPException(
            status_code=400,
            detail="Vision 응답을 JSON으로 변환하지 못했습니다."
        )