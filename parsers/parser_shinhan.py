# ==========================================
# 파일 위치 :
# app/parsers/shinhan_parser.py
# 역할 :
# 신한카드 거래명세서 엑셀 파싱
# 반환 :
# transactions 테이블 저장 형태
# ==========================================
import pandas as pd

def parse_shinhan(df):
    transactions = []

    # 컬럼명 공백 제거
    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    for _, row in df.iterrows():
        # 거래일 없는 행 제거
        if pd.isna(row["거래일"]):
            continue

        # 날짜 변환
        transaction_date = pd.to_datetime(
            row["거래일"]
        )

        # 금액 처리
        amount = str(
            row["금액"]
        ).replace(
            ",",
            ""
        )

        # 숫자 아닌 행 제거
        if not amount.replace(
            "-",
            ""
        ).isdigit():
            continue

        transaction = {
            # 거래일
            "transaction_date":
                transaction_date.date(),

            # 거래월
            "month":
                transaction_date.strftime(
                    "%Y-%m"
                ),

            # 가맹점
            "merchant_name":
                str(
                    row["가맹점명"]
                ),

            # 설명
            "description":
                str(
                    row["업종"]
                )
                if not pd.isna(
                    row["업종"]
                )
                else None,
                
            # 금액
            "amount":
                int(amount),

            # 카테고리
            "category":
                None,

            # 기본값
            "expense_type":
                "VARIABLE"
        }

        transactions.append(
            transaction
        )
    return transactions