import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile
from app.models.schemas import DocumentInfo
from rag.document_processor import DocumentProcessor
from config.settings import settings


class DocumentService:
    """문서 관리 서비스 클래스"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.document_metadata = {}  # 실제로는 데이터베이스 사용
        
        # 문서 저장 디렉토리 생성
        os.makedirs(settings.documents_path, exist_ok=True)
    
    async def upload_and_process_document(self, file: UploadFile) -> str:
        """문서 업로드 및 처리"""
        
        # 고유 문서 ID 생성
        document_id = str(uuid.uuid4())
        
        # 파일 저장
        file_path = os.path.join(settings.documents_path, f"{document_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 메타데이터 저장
        self.document_metadata[document_id] = DocumentInfo(
            id=document_id,
            filename=file.filename,
            upload_date=datetime.now().isoformat(),
            size=len(content),
            status="processing"
        )
        
        try:
            # 문서 처리 및 벡터화 (백그라운드에서 실행될 수 있음)
            await self.document_processor.process_document(file_path, document_id)
            
            # 상태 업데이트
            self.document_metadata[document_id].status = "completed"
            
        except Exception as e:
            self.document_metadata[document_id].status = "failed"
            raise e
        
        return document_id
    
    async def get_all_documents(self) -> List[DocumentInfo]:
        """모든 문서 정보 조회"""
        return list(self.document_metadata.values())
    
    async def get_document_info(self, document_id: str) -> Optional[DocumentInfo]:
        """특정 문서 정보 조회"""
        return self.document_metadata.get(document_id)
    
    async def delete_document(self, document_id: str) -> bool:
        """문서 삭제"""
        if document_id not in self.document_metadata:
            return False
        
        # 파일 시스템에서 문서 삭제
        doc_info = self.document_metadata[document_id]
        file_path = os.path.join(settings.documents_path, f"{document_id}_{doc_info.filename}")
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 벡터 저장소에서 문서 삭제
        await self.document_processor.delete_document(document_id)
        
        # 메타데이터에서 삭제
        del self.document_metadata[document_id]
        
        return True
    
    async def reindex_all_documents(self):
        """모든 문서 재인덱싱"""
        for document_id, doc_info in self.document_metadata.items():
            if doc_info.status == "completed":
                file_path = os.path.join(settings.documents_path, f"{document_id}_{doc_info.filename}")
                if os.path.exists(file_path):
                    doc_info.status = "processing"
                    try:
                        await self.document_processor.process_document(file_path, document_id)
                        doc_info.status = "completed"
                    except Exception:
                        doc_info.status = "failed" 