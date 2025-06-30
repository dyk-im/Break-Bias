import os
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.models.schemas import CommentData
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class YouTubeService:
    """유튜브 API를 사용한 댓글 수집 서비스"""
    
    def __init__(self):
        self.api_key = settings.youtube_api_key
        if not self.api_key:
            logger.warning("YouTube API 키가 설정되지 않았습니다.")
            self.youtube = None
        else:
            self.youtube = build(
                settings.youtube_api_service_name,
                settings.youtube_api_version,
                developerKey=self.api_key
            )
    
    async def search_videos(self, query: str, max_results: int = 10) -> List[Dict]:
        """특정 주제로 유튜브 영상 검색"""
        if not self.youtube:
            return self._get_dummy_videos(query)
        
        try:
            search_response = self.youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=max_results,
                order="relevance"
            ).execute()
            
            videos = []
            for item in search_response["items"]:
                video_data = {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "description": item["snippet"]["description"]
                }
                videos.append(video_data)
            
            return videos
            
        except HttpError as e:
            logger.error(f"YouTube API 오류: {e}")
            return self._get_dummy_videos(query)
    
    async def get_video_comments(self, video_id: str, max_results: int = 100) -> List[CommentData]:
        """특정 영상의 댓글 수집"""
        if not self.youtube:
            return self._get_dummy_comments(video_id)
        
        try:
            comments_response = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_results,
                order="relevance",
                textFormat="plainText"
            ).execute()
            
            comments = []
            for item in comments_response["items"]:
                comment_snippet = item["snippet"]["topLevelComment"]["snippet"]
                
                comment = CommentData(
                    comment_id=item["snippet"]["topLevelComment"]["id"],
                    text=comment_snippet["textDisplay"],
                    author=comment_snippet["authorDisplayName"],
                    like_count=comment_snippet["likeCount"],
                    video_id=video_id,
                    video_title="",  # 별도로 설정 필요
                    published_at=comment_snippet["publishedAt"]
                )
                comments.append(comment)
            
            return comments
            
        except HttpError as e:
            logger.error(f"댓글 수집 오류 (video_id: {video_id}): {e}")
            return self._get_dummy_comments(video_id)
    
    async def collect_comments_by_topic(
        self, 
        query: str, 
        max_videos: int = 10, 
        max_comments_per_video: int = 100
    ) -> List[CommentData]:
        """주제별 댓글 대량 수집"""
        
        # 1. 영상 검색
        videos = await self.search_videos(query, max_videos)
        logger.info(f"검색된 영상 수: {len(videos)}")
        
        # 2. 각 영상의 댓글 수집
        all_comments = []
        for video in videos:
            video_id = video["video_id"]
            video_title = video["title"]
            
            comments = await self.get_video_comments(video_id, max_comments_per_video)
            
            # 댓글에 영상 제목 추가
            for comment in comments:
                comment.video_title = video_title
            
            all_comments.extend(comments)
            logger.info(f"영상 '{video_title}': {len(comments)}개 댓글 수집")
        
        logger.info(f"총 수집된 댓글 수: {len(all_comments)}")
        return all_comments
    
    def _get_dummy_videos(self, query: str) -> List[Dict]:
        """API 키가 없을 때 사용하는 더미 영상 데이터"""
        return [
            {
                "video_id": f"dummy_video_{i}",
                "title": f"{query} 관련 영상 {i+1}",
                "channel_title": f"채널 {i+1}",
                "published_at": "2024-01-01T00:00:00Z",
                "description": f"{query}에 대한 설명입니다."
            }
            for i in range(3)
        ]
    
    def _get_dummy_comments(self, video_id: str) -> List[CommentData]:
        """API 키가 없을 때 사용하는 더미 댓글 데이터"""
        dummy_comments = [
            "정말 좋은 영상이네요! 👍",
            "이 주제에 대해 더 알고 싶어요",
            "반대 의견입니다. 다른 관점도 있어요",
            "완전 동감해요!",
            "이해하기 쉽게 설명해주셔서 감사합니다",
            "좀 더 자세한 설명이 필요할 것 같아요",
            "훌륭한 분석입니다",
            "이 부분은 틀린 것 같은데요?",
            "다음 영상도 기대됩니다",
            "구독하고 갑니다!"
        ]
        
        comments = []
        for i, text in enumerate(dummy_comments):
            comment = CommentData(
                comment_id=f"dummy_comment_{video_id}_{i}",
                text=text,
                author=f"사용자{i+1}",
                like_count=i * 2,
                video_id=video_id,
                video_title="더미 영상 제목",
                published_at="2024-01-01T00:00:00Z"
            )
            comments.append(comment)
        
        return comments 