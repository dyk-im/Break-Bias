import os
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from config.settings import settings
from rag.youtube_service import YouTubeService
from rag.sentiment_analyzer import SentimentAnalyzer
from app.models.schemas import CommentData


class DocumentProcessor:
    """문서 처리 및 청킹 클래스"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        self.retriever = None  # 순환 참조 방지를 위해 지연 초기화
    
    def _get_retriever(self):
        """Retriever 지연 초기화"""
        if self.retriever is None:
            # 직접 임포트하는 대신 인스턴스를 생성
            from rag.embeddings.embedding_manager import EmbeddingManager
            from rag.retrieval.retriever import Retriever
            
            embedding_manager = EmbeddingManager()
            self.retriever = Retriever(embedding_manager)
        return self.retriever
    
    async def process_document(self, file_path: str, document_id: str):
        """문서 처리 및 벡터 저장소에 추가"""
        
        # 1. 문서 로딩
        documents = self._load_document(file_path)
        
        # 2. 텍스트 청킹
        chunks = self._split_documents(documents)
        
        # 3. 메타데이터 추가
        processed_chunks = self._add_metadata(chunks, document_id, file_path)
        
        # 4. 벡터 저장소에 추가
        retriever = self._get_retriever()
        for chunk in processed_chunks:
            await retriever.add_document(
                content=chunk["content"],
                metadata=chunk["metadata"]
            )
    
    def _load_document(self, file_path: str) -> List[str]:
        """파일 형식에 따른 문서 로딩"""
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                return [doc.page_content for doc in documents]
            
            elif file_extension == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
                documents = loader.load()
                return [doc.page_content for doc in documents]
            
            elif file_extension in ['.docx', '.doc']:
                loader = Docx2txtLoader(file_path)
                documents = loader.load()
                return [doc.page_content for doc in documents]
            
            else:
                raise ValueError(f"지원되지 않는 파일 형식: {file_extension}")
                
        except Exception as e:
            raise Exception(f"문서 로딩 중 오류 발생: {str(e)}")
    
    def _split_documents(self, documents: List[str]) -> List[str]:
        """문서를 청크로 분할"""
        all_chunks = []
        
        for doc_content in documents:
            chunks = self.text_splitter.split_text(doc_content)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _add_metadata(self, chunks: List[str], document_id: str, file_path: str) -> List[Dict]:
        """청크에 메타데이터 추가"""
        filename = os.path.basename(file_path)
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            metadata = {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
                "source": filename,
                "file_path": file_path
            }
            
            processed_chunks.append({
                "content": chunk,
                "metadata": metadata
            })
        
        return processed_chunks
    
    async def delete_document(self, document_id: str):
        """문서 ID로 벡터 저장소에서 문서 삭제"""
        retriever = self._get_retriever()
        await retriever.delete_document(document_id)


class CommentProcessor:
    """댓글 처리 및 청킹 클래스"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " "]
        )
        self.youtube_service = YouTubeService()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.retriever = None  # 지연 초기화
    
    def _get_retriever(self):
        """RAG 시스템 지연 초기화"""
        if self.retriever is None:
            from rag.embeddings.embedding_manager import EmbeddingManager
            from rag.retrieval.retriever import Retriever
            
            embedding_manager = EmbeddingManager()
            self.retriever = Retriever(embedding_manager)
        return self.retriever
    
    async def collect_and_process_comments(self, topic: str, max_videos: int = 10, max_comments_per_video: int = 100):
        """주제별 댓글 수집 및 벡터 저장소에 추가"""
        
        # 1. 댓글 수집
        comments = await self.youtube_service.collect_comments_by_topic(
            query=topic,
            max_videos=max_videos,
            max_comments_per_video=max_comments_per_video
        )
        
        # 2. 댓글 정제 및 청킹
        processed_comments = await self._process_comments(comments, topic)
        
        # 3. 벡터 저장소에 추가
        retriever = self._get_retriever()
        for processed_comment in processed_comments:
            await retriever.add_document(
                content=processed_comment["content"],
                metadata=processed_comment["metadata"]
            )
        
        return len(comments), len(processed_comments)
    
    async def collect_and_process_video_comments(self, video_id: str, max_comments: int = 200):
        """특정 비디오 ID의 댓글 수집 및 벡터 저장소에 추가"""
        
        # 1. 특정 비디오의 댓글 수집
        comments = await self.youtube_service.get_video_comments(
            video_id=video_id,
            max_results=max_comments
        )
        
        # 비디오 제목을 위해 비디오 정보 가져오기 (간단한 더미 처리)
        for comment in comments:
            if not comment.video_title:
                comment.video_title = f"Video {video_id}"
        
        # 2. 댓글 정제 및 청킹 (video_id를 topic으로 사용)
        processed_comments = self._process_comments(comments, video_id)
        
        # 3. 벡터 저장소에 추가
        retriever = self._get_retriever()
        for processed_comment in processed_comments:
            await retriever.add_document(
                content=processed_comment["content"],
                metadata=processed_comment["metadata"]
            )
        
        return len(comments), len(processed_comments)
    
    def _process_comments(self, comments: List[CommentData], topic: str) -> List[Dict]:
        """댓글 정제 및 메타데이터 추가"""
        
        processed_comments = []
        
        for i, comment in enumerate(comments):
            # 댓글 텍스트 정제
            cleaned_text = self._clean_comment_text(comment.text)
            
            # 너무 짧은 댓글은 제외
            if len(cleaned_text.strip()) < 10:
                continue
            
            # 감정 분석
            sentiment = self.sentiment_analyzer.analyze_single_comment(cleaned_text)
            
            # 메타데이터 구성
            metadata = {
                "comment_id": comment.comment_id,
                "author": comment.author,
                "like_count": comment.like_count,
                "video_id": comment.video_id,
                "video_title": comment.video_title,
                "published_at": comment.published_at,
                "topic": topic,
                "sentiment_positive": sentiment["positive"],
                "sentiment_negative": sentiment["negative"],
                "sentiment_neutral": sentiment["neutral"],
                "source": f"{comment.video_title} (댓글)",
                "type": "youtube_comment"
            }
            
            # 긴 댓글은 청킹
            if len(cleaned_text) > settings.chunk_size:
                chunks = self.text_splitter.split_text(cleaned_text)
                for j, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata["chunk_index"] = j
                    chunk_metadata["is_chunked"] = True
                    
                    processed_comments.append({
                        "content": chunk,
                        "metadata": chunk_metadata
                    })
            else:
                metadata["chunk_index"] = 0
                metadata["is_chunked"] = False
                
                processed_comments.append({
                    "content": cleaned_text,
                    "metadata": metadata
                })
        
        return processed_comments
    
    def _clean_comment_text(self, text: str) -> str:
        """댓글 텍스트 정제"""
        import re
        
        # 기본 정제
        cleaned = text.strip()
        
        # 연속된 공백 제거
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 연속된 같은 문자 제거 (ㅋㅋㅋㅋ -> ㅋㅋ)
        cleaned = re.sub(r'([ㅋㅎ])\1{2,}', r'\1\1', cleaned)
        cleaned = re.sub(r'([!?.])\1{2,}', r'\1\1', cleaned)
        
        # 특수문자만 있는 경우 제거
        if re.match(r'^[^가-힣a-zA-Z0-9]*$', cleaned):
            return ""
        
        return cleaned
    
    async def delete_comments_by_topic(self, topic: str):
        """주제별 댓글 삭제"""
        retriever = self._get_retriever()
        
        # 해당 주제의 모든 댓글 삭제 (실제 구현은 retriever에서)
        try:
            # ChromaDB에서 메타데이터 필터링으로 삭제
            # 이 부분은 retriever에서 where 조건 지원 시 구현
            pass
        except Exception as e:
            print(f"댓글 삭제 중 오류: {e}")
    
    async def get_comment_statistics(self, topic: str) -> Dict:
        """주제별 댓글 통계"""
        retriever = self._get_retriever()
        
        try:
            # 전체 컬렉션 통계 (실제로는 토픽별로 필터링 필요)
            stats = retriever.get_collection_stats()
            return {
                "topic": topic,
                "total_comments": stats.get("total_documents", 0),
                "status": "success"
            }
        except Exception as e:
            return {
                "topic": topic,
                "total_comments": 0,
                "status": "error",
                "error": str(e)
            } 