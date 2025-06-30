from typing import List, Dict, Optional, Tuple
from rag.rag_system import OpinionAnalysisRAGSystem


class YouTubeAnalysisService:
    """YouTube 댓글 분석 서비스 클래스"""
    
    def __init__(self):
        self.rag_system = OpinionAnalysisRAGSystem()
        self.collected_topics = set()  # 실제로는 데이터베이스나 캐시 사용
    
    async def collect_topic_comments(
        self, 
        topic: str, 
        max_videos: int = 10, 
        max_comments_per_video: int = 100
    ) -> Dict:
        """특정 주제의 댓글 수집"""
        
        result = await self.rag_system.collect_and_analyze_topic(
            topic=topic,
            max_videos=max_videos,
            max_comments_per_video=max_comments_per_video
        )
        
        # 수집된 주제 추가
        self.collected_topics.add(topic)
        
        return result
    
    async def collect_video_comments(self, video_id: str, max_comments: int = 200) -> Dict:
        """특정 비디오 ID의 댓글 수집"""
        
        # CommentProcessor에 직접 접근하여 비디오 댓글 수집
        comment_count, processed_count = await self.rag_system.comment_processor.collect_and_process_video_comments(
            video_id=video_id,
            max_comments=max_comments
        )
        
        # 수집된 주제 추가 (비디오 ID를 주제로 사용)
        self.collected_topics.add(video_id)
        
        return {
            "video_id": video_id,
            "collected_comments": comment_count,
            "processed_chunks": processed_count,
            "status": "completed"
        }
    
    async def analyze_topic_opinion(
        self, 
        query: str, 
        topic: Optional[str] = None, 
        detailed: bool = True
    ) -> Tuple[str, Dict]:
        """수집된 댓글을 바탕으로 여론 분석"""
        
        analysis_text, analysis_data = await self.rag_system.analyze_opinion(
            query=query,
            topic=topic,
            detailed=detailed
        )
        
        return analysis_text, analysis_data
    
    async def get_topic_overview(self, topic: str) -> Dict:
        """특정 주제의 전체 개요"""
        return await self.rag_system.get_topic_overview(topic)
    
    async def get_collected_topics(self) -> List[str]:
        """수집된 주제 목록 조회"""
        return list(self.collected_topics)
    
    async def clear_topic_data(self, topic: str):
        """특정 주제의 모든 데이터 삭제"""
        await self.rag_system.clear_topic_data(topic)
        if topic in self.collected_topics:
            self.collected_topics.remove(topic)
    
    async def get_system_stats(self) -> Dict:
        """시스템 전체 통계"""
        stats = await self.rag_system.get_system_stats()
        stats["collected_topics_count"] = len(self.collected_topics)
        stats["collected_topics"] = list(self.collected_topics)
        return stats
    
    async def quick_analysis(self, topic_and_query: str) -> Tuple[str, Dict]:
        """주제 수집 + 분석을 한번에 수행 (데모용)"""
        
        # 1. 댓글 수집
        collect_result = await self.collect_topic_comments(
            topic=topic_and_query,
            max_videos=5,  # 빠른 분석을 위해 적게
            max_comments_per_video=50
        )
        
        # 2. 바로 분석
        analysis_text, analysis_data = await self.analyze_topic_opinion(
            query=topic_and_query,
            topic=topic_and_query,
            detailed=True
        )
        
        # 3. 결과 통합
        analysis_data["collection_info"] = collect_result
        
        return analysis_text, analysis_data 