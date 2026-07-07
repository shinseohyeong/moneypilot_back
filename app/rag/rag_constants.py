"""
RAG에서 공통으로 사용하는 상수들을 정의하는 모듈
이 파일의 목적은 팀원마다 domain, feature, collection 이름을 다르게 쓰는 것을 방지하기 위함
ex:
metadata = {
  "domain": "spending",
  "feature": "analysis_report",
  "source_table": "analysis_reports",
  "source_id": 1,
  "month": "2026-05",
  "document_type": "category",
}
"""

RAG_COLLECTION_NAME = "finance_agent_rag"
CHROMA_DB_PATH = './chroma_db'


class RagDomain:
  """ 
  RAG 문서가 어떤 업무 도메인에 속하는지 구분하는 상수 
  ex:
  - spending: 소비 분석 
  - stock: 주식/뉴스/시세
  - financial_product: 예금/적금/금융상품
  -> 임시로 명시해 둔거라서 spending 이외는 수정해도 됩니다!
  """
  
  SPENDING = "spending"
  STOCK = "stock"
  FINANCIAL_PRODUCT = "financial_product"


class RagFeature:
  """
  RAG 문서가 어떤 기능에서 생성되었는지 구분하는 상수
  같은 domain 안에서도 여러 기능이 생길 수 있기 때문에 feature 따로 둡니다
  ex:
  - spending + analysis_report
  - stock + stock_news
  - financial_product + deposit_savings
  """
  ANALYSIS_REPORT = "analysis_report"
  STOCK_NEWS = "stock_news"
  FINANCIAL_PRODUCT = "financial_product"


class RagSourceTable:
  """
  RAG 문서의 원본 데이터가 저장된 DB 테이블명을 관리하는 상수 
  Chroma에는 벡터만 저장되기 때문에, 원본 DB 데이터를 추적하려면
  source_table과 source_id를 metadata에 넣어두는 게 좋음
  """
  ANALYSIS_REPORTS = "analysis_reports"
  