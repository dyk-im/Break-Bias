from typing import List, Tuple, Optional
from rag.rag_system import RAGSystem
from app.models.schemas import ChatMessage
from app.services.youtube_analysis_service import YouTubeAnalysisService
import re


class ChatService:
    """채팅 서비스 클래스"""
    
    def __init__(self):
        self.rag_system = RAGSystem()
        self.youtube_service = YouTubeAnalysisService()
        self.conversation_history = {}  # 실제로는 데이터베이스나 캐시 사용
    
    def _extract_youtube_url(self, message: str) -> Optional[str]:
        """메시지에서 YouTube URL 추출"""
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(0)
        return None
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """YouTube URL에서 비디오 ID 추출"""
        patterns = [
            r'(?:v=|/)([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def process_message(
        self, 
        message: str, 
        conversation_id: str, 
        use_rag: bool = True
    ) -> Tuple[str, Optional[List[str]]]:
        """메시지 처리 및 응답 생성"""
        
        # 대화 히스토리 가져오기
        history = self.conversation_history.get(conversation_id, [])
        
        # 사용자 메시지를 히스토리에 추가
        user_message = ChatMessage(role="user", content=message)
        history.append(user_message)
        
        try:
            # YouTube 링크 감지
            youtube_url = self._extract_youtube_url(message)
            
            if youtube_url:
                # YouTube 영상 분석 수행
                response_text, sources = await self._handle_youtube_analysis(message, youtube_url)
            elif use_rag:
                # RAG 시스템을 사용한 응답 생성
                response_text, sources = await self.rag_system.generate_response(
                    query=message,
                    conversation_history=history
                )
            else:
                # RAG 없이 직접 LLM 응답 생성
                response_text = await self.rag_system.generate_direct_response(
                    query=message,
                    conversation_history=history
                )
                sources = None
            
            # 어시스턴트 응답을 히스토리에 추가
            assistant_message = ChatMessage(role="assistant", content=response_text)
            history.append(assistant_message)
            
            # 히스토리 저장 (최근 20개 메시지만 유지)
            self.conversation_history[conversation_id] = history[-20:]
            
            return response_text, sources
            
        except Exception as e:
            error_response = f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
            assistant_message = ChatMessage(role="assistant", content=error_response)
            history.append(assistant_message)
            self.conversation_history[conversation_id] = history[-20:]
            
            return error_response, None
    
    async def _handle_youtube_analysis(self, message: str, youtube_url: str) -> Tuple[str, Optional[List[str]]]:
        """YouTube 영상 분석 처리"""
        try:
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                return "죄송합니다. YouTube 링크에서 비디오 ID를 추출할 수 없습니다.", None
            
            # 분석 질문 추출 (기본값 설정)
            analysis_query = message.replace(youtube_url, "").strip()
            if not analysis_query or len(analysis_query) < 3:
                analysis_query = "이 영상에 대한 전반적인 여론"
            
            # 1. 비디오 ID를 주제로 댓글 수집
            collection_result = await self.youtube_service.collect_video_comments(
                video_id=video_id,
                max_comments=200  # 더 많은 댓글 수집
            )
            
            # 2. 수집된 댓글로 여론 분석
            analysis_text, analysis_data = await self.youtube_service.analyze_topic_opinion(
                query=analysis_query,
                topic=video_id,
                detailed=True
            )
            
            # 3. 결과 포맷팅
            result_text = f"""
🎥 **YouTube 영상 분석 결과**

📊 **수집 정보**
- 수집된 댓글: {collection_result.get('collected_comments', 0)}개
- 처리된 청크: {collection_result.get('processed_chunks', 0)}개

{analysis_text}

🔗 **분석 대상**: {youtube_url}
"""
            
            # 소스 정보
            sources = [f"YouTube Video: {video_id}"]
            
            return result_text, sources
            
        except Exception as e:
            return f"YouTube 영상 분석 중 오류가 발생했습니다: {str(e)}", None
    
    async def get_conversation_history(self, conversation_id: str) -> List[dict]:
        """대화 히스토리 조회"""
        history = self.conversation_history.get(conversation_id, [])
        return [{"role": msg.role, "content": msg.content} for msg in history]
    
    async def clear_conversation(self, conversation_id: str):
        """대화 히스토리 삭제"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id] 