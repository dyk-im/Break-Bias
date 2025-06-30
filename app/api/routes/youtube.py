from fastapi import APIRouter, HTTPException
from typing import Optional
from app.models.schemas import YouTubeSearchRequest, YouTubeAnalysisResponse
from app.services.youtube_analysis_service import YouTubeAnalysisService

router = APIRouter()
youtube_service = YouTubeAnalysisService()


@router.post("/youtube/collect")
async def collect_comments(request: YouTubeSearchRequest):
    """특정 주제의 유튜브 댓글 수집"""
    try:
        result = await youtube_service.collect_topic_comments(
            topic=request.query,
            max_videos=request.max_videos or 10,
            max_comments_per_video=request.max_comments_per_video or 100
        )
        
        return {
            "message": f"'{request.query}' 주제의 댓글 수집 완료",
            "collected_comments": result["collected_comments"],
            "processed_chunks": result["processed_chunks"],
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"댓글 수집 중 오류 발생: {str(e)}")


@router.post("/youtube/analyze")
async def analyze_opinion(
    query: str,
    topic: Optional[str] = None,
    detailed: bool = True
):
    """수집된 댓글을 바탕으로 여론 분석"""
    try:
        analysis_text, analysis_data = await youtube_service.analyze_topic_opinion(
            query=query,
            topic=topic,
            detailed=detailed
        )
        
        return {
            "query": query,
            "topic": topic,
            "analysis": analysis_text,
            "sentiment_stats": analysis_data["sentiment_stats"],
            "representative_comments": analysis_data["representative_comments"],
            "keywords": analysis_data["keywords"],
            "total_relevant_comments": analysis_data["total_relevant_comments"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"여론 분석 중 오류 발생: {str(e)}")


@router.get("/youtube/topics/{topic}/overview")
async def get_topic_overview(topic: str):
    """특정 주제의 전체 개요"""
    try:
        overview = await youtube_service.get_topic_overview(topic)
        return overview
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주제 개요 조회 중 오류 발생: {str(e)}")


@router.get("/youtube/topics")
async def list_collected_topics():
    """수집된 주제 목록 조회"""
    try:
        topics = await youtube_service.get_collected_topics()
        return {"topics": topics}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주제 목록 조회 중 오류 발생: {str(e)}")


@router.delete("/youtube/topics/{topic}")
async def clear_topic_data(topic: str):
    """특정 주제의 모든 데이터 삭제"""
    try:
        await youtube_service.clear_topic_data(topic)
        return {"message": f"'{topic}' 주제의 데이터가 삭제되었습니다."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 삭제 중 오류 발생: {str(e)}")


@router.get("/youtube/stats")
async def get_system_stats():
    """시스템 전체 통계"""
    try:
        stats = await youtube_service.get_system_stats()
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류 발생: {str(e)}") 