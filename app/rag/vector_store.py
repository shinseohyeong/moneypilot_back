""" 
Chroma Vector Store 연결을 담당하는 모듈

Chroma PersistentClient 생성,
OpenAI Embedding Function 연결한 뒤,
프로젝트 전체에서 사용할 RAG collection 생성

다른 파일에서 Chroma 직접 생성하지 않고,
이 파일의 rag_collection을 import 해서 사용하기 !
"""
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from app.core.config import settings
from app.rag.rag_constants import RAG_COLLECTION_NAME, CHROMA_DB_PATH


chroma_client = chromadb.PersistentClient(
  path=CHROMA_DB_PATH,
)

embedding_function = OpenAIEmbeddingFunction(
  api_key=settings.OPENAI_API_KEY,
  model_name="text-embedding-3-small",
)

rag_collection = chroma_client.get_or_create_collection(
  name=RAG_COLLECTION_NAME,
  embedding_function=embedding_function,
)