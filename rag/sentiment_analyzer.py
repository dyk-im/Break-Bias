from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from app.models.schemas import CommentData, SentimentResult
from config.settings import settings
import logging
from langchain.schema import HumanMessage

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Gemini를 사용한 댓글 감정 분석 클래스"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Gemini 모델 초기화"""
        if settings.gemini_api_key:
            try:
                return ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-lite",
                    google_api_key=settings.gemini_api_key,
                    temperature=0.1  # 감정 분석은 낮은 temperature
                )
            except Exception as e:
                logger.error(f"Gemini 초기화 실패: {e}")
        return None

    async def analyze_single_comment(self, text: str) -> Dict[str, float]:
        """단일 댓글 감정 분석"""
        if not self.llm:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        
        prompt = f"""다음 댓글의 감정을 분석해주세요. 긍정, 부정, 중립 점수의 합이 1이 되도록 분석해주세요.
        
댓글: {text}

다음 형식으로 응답해주세요:
positive: (0~1 사이 숫자)
negative: (0~1 사이 숫자)
neutral: (0~1 사이 숫자)"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text.strip()
            
            # 응답 파싱
            scores = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
            for line in result.split('\n'):
                if ':' in line:
                    key, value = line.split(':')
                    key = key.strip().lower()
                    try:
                        value = float(value.strip())
                        if key in scores:
                            scores[key] = value
                    except ValueError:
                        continue
            
            # 정규화
            total = sum(scores.values())
            if total > 0:
                return {k: v/total for k, v in scores.items()}
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
            
        except Exception as e:
            logger.error(f"감정 분석 중 오류: {e}")
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
    
    async def analyze_comments(self, comments: List[CommentData]) -> SentimentResult:
        """여러 댓글의 감정 분석 및 통계"""
        if not comments:
            return SentimentResult(
                positive=0.0,
                negative=0.0,
                neutral=1.0,
                dominant="neutral"
            )
        
        # 모든 댓글 텍스트를 하나로 합쳐서 분석
        combined_text = "\n".join([f"- {comment.text}" for comment in comments])
        
        prompt = f"""다음은 특정 주제에 대한 여러 댓글들입니다. 전체적인 여론의 감정을 분석해주세요.
        
댓글들:
{combined_text}

다음 형식으로 전체 여론의 감정 분포를 분석해주세요:
positive: (0~1 사이 숫자)
negative: (0~1 사이 숫자)
neutral: (0~1 사이 숫자)"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text.strip()
            
            # 응답 파싱
            scores = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
            for line in result.split('\n'):
                if ':' in line:
                    key, value = line.split(':')
                    key = key.strip().lower()
                    try:
                        value = float(value.strip())
                        if key in scores:
                            scores[key] = value
                    except ValueError:
                        continue
            
            # 정규화
            total = sum(scores.values())
            if total > 0:
                scores = {k: v/total for k, v in scores.items()}
            
            # 지배적 감정 결정
            dominant = max(scores.items(), key=lambda x: x[1])[0]
            
            return SentimentResult(
                positive=round(scores["positive"], 3),
                negative=round(scores["negative"], 3),
                neutral=round(scores["neutral"], 3),
                dominant=dominant
            )
            
        except Exception as e:
            logger.error(f"감정 분석 중 오류: {e}")
            return SentimentResult(
                positive=0.0,
                negative=0.0,
                neutral=1.0,
                dominant="neutral"
            )
    
    async def get_sentiment_keywords(self, comments: List[CommentData], sentiment_type: str = "all") -> List[str]:
        """감정별 주요 키워드 추출"""
        if not comments or not self.llm:
            return []
        
        # 감정 타입에 따라 프롬프트 조정
        sentiment_filter = ""
        if sentiment_type == "positive":
            sentiment_filter = "긍정적인 의견에서만"
        elif sentiment_type == "negative":
            sentiment_filter = "부정적인 의견에서만"
        elif sentiment_type == "neutral":
            sentiment_filter = "중립적인 의견에서만"
        
        combined_text = "\n".join([f"- {comment.text}" for comment in comments])
        
        prompt = f"""다음은 특정 주제에 대한 여러 댓글들입니다. {sentiment_filter} 자주 등장하는 주요 키워드를 추출해주세요.
        
댓글들:
{combined_text}

주요 키워드 20개를 쉼표로 구분하여 나열해주세요. 키워드는 명사 위주로 추출해주세요."""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text.strip()
            
            # 쉼표로 구분된 키워드를 리스트로 변환
            keywords = [word.strip() for word in result.split(',')]
            return [word for word in keywords if word]  # 빈 문자열 제거
            
        except Exception as e:
            logger.error(f"키워드 추출 중 오류: {e}")
            return [] 