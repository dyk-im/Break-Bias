from typing import List, Optional, Tuple, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.models.schemas import ChatMessage, CommentData, SentimentResult
from rag.sentiment_analyzer import SentimentAnalyzer
from config.settings import settings
import google.generativeai as genai


class OpinionAnalysisGenerator:
    """댓글 분석 및 여론 요약을 위한 LLM 응답 생성 클래스"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.llm = self._initialize_llm()
        self.analysis_prompt_template = self._create_analysis_prompt_template()
        self.summary_prompt_template = self._create_summary_prompt_template()
    
    def _initialize_llm(self):
        """LLM 초기화 (Gemini 사용)"""
        
        if not settings.gemini_api_key:
            return None
            
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=settings.gemini_api_key,
                temperature=settings.temperature,
                max_output_tokens=settings.max_tokens
            )
        except Exception as e:
            print(f"Gemini 초기화 실패: {e}")
            return None
    
    def _create_analysis_prompt_template(self) -> ChatPromptTemplate:
        """댓글 분석용 프롬프트 템플릿"""
        system_message = """당신은 유튜브 댓글을 분석하는 전문가입니다.
주어진 댓글들을 바탕으로 사용자의 질문에 대한 여론을 분석하고 요약해주세요.

분석 시 다음 사항을 고려하세요:
1. 댓글의 전반적인 감정(긍정/부정/중립)
2. 주요 논점과 의견들
3. 찬성/반대 의견의 근거
4. 댓글 작성자들의 주요 관심사
5. 여론의 전반적인 방향성

다음 형식으로 답변해주세요:
### 📊 여론 분석 요약
[전체적인 여론 동향과 주요 포인트]

### 💭 주요 의견들
[긍정적 의견]
- 의견 1
- 의견 2

[부정적 의견]  
- 의견 1
- 의견 2

[중립적/기타 의견]
- 의견 1
- 의견 2

### 🎯 결론
[종합적인 분석 결과]

관련 댓글들:
{comments}

감정 분석 결과: {sentiment_stats}"""

        human_message = "질문: {query}"
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message)
        ])
    
    def _create_summary_prompt_template(self) -> ChatPromptTemplate:
        """간단 요약용 프롬프트 템플릿"""
        system_message = """주어진 댓글들을 바탕으로 질문에 대한 간단한 답변을 제공해주세요.
답변은 한국어로 작성하고, 3-5문장으로 핵심만 요약해주세요.

댓글 내용: {comments}
감정 분석: {sentiment_stats}"""

        human_message = "질문: {query}"
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message)
        ])
    
    async def generate_opinion_analysis(
        self, 
        query: str, 
        relevant_comments: List[Dict], 
        detailed: bool = True
    ) -> Tuple[str, Dict]:
        """여론 분석 응답 생성"""
        
        if not relevant_comments:
            return self._generate_no_data_response(query), {}
        
        # 1. 댓글에서 CommentData 추출 또는 구성
        comment_texts = []
        for comment_dict in relevant_comments:
            content = comment_dict.get("content", "")
            metadata = comment_dict.get("metadata", {})
            comment_texts.append({
                "text": content,
                "author": metadata.get("author", "익명"),
                "like_count": metadata.get("like_count", 0),
                "video_title": metadata.get("video_title", "")
            })
        
        # 2. 감정 분석
        sentiment_stats = await self._analyze_comment_sentiments(comment_texts)
        
        # 3. 댓글 텍스트 포맷팅
        formatted_comments = self._format_comments_for_llm(comment_texts)
        
        # 4. LLM 응답 생성
        if not self.llm:
            return self._generate_dummy_analysis(query, sentiment_stats), sentiment_stats
        
        try:
            if detailed:
                prompt = self.analysis_prompt_template.format_messages(
                    query=query,
                    comments=formatted_comments,
                    sentiment_stats=self._format_sentiment_stats(sentiment_stats)
                )
            else:
                prompt = self.summary_prompt_template.format_messages(
                    query=query,
                    comments=formatted_comments,
                    sentiment_stats=self._format_sentiment_stats(sentiment_stats)
                )
            
            response = await self.llm.agenerate([prompt])
            analysis_text = response.generations[0][0].text.strip()
            
            return analysis_text, sentiment_stats
            
        except Exception as e:
            error_msg = f"분석 생성 중 오류 발생: {str(e)}"
            return error_msg, sentiment_stats
    
    async def _analyze_comment_sentiments(self, comment_texts: List[Dict]) -> Dict:
        """댓글들의 감정 분석"""
        if not comment_texts:
            return {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
                "total_comments": 0,
                "dominant": "neutral"
            }
        
        sentiments = []
        for comment in comment_texts:
            sentiment = await self.sentiment_analyzer.analyze_single_comment(comment["text"])
            sentiments.append(sentiment)
        
        # 평균 계산
        avg_positive = sum(s["positive"] for s in sentiments) / len(sentiments)
        avg_negative = sum(s["negative"] for s in sentiments) / len(sentiments)
        avg_neutral = sum(s["neutral"] for s in sentiments) / len(sentiments)
        
        # 지배적 감정
        if avg_positive > avg_negative and avg_positive > avg_neutral:
            dominant = "positive"
        elif avg_negative > avg_positive and avg_negative > avg_neutral:
            dominant = "negative"
        else:
            dominant = "neutral"
        
        return {
            "positive": round(avg_positive, 3),
            "negative": round(avg_negative, 3),
            "neutral": round(avg_neutral, 3),
            "total_comments": len(comment_texts),
            "dominant": dominant
        }
    
    def _format_comments_for_llm(self, comment_texts: List[Dict]) -> str:
        """LLM에 전달할 댓글 포맷팅"""
        formatted = []
        
        for i, comment in enumerate(comment_texts[:20], 1):  # 최대 20개만
            text = comment["text"][:200]  # 각 댓글 최대 200자
            author = comment["author"]
            likes = comment["like_count"]
            
            formatted.append(f"[댓글 {i}] {author} (👍{likes}): {text}")
        
        return "\n".join(formatted)
    
    def _format_sentiment_stats(self, sentiment_stats: Dict) -> str:
        """감정 통계 포맷팅"""
        return f"""
