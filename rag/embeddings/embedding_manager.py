from typing import List, Dict, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Gemini 임베딩을 사용한 임베딩 관리 클래스"""
    
    def __init__(self):
        self.model = self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Gemini 실험적 임베딩 모델 초기화"""
        if not settings.gemini_api_key:
            raise ValueError("Gemini API 키가 설정되지 않았습니다.")
            
        try:
            return GoogleGenerativeAIEmbeddings(
                google_api_key=settings.gemini_api_key,
                model="models/gemini-embedding-exp-03-07",  # 더 안정적인 모델
                task_type="retrieval_document",  # 문서 검색용
                title="YouTube 댓글 임베딩"
            )
        except Exception as e:
            logger.error(f"Gemini 임베딩 초기화 실패: {e}")
            raise
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트의 임베딩 생성"""
        if not self.model:
            raise ValueError("임베딩 모델이 초기화되지 않았습니다.")
        
        try:
            embeddings = await self.model.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        """단일 텍스트의 임베딩 생성"""
        try:
            embedding = await self.model.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"단일 임베딩 생성 실패: {e}")
            raise 