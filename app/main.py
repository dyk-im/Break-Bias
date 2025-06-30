from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import chat, documents, youtube
from config.settings import settings

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="YouTube Opinion Analysis API",
    description="유튜브 댓글 기반 여론 분석 AI 에이전트",
    version="1.0.0",
    debug=settings.debug
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(youtube.router, prefix="/api/v1", tags=["youtube"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "YouTube Opinion Analysis API에 오신 것을 환영합니다!",
        "description": "유튜브 댓글을 수집하고 여론을 분석하는 AI 에이전트입니다.",
        "features": [
            "YouTube 댓글 수집",
            "감정 분석",
            "여론 요약",
            "RAG 기반 질의응답"
        ]
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "version": "1.0.0", "service": "youtube-opinion-analysis"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    ) 