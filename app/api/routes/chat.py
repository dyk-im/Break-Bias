from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
import uuid

router = APIRouter()
chat_service = ChatService()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """채팅 메시지 처리"""
    try:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        response_text, sources = await chat_service.process_message(
            message=request.message,
            conversation_id=conversation_id,
            use_rag=request.use_rag
        )
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            sources=sources
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류 발생: {str(e)}")


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """대화 히스토리 조회"""
    try:
        history = await chat_service.get_conversation_history(conversation_id)
        return {"conversation_id": conversation_id, "messages": history}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 히스토리 조회 중 오류 발생: {str(e)}")


@router.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """대화 히스토리 삭제"""
    try:
        await chat_service.clear_conversation(conversation_id)
        return {"message": "대화가 성공적으로 삭제되었습니다."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 삭제 중 오류 발생: {str(e)}") 