# ==========================================
# 파일 위치 : app/services/vision_service.py
# 역할 :
# Vision Parser 호출
# Vision 결과 후처리
# ==========================================
from datetime import datetime

from parsers.vision_parser import vision_parser

class VisionService:
    # ======================================
    # 카드명세서 Vision 분석
    # ======================================
    def extract_transactions(
        self,
        file_path: str,
        db,
        user_id: int,
    ):
        result = vision_parser(
            file_path=file_path,
            db=db,
            user_id=user_id,
        )

        transactions = result["transactions"]
        response = result["response"]

        # 후처리
        for tx in transactions:

            tx["transaction_date"] = datetime.strptime(
                tx["transaction_date"],
                "%Y-%m-%d"
            ).date()

            tx["month"] = tx["transaction_date"].strftime("%Y-%m")
            tx["amount"] = int(str(tx["amount"]).replace(",", ""))

        return {
            "transactions": transactions,
            "response": response,
        }