import requests
from app.core.config import settings

DEPOSIT_API_URL = "http://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json"
SAVING_API_URL = "http://finlife.fss.or.kr/finlifeapi/savingProductsSearch.json"

def fetch_deposit_products():
    params = {
        "auth": settings.FINANCE_API_KEY,
        "topFinGrpNo": "020000",
        "pageNo": "1",
    }

    # API 호출
    response = requests.get(
    DEPOSIT_API_URL,
    params=params,
    )
    
    # 에러 확인
    response.raise_for_status()

    # JSON으로 반환
    data = response.json()

    print(data)

    return data

def fetch_saving_products():
    params = {
        "auth": settings.FINANCE_API_KEY,
        "topFinGrpNo": "020000",
        "pageNo": 1,
        "financeCd": "0010587",
    }

    response = requests.get(
        SAVING_API_URL,
        params=params,
    )

    response.raise_for_status()

    return response.json()
