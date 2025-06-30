from typing import List, Optional, Dict
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """채팅 메시지 모델"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str
    conversation_id: Optional[str] = None
    use_rag: bool = True


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    response: str
    conversation_id: str
    sources: Optional[List[str]] = None
    sentiment_analysis: Optional[Dict] = None  # 감정 분석 결과


# YouTube 관련 모델들
class YouTubeSearchRequest(BaseModel):
    """유튜브 검색 요청 모델"""
    query: str
    max_videos: Optional[int] = 10
    max_comments_per_video: Optional[int] = 100


class CommentData(BaseModel):
    """댓글 데이터 모델"""
    comment_id: str
    text: str
    author: str
    like_count: int
    video_id: str
    video_title: str
    published_at: str


class SentimentResult(BaseModel):
    """감정 분석 결과 모델"""
    positive: float
    negative: float
    neutral: float
    dominant: str  # "positive", "negative", "neutral"


class AnalysisResult(BaseModel):
    """분석 결과 모델"""
    summary: str
    sentiment_analysis: SentimentResult
    total_comments: int
    keywords: List[str]
    representative_comments: List[CommentData]


class YouTubeAnalysisResponse(BaseModel):
    """유튜브 분석 응답 모델"""
    query: str
    analysis: AnalysisResult
    video_count: int
    comment_count: int


# 기존 Document 관련 모델들 (댓글 데이터에도 활용)
class DocumentUpload(BaseModel):
    """문서 업로드 모델"""
    filename: str
    content_type: str


class DocumentInfo(BaseModel):
    """문서 정보 모델"""
    id: str
    filename: str
    upload_date: str
    size: int
    status: str  # "processing", "completed", "failed"


class DocumentResponse(BaseModel):
    """문서 응답 모델"""
    message: str
    document_id: Optional[str] = None
    status: str 