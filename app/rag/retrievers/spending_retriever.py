"""
소비 분석 RAG 문서를 검색하는 retriever 모듈
이 파일은 Chroma에 저장된 여러 RAG 문서 중에서 
소비 분석 리포트 문서만 검색하기 위한 조건 구성

소비 분석 리포트만 검색하려면
domain=spending, feature=analysis_report 조건이 필요
SpendingReportRetriever가 검색 로직을 감싸줌

추후에 langGraph tools에서 rag 검색 + LLM 답변 생성에 활용할 예정 !
"""
from app.rag.rag_constants import RagDomain, RagFeature
from app.rag.rag_service import RagService


class SpendingReportRetriever:
  """ 소비 분석 리포트 RAG 문서 검색 전용 Retriever """
  def __init__(self):
    self.rag_service = RagService()
  
  def search_reports(
    self, 
    user_id: int,
    query: str,
    month: str | None = None,
    n_results: int = 4,
  ) -> list[dict]:
    """
    소비 분석 리포트 RAG 문서를 검색
    """
    where_filter = self._build_report_filter(
      user_id=user_id,
      month=month,
    )
    
    return self.rag_service.search(
      query=query,
      where=where_filter,
      n_results=n_results,
    )
    
  
  def search_reports_by_document_type(
    self,
    user_id: int,
    query: str, 
    document_type: str, 
    month: str | None = None,
    n_results: int = 4,
  ) -> list[dict]:
    """ 
    특정 document_type의 소비 분석 리포트 문서만 검색
    """
    filters = [
      {"user_id": user_id},
      {"domain": RagDomain.SPENDING},
      {"feature": RagFeature.ANALYSIS_REPORT},
      {"document_type": document_type},
    ]
    
    if month:
      filters.append({"month": month})
      
    where_filter = {
      "$and": filters,
    }
    
    return self.rag_service.search(
      query=query,
      where=where_filter,
      n_results=n_results,
    )
    
  
  def _build_report_filter(
    self,
    user_id: int,
    month: str | None = None,
  ) -> dict: 
    """
    소비 분석 리포트 검색용 Chroma metadata filter 생성
    """
    filters = [
      {"user_id": user_id},
      {"domain": RagDomain.SPENDING},
      {"feature": RagFeature.ANALYSIS_REPORT},
    ]
    
    if month:
      filter.append({"month": month})
      
    return {
      "$and": filters,
    }