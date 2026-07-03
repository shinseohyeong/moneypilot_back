import pandas as pd

def parse_kb(df):
    transactions=[]

    # 상단 카드 정보 제거
    # 실제 거래 헤더 아래부터 사용
    header_index = None
    for index,row in df.iterrows():
        if row.astype(str).str.contains("이용일").any():
            header_index=index
            break

    # 거래 시작 위치로 자르기
    df = df.iloc[header_index+1:]

    # 컬럼명 재설정
    df.columns = [
        "이용일",
        "이용시간",
        "이용고객명",
        "이용카드명",
        "이용하신곳",
        "국내이용금액",
        "해외이용금액",
        "결제방법",
        "가맹점정보",
        "할인금액",
        "포인트",
        "상태",
        "결제예정일",
        "승인번호"
    ]

    for _,row in df.iterrows():

        # 빈 행 제거
        if pd.isna(row["이용일"]):
            continue
          
        date = pd.to_datetime(
            row["이용일"]
        )

        transaction = {
            "transaction_date":
                date.date(),
                
            "month":
                date.strftime(
                    "%Y-%m"
                ),

            "merchant_name":
                str(
                    row["이용하신곳"]
                ),

            "description":
                str(
                    row["결제방법"]
                ),
                
            "amount":
                int(
                    str(
                        row["국내이용금액"]
                    )
                    .replace(",","")
                ),

            "category":
                None,

            "expense_type":
                "VARIABLE"
        }

        transactions.append(
            transaction
        )
    return transactions