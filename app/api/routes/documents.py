from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.models.schemas import DocumentResponse, DocumentInfo
from app.services.document_service import DocumentService

router = APIRouter()
document_service = DocumentService()


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """문서 업로드 및 벡터화"""
    try:
        # 파일 형식 검증
        allowed_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="지원되지 않는 파일 형식입니다. PDF, TXT, DOCX 파일만 업로드 가능합니다."
            )
        
        document_id = await document_service.upload_and_process_document(file)
        
        return DocumentResponse(
            message="문서가 성공적으로 업로드되었습니다.",
            document_id=document_id,
            status="processing"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 업로드 중 오류 발생: {str(e)}")


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """업로드된 문서 목록 조회"""
    try:
        documents = await document_service.get_all_documents()
        return documents
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 목록 조회 중 오류 발생: {str(e)}")


@router.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    """특정 문서 정보 조회"""
    try:
        document = await document_service.get_document_info(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        return document
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 조회 중 오류 발생: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """문서 삭제"""
    try:
        success = await document_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        
        return {"message": "문서가 성공적으로 삭제되었습니다."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 삭제 중 오류 발생: {str(e)}")


@router.post("/documents/reindex")
async def reindex_documents():
    """모든 문서 재인덱싱"""
    try:
        await document_service.reindex_all_documents()
        return {"message": "모든 문서가 성공적으로 재인덱싱되었습니다."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 재인덱싱 중 오류 발생: {str(e)}") 