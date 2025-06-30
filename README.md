# YouTube Opinion Analysis Agent

유튜브 댓글을 기반으로 특정 주제에 대한 여론을 분석하는 RAG AI 에이전트입니다.

## 🎯 주요 기능

- **📺 YouTube 댓글 수집**: 특정 주제로 영상 검색 후 댓글 대량 수집
- **🧠 감정 분석**: 댓글의 긍정/부정/중립 감정 자동 분석  
- **📊 여론 분석**: RAG를 활용한 지능적인 여론 요약 및 분석
- **🔍 의미적 검색**: 질문과 관련된 댓글들을 벡터 검색으로 찾기
- **📈 시각화**: 감정 분포와 키워드 분석 결과 제공

## 📋 시스템 플로우

```
[댓글 수집 및 정제] → [댓글 임베딩 → Vector DB 저장]
    ↓
[사용자 질문] → [질문 임베딩] → [Top-K 관련 댓글 검색]
    ↓
[감정 분석] + [LLM 요약 생성] → [응답 통합: 요약 + 여론 퍼센티지]
```

## 🛠 기술 스택

- **Backend**: FastAPI
- **Frontend**: Streamlit  
- **AI Framework**: LangChain
- **LLM**: Gemini Pro (무료 API) / OpenAI GPT (백업)
- **Vector Store**: ChromaDB
- **Embeddings**: Sentence Transformers
- **YouTube API**: Google API Client
- **Sentiment Analysis**: Transformers, VADER, TextBlob
- **API**: Youtube API

## 📁 프로젝트 구조

```
├── app/                    # FastAPI 애플리케이션
│   ├── api/routes/         
│   │   ├── youtube.py      # YouTube 분석 API
│   │   ├── chat.py         # 대화형 질의응답
│   │   └── documents.py    # 문서 관리 (기존)
│   ├── models/schemas.py   # 데이터 모델
│   └── services/
│       └── youtube_analysis_service.py # 분석 서비스
├── frontend/main.py        # Streamlit 웹 인터페이스
├── rag/                    # RAG 시스템 핵심
│   ├── youtube_service.py  # YouTube API 연동
│   ├── sentiment_analyzer.py # 감정 분석
│   ├── document_processor.py # 댓글 처리 및 청킹
│   ├── embeddings/         # 임베딩 관리
│   ├── retrieval/          # 벡터 검색
│   └── generation/         # LLM 응답 생성
├── data/                   # 데이터 저장소
│   ├── cache/              # 캐시 데이터
│   ├── vectorstore/        # 벡터 DB
│   └── results/            # 분석 결과
└── config/settings.py      # 환경 설정
```
