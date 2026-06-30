"""
RAG 문서의 저장, 검색, 삭제를 담당하는 공통 서비스 모듈
문서 형식:
{
    "id": "spending:analysis_report:1:summary",
    "content": "RAG에 저장할 자연어 문서 내용",
    "metadata": {
        "user_id": 1,
        "domain": "spending",
        "feature": "analysis_report",
        ...
    }
}
"""
from app.rag.vector_store import rag_collection

class RagService:
  """
  Chroma collection에 대해 공통 RAG 작업을 수행하는 서비스 클래스
  주요 기능:
  - RAG 문서 저장 또는 업데이트
  - RAG 문서 검색
  - RAG 문서 삭제
  """
  
  def upsert_documents(
    self, 
    documents: list[dict],
  ) -> None:
    """
    RAG 문서 목록을 Chroma에 저장하거나 업데이트
    같은 id가 이미 존재하면 기존 문서를 덮어쓰기
    """
    if not documents:
      return
    
    ids = [doc["id"] for doc in documents]
    contents = [doc["content"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]
    
    rag_collection.upsert(
      ids=ids,
      documents=contents, 
      metadatas=metadatas,
    )
  
  
  def search(
    self,
    query: str, 
    where: dict | None = None,
    n_results: int = 4,
  ) -> list[dict]:
    """ 
    사용자 질문과 관련된 RAG 문서를 Chroma에서 검색
    where 조건을 사용하면 특정 사용자, 특정 도메인, 특정 월 데이터만
    필터링해서 검색 가능
    Args:
      query: 사용자의 질문 또는 검색 문장.
      where: Chroma metadata filter 조건.
        예:
        {
          "$and": [
            {"user_id": 1},
            {"domain": "spending"},
            {"month": "2026-05"}
          ]
        }
      n_results: 검색할 문서 개수.

    Returns:
      검색된 문서 목록.
      각 결과는 content와 metadata를 포함합니다.
    """
    results = rag_collection.query(
      query_texts=[query],
      n_results=n_results,
      where=where,
    )
    
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    
    searched_docs = []
    
    for content, metadata in zip(documents, metadatas):
      searched_docs.append({
        "content": content,
        "metadata": metadata,
      })
    
    return searched_docs
  
  
  def delete_by_ids(
    self, 
    ids: list[str],
  ) -> None:
    """
    vector_id 목록을 기준으로 Chroma 문서를 삭제
    """
    if not ids:
      return
    
    rag_collection.delete(
      ids=ids,
    )
  
  
  def delete_by_filter(
    self, 
    where: dict,
  ) -> None:
    """metadata filter 조건에 해당하는 Chroma 문서 삭제"""
    rag_collection.delete(
      where=where,
    )