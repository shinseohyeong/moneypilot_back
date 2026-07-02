# ============================================================
# 파일 위치: app/services/stock_rag_service.py
# 역할:
#   - 뉴스 요약/섹터 인사이트를 vector store에 인덱싱합니다.
#   - 사용자의 질문과 관련된 RAG 문서를 검색합니다.
# ============================================================

import os
import shutil
from pathlib import Path
from typing import List

from fastapi import HTTPException
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.stock_rag_repository import StockRagRepository
from app.schemas.stock_rag_schema import (
    StockRagBuildRequest,
    StockRagBuildResponse,
    StockRagSearchItem,
    StockRagSearchResponse,
)


class StockRagService:
    """
    주식/경제 RAG service입니다.
    """

    COLLECTION_NAME = "stock_economy_rag"
    PERSIST_DIR = Path("storage/vectorstores/stock_economy_rag")

    def __init__(self, db: Session):
        self.db = db
        self.repository = StockRagRepository(db)

    def build_index(
        self,
        request: StockRagBuildRequest,
    ) -> StockRagBuildResponse:
        """
        DB의 뉴스 요약/섹터 인사이트를 vector store에 저장합니다.
        """
        self._validate_openai_key()

        raw_documents = []
        raw_documents.extend(
            self.repository.list_news_summary_documents(
                limit=request.news_limit,
            )
        )
        raw_documents.extend(
            self.repository.list_sector_insight_documents(
                limit=request.sector_limit,
            )
        )

        if not raw_documents:
            raise HTTPException(
                status_code=404,
                detail="RAG에 인덱싱할 뉴스 요약 또는 섹터 인사이트 데이터가 없습니다.",
            )

        if request.rebuild and self.PERSIST_DIR.exists():
            shutil.rmtree(self.PERSIST_DIR)

        self.PERSIST_DIR.mkdir(parents=True, exist_ok=True)

        documents = [
            Document(
                page_content=item["content"],
                metadata=item["metadata"],
            )
            for item in raw_documents
        ]

        ids = [item["id"] for item in raw_documents]

        vector_store = self._get_vector_store()
        vector_store.add_documents(
            documents=documents,
            ids=ids,
        )

        return StockRagBuildResponse(
            collection_name=self.COLLECTION_NAME,
            indexed_count=len(documents),
            message="주식/경제 RAG 인덱싱이 완료되었습니다.",
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> StockRagSearchResponse:
        """
        사용자 질문과 관련된 RAG 문서를 검색합니다.
        """
        self._validate_openai_key()

        if not self.PERSIST_DIR.exists():
            raise HTTPException(
                status_code=404,
                detail="RAG index가 없습니다. 먼저 /stock/build API를 실행해주세요.",
            )

        vector_store = self._get_vector_store()

        results = vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
        )

        items: List[StockRagSearchItem] = []

        for document, score in results:
            metadata = document.metadata or {}

            items.append(
                StockRagSearchItem(
                    source_type=metadata.get("source_type", "unknown"),
                    source_id=metadata.get("source_id", ""),
                    title=metadata.get("title"),
                    content=document.page_content,
                    score=float(score) if score is not None else None,
                    metadata=metadata,
                )
            )

        return StockRagSearchResponse(
            query=query,
            top_k=top_k,
            total_count=len(items),
            results=items,
        )

    def _get_vector_store(self) -> Chroma:
        """
        Chroma vector store 인스턴스를 생성합니다.
        """
        embedding_model = os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small",
        )

        embeddings = OpenAIEmbeddings(
            model=embedding_model,
            api_key=settings.openai_api_key,
        )

        return Chroma(
            collection_name=self.COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(self.PERSIST_DIR),
        )

    def _validate_openai_key(self) -> None:
        """
        OpenAI embedding 호출에 필요한 API key를 확인합니다.
        """
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY가 설정되지 않았습니다. .env를 확인해주세요.",
            )