긍정: {sentiment_stats['positive']:.1%}
부정: {sentiment_stats['negative']:.1%}  
중립: {sentiment_stats['neutral']:.1%}
전체 댓글 수: {sentiment_stats['total_comments']}개
지배적 감정: {sentiment_stats['dominant']}
"""
    
    def _generate_dummy_analysis(self, query: str, sentiment_stats: Dict) -> str:
        """API 키가 없을 때의 더미 분석"""
        return f"""
### 📊 여론 분석 요약 (더미 데이터)
'{query}'에 대한 분석이 요청되었습니다.

### 💭 주요 의견들
현재 AI 모델이 설정되지 않아 실제 분석을 수행할 수 없습니다.

감정 분석 결과:
- 긍정: {sentiment_stats['positive']:.1%}
- 부정: {sentiment_stats['negative']:.1%}
- 중립: {sentiment_stats['neutral']:.1%}

### 🎯 결론
실제 사용을 위해서는 Gemini API 키를 설정해주세요.
"""
    
    def _generate_no_data_response(self, query: str) -> str:
        """관련 댓글이 없을 때의 응답"""
        return f"""
### ⚠️ 데이터 부족
'{query}'와 관련된 댓글을 찾을 수 없습니다.

다음을 확인해보세요:
1. 검색어가 정확한지 확인
2. 해당 주제의 댓글이 수집되었는지 확인
3. 더 일반적인 키워드로 다시 시도

먼저 해당 주제의 유튜브 댓글을 수집해주세요.
"""
    
    async def generate_simple_response(
        self,
        query: str,
        context_documents: List[Dict],
        conversation_history: List[ChatMessage] = None
    ) -> str:
        """간단한 RAG 응답 생성"""
        if not self.llm:
            return "죄송합니다. AI 모델이 초기화되지 않았습니다."
        
        # 컨텍스트 문서 포맷팅
        context_text = ""
        if context_documents:
            context_text = "\n".join([
                f"- {doc.get('content', '')[:200]}..."
                for doc in context_documents[:3]
            ])
        
        # 대화 히스토리 포맷팅
        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in conversation_history[-5:]  # 최근 5개만
            ])
        
        prompt_text = f"""다음 정보를 바탕으로 사용자의 질문에 답변해주세요.

관련 정보:
{context_text}

이전 대화:
{history_text}

질문: {query}

답변:"""
        
        try:
            # ChatPromptTemplate을 사용하여 메시지 형식 수정
            from langchain.schema import HumanMessage
            messages = [HumanMessage(content=prompt_text)]
            response = await self.llm.agenerate([messages])
            return response.generations[0][0].text.strip()
        except Exception as e:
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def generate_direct_response(
        self,
        query: str,
        conversation_history: List[ChatMessage] = None
    ) -> str:
        """RAG 없이 직접 응답 생성"""
        if not self.llm:
            return "죄송합니다. AI 모델이 초기화되지 않았습니다."
        
        # 대화 히스토리 포맷팅
        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in conversation_history[-5:]  # 최근 5개만
            ])
        
        prompt_text = f"""사용자와 자연스럽게 대화해주세요.

이전 대화:
{history_text}

사용자: {query}

어시스턴트:"""
        
        try:
            # ChatPromptTemplate을 사용하여 메시지 형식 수정
            from langchain.schema import HumanMessage
            messages = [HumanMessage(content=prompt_text)]
            response = await self.llm.agenerate([messages])
            return response.generations[0][0].text.strip()
        except Exception as e:
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}" 