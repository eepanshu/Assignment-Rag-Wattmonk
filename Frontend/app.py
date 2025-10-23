import streamlit as st
import requests
import json
from typing import Dict, Any, List
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="RAG Chatbot - Wattmonk & NEC Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
    }
    .intent-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .intent-nec {
        background-color: #ff9800;
        color: white;
    }
    .intent-wattmonk {
        background-color: #9c27b0;
        color: white;
    }
    .intent-general {
        background-color: #607d8b;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict[str, Any]:
    """Make API request to the backend."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {"error": str(e)}

def display_chat_message(message: Dict[str, Any], is_user: bool = False):
    """Display a chat message with proper formatting."""
    if is_user:
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {message}
        </div>
        """, unsafe_allow_html=True)
    else:
        intent = message.get("intent", {}).get("intent", "general")
        intent_class = f"intent-{intent}"
        
        st.markdown(f"""
        <div class="chat-message bot-message">
            <div>
                <span class="intent-badge {intent_class}">{intent.upper()}</span>
                <strong>Assistant:</strong>
            </div>
            <div style="margin-top: 0.5rem;">{message.get("response", "")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if message.get("sources_count", 0) > 0:
            with st.expander(f"📚 Sources Used ({message['sources_count']})"):
                for i, context in enumerate(message.get("context_used", []), 1):
                    st.write(f"**Source {i}:** {context['metadata'].get('source', 'Unknown')}")
                    st.write(f"**Type:** {context['metadata'].get('document_type', 'Unknown').upper()}")
                    st.write(f"**Content:** {context['content'][:200]}...")
                    st.divider()

def main():
    """Main application function."""
    st.markdown('<h1 class="main-header">🤖 RAG Chatbot Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### Your AI assistant for NEC Code Guidelines and Wattmonk Information")
    
    with st.sidebar:
        st.header("🛠️ Controls")
        
        if st.button("🚀 Initialize System", help="Load NEC and Wattmonk documents"):
            with st.spinner("Initializing documents..."):
                result = make_api_request("/initialize-documents", "POST")
                if "error" not in result:
                    st.success(f"✅ Processed {result.get('total_processed', 0)} documents")
                    if result.get('errors'):
                        st.warning(f"⚠️ {result.get('total_errors', 0)} errors occurred")
                        for error in result['errors']:
                            st.error(f"❌ {error['file']}: {error['error']}")
                else:
                    st.error("❌ Initialization failed")

        if st.button("🔄 Reset & Reload Documents", help="Clear database and reload documents"):
            with st.spinner("Resetting database and reloading documents..."):
                result = make_api_request("/reset-database", "POST")
                if "error" not in result:
                    st.success(f"✅ Database reset! Processed {result.get('total_processed', 0)} documents")
                    if result.get('errors'):
                        st.warning(f"⚠️ {result.get('total_errors', 0)} errors occurred")
                        for error in result['errors']:
                            st.error(f"❌ {error['file']}: {error['error']}")
                else:
                    st.error("❌ Reset failed")

        if st.button("⚡ Force Process Documents", help="Process documents without resetting database"):
            with st.spinner("Force processing documents..."):
                result = make_api_request("/force-process-documents", "POST")
                if "error" not in result:
                    st.success(f"✅ Force processing completed! Processed {result.get('total_processed', 0)} documents")
                    if result.get('final_stats'):
                        stats = result['final_stats']
                        st.info(f"📊 Database now contains: NEC={stats.get('document_stats', {}).get('nec_documents', 0)}, Wattmonk={stats.get('document_stats', {}).get('wattmonk_documents', 0)}")
                    if result.get('errors'):
                        st.warning(f"⚠️ {result.get('total_errors', 0)} errors occurred")
                        for error in result['errors']:
                            st.error(f"❌ {error['file']}: {error['error']}")
                else:
                    st.error("❌ Force processing failed")

        if st.button("🔍 Debug Search for 'Zippy'", help="Check if Zippy info is in database"):
            with st.spinner("Searching for Zippy..."):
                result = make_api_request("/debug-search?query=zippy", "GET")
                if "error" not in result:
                    st.write(f"**Total Wattmonk documents:** {result.get('total_documents', 0)}")
                    st.write(f"**Documents containing 'zippy':** {result.get('direct_matches', 0)}")

                    if result.get('matching_documents'):
                        st.write("**Matching documents:**")
                        for i, doc in enumerate(result['matching_documents']):
                            st.write(f"Document {i+1}: {doc['content'][:200]}...")

                    if result.get('search_results'):
                        st.write("**Search results:**")
                        for i, res in enumerate(result['search_results']):
                            st.write(f"Result {i+1}: {res['content'][:200]}...")
                else:
                    st.error("❌ Debug search failed")
        
        st.divider()
        
        if st.button("📊 Show System Stats"):
            stats = make_api_request("/system-stats")
            if "error" not in stats:
                st.metric("NEC Documents", stats['document_stats']['nec_documents'])
                st.metric("Wattmonk Documents", stats['document_stats']['wattmonk_documents'])
                st.metric("Conversation Length", stats['conversation_length'])
        
        st.divider()
        
        if st.button("🗑️ Clear Conversation"):
            result = make_api_request("/conversation-history", "DELETE")
            if "error" not in result:
                st.success("✅ Conversation cleared")
                st.rerun()
        
        st.divider()
        
        st.subheader("📄 Upload Document")
        uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'txt', 'docx'])
        doc_type = st.selectbox("Document Type", ["nec", "wattmonk"])
        
        if uploaded_file and st.button("Upload & Process"):
            with st.spinner("Processing document..."):
                files = {"file": uploaded_file}
                data = {"document_type": doc_type}
                result = make_api_request("/upload-document", "POST", data=data, files=files)
                
                if result.get("success"):
                    st.success(f"✅ {result['message']}")
                else:
                    st.error(f"❌ {result.get('message', 'Upload failed')}")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    user_input = st.chat_input("Ask me about NEC codes, Wattmonk services, or anything else...")

    if user_input:

        st.session_state.messages.append({"type": "user", "content": user_input})

        with st.spinner("Thinking..."):
            response = make_api_request("/chat", "POST", {"query": user_input})

            if "error" not in response:
                st.session_state.messages.append({"type": "bot", "content": response})
            else:
                st.error("Failed to get response from the chatbot")

        st.rerun()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("💬 Chat Interface")

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message["type"] == "user":
                    display_chat_message(message["content"], is_user=True)
                else:
                    display_chat_message(message["content"], is_user=False)

    with col2:
        st.subheader("🔍 Knowledge Base Search")
        
        search_query = st.text_input("Search query:")
        search_type = st.selectbox("Search in:", ["All", "NEC", "Wattmonk"], key="search_type")
        search_results_count = st.slider("Number of results:", 1, 10, 5)
        
        if st.button("🔍 Search") and search_query:
            doc_type = None if search_type == "All" else search_type.lower()
            
            with st.spinner("Searching..."):
                search_data = {
                    "query": search_query,
                    "document_type": doc_type,
                    "n_results": search_results_count
                }
                results = make_api_request("/search", "POST", search_data)
                
                if "error" not in results:
                    st.write(f"**Found {results['total_results']} results:**")
                    
                    for i, result in enumerate(results['results'], 1):
                        with st.expander(f"Result {i} - {result['source']} ({result['document_type'].upper()})"):
                            st.write(f"**Relevance:** {result['relevance_score']:.2f}")
                            st.write(f"**Content:** {result['content']}")
                else:
                    st.error("Search failed")
        
        st.subheader("⚡ Quick Questions")
        quick_questions = [
            "What is Wattmonk?",
            "What services does Wattmonk offer?",
            "What is NEC code?",
            "Tell me about electrical safety standards",
            "What is Zippy tool?"
        ]
        
        for question in quick_questions:
            if st.button(question, key=f"quick_{question}"):

                st.session_state.messages.append({"type": "user", "content": question})

                with st.spinner("Getting answer..."):
                    response = make_api_request("/chat", "POST", {"query": question})

                    if "error" not in response:
                        st.session_state.messages.append({"type": "bot", "content": response})
                    else:
                        st.error("Failed to get response from the chatbot")

                st.rerun()

if __name__ == "__main__":
    main()
