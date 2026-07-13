import requests
from app.core.config import settings

DEPOSIT_API_URL = "http://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json"
SAVING_API_URL = "http://finlife.fss.or.kr/finlifeapi/savingProductsSearch.json"
INSURANCE_API_URL = "http://apis.data.go.kr/1160100/service/GetMedicalReimbursementInsuranceInfoService.json"

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
    }

    response = requests.get(
        SAVING_API_URL,
        params=params,
    )

    response.raise_for_status()

    data = response.json()

    return data

def fetch_insurance_products():
    url = settings.INSURANCE_API_URL
    
    params = {
        "serviceKey": settings.PUBLIC_DATA_API_KEY,
        "pageNo": 1,
        "numOfRows": 1000,
    }

    response = requests.get(
        url,
        params=params,
    )

    response.raise_for_status()

    return response.json()