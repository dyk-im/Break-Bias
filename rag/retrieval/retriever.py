import os
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from rag.embeddings.embedding_manager import EmbeddingManager
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class Retriever:
    """ChromaDB를 사용한 벡터 검색 클래스"""
    
    def __init__(self, embedding_manager: EmbeddingManager):
        self.embedding_manager = embedding_manager
        self.client = self._initialize_chromadb()
        self.collection = self._get_or_create_collection()
    
    def _initialize_chromadb(self):
        """ChromaDB 클라이언트 초기화"""
        try:
            # 벡터 저장소 경로 생성
            os.makedirs(settings.vectorstore_path, exist_ok=True)
            
            # ChromaDB 설정
            chroma_settings = Settings(
                persist_directory=settings.vectorstore_path,
                anonymized_telemetry=False
            )
            
            return chromadb.Client(settings=chroma_settings)
            
        except Exception as e:
            logger.error(f"ChromaDB 초기화 실패: {e}")
            raise
    
    def _get_or_create_collection(self):
        """컬렉션 가져오기 또는 생성"""
        try:
            return self.client.get_or_create_collection(
                name="youtube_comments",
                metadata={"description": "YouTube 댓글 벡터 저장소"}
            )
        except Exception as e:
            logger.error(f"컬렉션 생성 실패: {e}")
            raise
    
    async def add_document(self, content: str, metadata: Dict):
        """문서 추가"""
        try:
            # 임베딩 생성
            embedding = await self.embedding_manager.get_embeddings([content])
            
            # 문서 ID 생성 (메타데이터의 comment_id 사용)
            doc_id = metadata.get("comment_id", str(hash(content)))
            
            # ChromaDB에 추가
            self.collection.add(
                embeddings=embedding,
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
        except Exception as e:
            logger.error(f"문서 추가 실패: {e}")
            raise
    
    async def retrieve(self, query: str, top_k: int = 20) -> List[Dict]:
        """쿼리와 관련된 문서 검색"""
        try:
            # 쿼리 임베딩 생성
            query_embedding = await self.embedding_manager.get_embeddings([query])
            
            # 유사도 검색
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # 결과 포맷팅
            documents = []
            for i in range(len(results["documents"][0])):
                doc = {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - min(results["distances"][0][i], 1)  # 거리를 유사도 점수로 변환
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            return []
    
    async def delete_document(self, document_id: str):
        """문서 삭제"""
        try:
            self.collection.delete(ids=[document_id])
        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            raise
    
    def get_collection_stats(self) -> Dict:
        """컬렉션 통계"""
        try:
            return {
                "total_documents": self.collection.count(),
                "name": self.collection.name,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {} 