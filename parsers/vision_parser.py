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

client = OpenAI()

# ==========================================
# 파일 base64 인코딩
# ==========================================
def encode_file(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# ==========================================
# Vision 입력 데이터 생성
# ==========================================
def make_file_content(file_path: str) -> dict:
    suffix = Path(file_path).suffix.lower()
    file_base64 = encode_file(file_path)

    # 이미지
    if suffix in [".png", ".jpg", ".jpeg"]:
        return {
            "type": "input_image",
            "image_url": f"data:image/{suffix[1:]};base64,{file_base64}",
        }

    # PDF
    return {
        "type": "input_file",
        "filename": Path(file_path).name,
        "file_data": file_base64,
    }


# ==========================================
# Vision으로 카드 거래명세서 파싱
# ==========================================
def parse_card_statement(file_path: str):
    prompt = """
    이 파일은 카드 거래명세서입니다.
    모든 거래내역을 아래 JSON 배열 형식으로 반환하세요.
    [
      {
        "transaction_date":"",
        "merchant_name":"",
        "amount":0,
        "installment":""
      }
    ]
    
    누락된 거래가 있더라도 임의로 생성하지 마세요.
    금액은 숫자만 반환하세요.
    날짜는 YYYY-MM-DD 형식으로 반환하세요.
    JSON 외에는 아무 것도 출력하지 마세요.
    
    반드시 JSON 배열만 출력하세요.
    설명이나 ```json 같은 마크다운은 출력하지 마세요.
    """
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    make_file_content(file_path),
                ],
            }
        ],
    )

    result = response.output_text.strip()
    result = (
        result.replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        return json.loads(result)

    except json.JSONDecodeError:
        raise ValueError(status_code=400,
                detail="Vision 응답을 JSON으로 변환하지 못했습니다.")