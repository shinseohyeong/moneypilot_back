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
    ):
        transactions = vision_parser(file_path)
        # 후처리
        for tx in transactions:

            # 날짜 문자열 → date 객체
            tx["transaction_date"] = datetime.strptime(
                tx["transaction_date"],
                "%Y-%m-%d"
            ).date()

            # month 생성
            tx["month"] = tx["transaction_date"].strftime("%Y-%m")

            # 금액 int 보장
            tx["amount"] = int(str(tx["amount"]).replace(",", ""))

        return transactions