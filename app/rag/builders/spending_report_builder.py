"""
AI 소비분석 리포트 데이터를 RAG 문서로 변환하는 builder 모듈

변환 대상 컬럼:
- summary_text
- category_text
- overspending_text
- card_text
- compare_text
- recommendation_text
"""
from app.models.spending_analysis_model import AnalysisReport
from app.rag.rag_constants import RagDomain, RagFeature, RagSourceTable

def build_spending_report_documents(
  report: AnalysisReport,
) -> list[dict]:
  """
  AnalysisReport 객체를 Chroma에 저장할 RAG 문서 목록으로 변환
  document_type:
  - summary
  - category
  - overspending
  - card
  - compare
  - recommendation
  """
  sections = [
    {
      "document_type": "summary",
      "title_suffix": "월별 소비 요약",
      "content": report.summary_text,
    },
    {
      "document_type": "category",
      "title_suffix": "카테고리별 소비 분석",
      "content": report.category_text,
    },
    {
      "document_type": "overspending",
      "title_suffix": "과소비 분석",
      "content": report.overspending_text,
    },
    {
      "document_type": "card",
      "title_suffix": "카드별 사용 분석",
      "content": report.card_text,
    },
    {
      "document_type": "compare",
      "title_suffix": "전월 대비 소비 비교",
      "content": report.compare_text,
    },
    {
      "document_type": "recommendation",
      "title_suffix": "소비 개선 추천",
      "content": report.recommendation_text,
    },
  ]
  
  documents = []
  
  for section in sections:
    content = section["content"]
    
    if not content:
      continue
    
    document_type = section["document_type"]
    title = f"{report.month} AI 소비분석 리포트 - {section['title_suffix']}"
    
    rag_content = f"""
    [{title}]
    
    {content}
    """.strip()
    
    vector_id = build_spending_report_vector_id(
      report_id=report.id,
      document_type=document_type,
    )
    
    documents.append({
      "id": vector_id,
        "content": rag_content,
        "metadata": {
          "user_id": int(report.user_id),
          "domain": RagDomain.SPENDING,
          "feature": RagFeature.ANALYSIS_REPORT,
          "source_table": RagSourceTable.ANALYSIS_REPORTS,
          "source_id": int(report.id),
          "summary_id": int(report.summary_id),
          "month": report.month,
          "document_type": document_type,
          "title": title,
        },
    })
    
    return documents


def build_spending_report_vector_id(
  report_id: int,
  document_type: str,
) -> str:
  """
  소비분석 리포트 RAG 문서의 고유 vector_id를 생성
  vector_id는 Chroma에서 문서를 식별하는 id
  """
  return (
    f"{RagDomain.SPENDING}:"
    f"{RagFeature.ANALYSIS_REPORT}:"
    f"{report_id}:"
    f"{document_type}"
  )
  