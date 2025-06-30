import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # AI Model Configuration
    gemini_api_key: Optional[str] = None
    
    # YouTube API Settings
    youtube_api_key: Optional[str] = None
    max_videos_per_search: int = 10
    max_comments_per_video: int = 100
    youtube_api_service_name: str = "youtube"
    youtube_api_version: str = "v3"
    
    # Model Settings
    embedding_model: str = "models/gemini-embedding-exp-03-07"
    llm_model_name: str = "gemini-2.0-flash-lite"
    temperature: float = 0.7
    max_tokens: int = 1000
    
    # Vector Store Configuration
    vector_store_type: str = "chromadb"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Sentiment Analysis Settings
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    sentiment_threshold: float = 0.1
    
    # Analysis Settings
    top_k_comments: int = 20
    summary_max_length: int = 500
    
    # FastAPI Configuration
    api_host: str = "localhost"
    api_port: int = 8000
    debug: bool = True
    
    # Streamlit Configuration
    streamlit_port: int = 8501
    
    # Data Paths
    documents_path: str = "./data/documents"  # 댓글 저장 경로
    vectorstore_path: str = "./data/vectorstore"
    cache_path: str = "./data/cache"
    results_path: str = "./data/results"
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # 추가 필드 무시
    }


# 전역 설정 인스턴스
settings = Settings() 