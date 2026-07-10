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
이 파일은 카드 거래명세서입니다.

모든 거래내역을 아래 JSON 배열 형식으로 반환하세요.

[
  {
    "transaction_date": "2026-01-10",
    "merchant_name": "",
    "amount": 0,
    "description": "일시불"
  }
]

규칙

- 누락된 거래를 임의로 생성하지 마세요.
- amount는 반드시 숫자(integer)만 반환하세요.
- transaction_date는 반드시 YYYY-MM-DD 형식 문자열로 반환하세요.
- description은 반드시 문자열입니다.
- JSON 배열만 출력하세요.
- ```json 같은 마크다운은 출력하지 마세요.
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