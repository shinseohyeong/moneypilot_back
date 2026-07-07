# ==========================================
# 파일 위치 : app/services/vision_service.py
# 역할 :
# Vision Parser 호출
# Vision 결과 후처리
# ==========================================
from parsers.vision_parser import parse_card_statement

class VisionService:
    # ======================================
    # 카드명세서 Vision 분석
    # ======================================
    def extract_transactions(
        self,
        file_path: str
    ):
        transactions = parse_card_statement(file_path)
        # 나중에 후처리 필요하면 여기서
        # 날짜 형식 변환
        # amount int 변환
        # category 추론

        return transactions