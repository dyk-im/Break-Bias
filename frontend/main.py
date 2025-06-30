import streamlit as st
import requests
import json
from typing import List, Dict

# 페이지 설정
st.set_page_config(
    page_title="RAG AI Agent",
    page_icon="🤖",
    layout="wide"
)

# API URL 설정
API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    st.title("🤖 RAG AI Agent")
    st.markdown("RAG(Retrieval-Augmented Generation)를 활용한 AI 에이전트입니다.")
    
    # 사이드바
    with st.sidebar:
        st.header("📁 문서 관리")
        
        # 문서 업로드
        uploaded_file = st.file_uploader(
            "문서 업로드",
            type=['pdf', 'txt', 'docx'],
            help="PDF, TXT, DOCX 파일을 업로드할 수 있습니다."
        )
        
        if uploaded_file is not None:
            if st.button("문서 업로드"):
                upload_document(uploaded_file)
        
        st.divider()
        
        # 업로드된 문서 목록
        st.subheader("📋 업로드된 문서")
        display_documents()
        
        st.divider()
        
        # 설정
        st.subheader("⚙️ 설정")
        use_rag = st.checkbox("RAG 사용", value=True, help="체크 해제시 RAG 없이 일반 LLM 응답만 사용")
    
    # 메인 채팅 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 채팅")
        
        # 대화 히스토리 초기화
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "conversation_id" not in st.session_state:
            st.session_state.conversation_id = None
        
        # 대화 히스토리 표시
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and message.get("sources"):
                    with st.expander("📚 참고 문서"):
                        for source in message["sources"]:
                            if source:
                                st.write(f"- {source}")
        
        # 채팅 입력
        if prompt := st.chat_input("메시지를 입력하세요..."):
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # AI 응답 생성
            with st.chat_message("assistant"):
                with st.spinner("응답 생성 중..."):
                    response, sources = send_chat_message(prompt, use_rag)
                st.markdown(response)
                
                if sources:
                    with st.expander("📚 참고 문서"):
                        for source in sources:
                            if source:
                                st.write(f"- {source}")
            
            # 응답을 히스토리에 추가
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "sources": sources
            })
    
    with col2:
        st.header("📊 시스템 정보")
        
        # API 상태 확인
        api_status = check_api_status()
        if api_status:
            st.success("✅ API 서버 연결됨")
        else:
            st.error("❌ API 서버 연결 실패")
        
        # 대화 관리
        st.subheader("🗂️ 대화 관리")
        if st.button("대화 초기화"):
            clear_conversation()
        
        # 통계 정보 (추후 구현)
        st.subheader("📈 통계")
        st.info("업로드된 문서 수: 확인 중...")


def upload_document(file):
    """문서 업로드"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)
        
        if response.status_code == 200:
            st.success(f"✅ '{file.name}' 업로드 완료!")
            st.rerun()  # 페이지 새로고침
        else:
            st.error(f"❌ 업로드 실패: {response.text}")
    except Exception as e:
        st.error(f"❌ 업로드 중 오류 발생: {str(e)}")


def display_documents():
    """업로드된 문서 목록 표시"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        if response.status_code == 200:
            documents = response.json()
            
            if documents:
                for doc in documents:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        status_emoji = "✅" if doc["status"] == "completed" else "⏳" if doc["status"] == "processing" else "❌"
                        st.write(f"{status_emoji} {doc['filename']}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{doc['id']}", help="문서 삭제"):
                            delete_document(doc['id'])
            else:
                st.info("업로드된 문서가 없습니다.")
        else:
            st.error("문서 목록을 불러올 수 없습니다.")
    except Exception as e:
        st.error(f"문서 목록 조회 중 오류: {str(e)}")


def delete_document(document_id: str):
    """문서 삭제"""
    try:
        response = requests.delete(f"{API_BASE_URL}/documents/{document_id}")
        if response.status_code == 200:
            st.success("✅ 문서가 삭제되었습니다.")
            st.rerun()
        else:
            st.error("❌ 문서 삭제 실패")
    except Exception as e:
        st.error(f"❌ 문서 삭제 중 오류: {str(e)}")


def send_chat_message(message: str, use_rag: bool = True):
    """채팅 메시지 전송"""
    try:
        payload = {
            "message": message,
            "conversation_id": st.session_state.conversation_id,
            "use_rag": use_rag
        }
        
        response = requests.post(f"{API_BASE_URL}/chat", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.conversation_id = data["conversation_id"]
            return data["response"], data.get("sources", [])
        else:
            return f"오류 발생: {response.text}", []
    except Exception as e:
        return f"채팅 요청 중 오류 발생: {str(e)}", []


def clear_conversation():
    """대화 초기화"""
    st.session_state.messages = []
    if st.session_state.conversation_id:
        try:
            requests.delete(f"{API_BASE_URL}/conversations/{st.session_state.conversation_id}")
        except:
            pass
    st.session_state.conversation_id = None
    st.success("✅ 대화가 초기화되었습니다.")
    st.rerun()


def check_api_status():
    """API 서버 상태 확인"""
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health")
        return response.status_code == 200
    except:
        return False


if __name__ == "__main__":
    main() 