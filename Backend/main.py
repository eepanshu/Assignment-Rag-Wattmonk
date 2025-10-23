from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import tempfile
from dotenv import load_dotenv
from rag_chatbot import RAGChatbot
import uvicorn

load_dotenv()

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

chatbot = RAGChatbot(GEMINI_API_KEY)
class ChatRequest(BaseModel):
    query: str
    maintain_history: bool = True

class ChatResponse(BaseModel):
    query: str
    response: str
    intent: Dict[str, Any]
    context_used: List[Dict[str, Any]]
    sources_count: int
    has_context: bool
    timestamp: str

class SearchRequest(BaseModel):
    query: str
    document_type: Optional[str] = None
    n_results: int = 5

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    filename: str

@app.get("/")
async def root():
    return {"message": "RAG Chatbot API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = chatbot.chat(request.query, request.maintain_history)
        return ChatResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_knowledge_base(request: SearchRequest):
    try:
        results = chatbot.search_knowledge_base(
            request.query,
            request.document_type,
            request.n_results
        )
        return {
            "query": request.query,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-document", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...)
):
    try:
        if document_type.lower() not in ['nec', 'wattmonk']:
            raise HTTPException(
                status_code=400,
                detail="Document type must be 'nec' or 'wattmonk'"
            )
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            success = chatbot.document_processor.process_document(tmp_file_path, document_type)

            if success:
                return DocumentUploadResponse(
                    success=True,
                    message=f"Document '{file.filename}' processed successfully",
                    filename=file.filename
                )
            else:
                return DocumentUploadResponse(
                    success=False,
                    message=f"Failed to process document '{file.filename}'",
                    filename=file.filename
                )
        finally:
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation-history")
async def get_conversation_history(limit: int = 10):
    """Get conversation history."""
    try:
        history = chatbot.get_conversation_history(limit)
        return {"history": history, "total_messages": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversation-history")
async def clear_conversation_history():
    """Clear conversation history."""
    try:
        chatbot.clear_conversation_history()
        return {"message": "Conversation history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system-stats")
async def get_system_stats():
    """Get system statistics."""
    try:
        stats = chatbot.get_system_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/initialize-documents")
async def initialize_documents(force_reinit: bool = False):
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(root_dir, "data")

        print(f"Looking for documents in: {data_dir}")
        print(f"Force reinitialize: {force_reinit}")

        processed_files = []
        errors = []

        nec_file = os.path.join(data_dir, "2017-NEC-Code-2 (1).pdf")
        if os.path.exists(nec_file):
            success = chatbot.document_processor.process_document(nec_file, "nec")
            if success:
                processed_files.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "status": "success"})
            else:
                errors.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "error": "Processing failed"})
        else:
            errors.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "error": "File not found"})

        wattmonk_file = os.path.join(data_dir, "Wattmonk Information.docx")
        if os.path.exists(wattmonk_file):
            success = chatbot.document_processor.process_document(wattmonk_file, "wattmonk")
            if success:
                processed_files.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "status": "success"})
            else:
                errors.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "error": "Processing failed"})
        else:
            errors.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "error": "File not found"})
        
        return {
            "message": "Document initialization completed",
            "processed_files": processed_files,
            "errors": errors,
            "total_processed": len(processed_files),
            "total_errors": len(errors)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset-database")
async def reset_database():
    """Reset the vector database and reinitialize with documents."""
    try:
        import shutil

        print("🔄 Starting database reset...")

        chroma_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
        print(f"ChromaDB directory: {chroma_dir}")

        if os.path.exists(chroma_dir):
            shutil.rmtree(chroma_dir)
            print("✅ Deleted existing ChromaDB")
        else:
            print("ℹ️ ChromaDB directory didn't exist")

        global chatbot
        print("🔄 Reinitializing chatbot...")
        try:
            chatbot = RAGChatbot(GEMINI_API_KEY)
            print("✅ Chatbot reinitialized")
        except Exception as e:
            print(f"❌ Failed to reinitialize chatbot: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to reinitialize chatbot: {str(e)}")

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(root_dir, "data")
        print(f"📁 Looking for documents in: {data_dir}")

        processed_files = []
        errors = []
        nec_file = os.path.join(data_dir, "2017-NEC-Code-2 (1).pdf")
        print(f"🔍 Looking for NEC file: {nec_file}")

        if os.path.exists(nec_file):
            print(f"✅ Found NEC file, size: {os.path.getsize(nec_file)} bytes")
            print(f"📄 Processing NEC file: {nec_file}")
            try:
                success = chatbot.document_processor.process_document(nec_file, "nec")
                if success:
                    processed_files.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "status": "success"})
                    print("✅ NEC document processed successfully")
                else:
                    errors.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "error": "Processing failed"})
                    print("❌ NEC document processing failed")
            except Exception as e:
                error_msg = f"Exception during processing: {str(e)}"
                errors.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "error": error_msg})
                print(f"❌ NEC processing exception: {e}")
        else:
            errors.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "error": "File not found"})
            print(f"❌ NEC file not found at: {nec_file}")


        wattmonk_file = os.path.join(data_dir, "Wattmonk Information.docx")
        print(f"🔍 Looking for Wattmonk file: {wattmonk_file}")

        if os.path.exists(wattmonk_file):
            print(f"✅ Found Wattmonk file, size: {os.path.getsize(wattmonk_file)} bytes")
            print(f"📄 Processing Wattmonk file: {wattmonk_file}")
            try:
                success = chatbot.document_processor.process_document(wattmonk_file, "wattmonk")
                if success:
                    processed_files.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "status": "success"})
                    print("✅ Wattmonk document processed successfully")
                else:
                    errors.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "error": "Processing failed"})
                    print("❌ Wattmonk document processing failed")
            except Exception as e:
                error_msg = f"Exception during processing: {str(e)}"
                errors.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "error": error_msg})
                print(f"❌ Wattmonk processing exception: {e}")
        else:
            errors.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "error": "File not found"})
            print(f"❌ Wattmonk file not found at: {wattmonk_file}")


        final_stats = chatbot.get_system_stats()
        print(f"📊 Final stats: {final_stats}")

        return {
            "message": "Database reset and reinitialized",
            "processed_files": processed_files,
            "errors": errors,
            "total_processed": len(processed_files),
            "total_errors": len(errors),
            "final_stats": final_stats
        }

    except Exception as e:
        print(f"❌ Reset database failed with error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@app.post("/force-process-documents")
async def force_process_documents():
    """Force process documents without resetting database."""
    try:
        print("🔄 Force processing documents...")

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(root_dir, "data")
        print(f"📁 Looking for documents in: {data_dir}")

        processed_files = []
        errors = []
        nec_file = os.path.join(data_dir, "2017-NEC-Code-2 (1).pdf")
        print(f"🔍 Looking for NEC file: {nec_file}")

        if os.path.exists(nec_file):
            print(f"✅ Found NEC file, size: {os.path.getsize(nec_file)} bytes")
            try:
                success = chatbot.document_processor.process_document(nec_file, "nec")
                if success:
                    processed_files.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "status": "success"})
                    print("✅ NEC document processed successfully")
                else:
                    errors.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "error": "Processing returned False"})
                    print("❌ NEC document processing returned False")
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                errors.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "error": error_msg})
                print(f"❌ NEC processing exception: {e}")
        else:
            errors.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "error": "File not found"})
            print(f"❌ NEC file not found")


        wattmonk_file = os.path.join(data_dir, "Wattmonk Information.docx")
        print(f"🔍 Looking for Wattmonk file: {wattmonk_file}")

        if os.path.exists(wattmonk_file):
            print(f"✅ Found Wattmonk file, size: {os.path.getsize(wattmonk_file)} bytes")
            try:
                success = chatbot.document_processor.process_document(wattmonk_file, "wattmonk")
                if success:
                    processed_files.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "status": "success"})
                    print("✅ Wattmonk document processed successfully")
                else:
                    errors.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "error": "Processing returned False"})
                    print("❌ Wattmonk document processing returned False")
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                errors.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "error": error_msg})
                print(f"❌ Wattmonk processing exception: {e}")
        else:
            errors.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "error": "File not found"})
            print(f"❌ Wattmonk file not found")


        final_stats = chatbot.get_system_stats()
        print(f"📊 Final stats: {final_stats}")

        return {
            "message": "Force processing completed",
            "processed_files": processed_files,
            "errors": errors,
            "total_processed": len(processed_files),
            "total_errors": len(errors),
            "final_stats": final_stats
        }

    except Exception as e:
        print(f"❌ Force processing failed: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Force processing failed: {str(e)}")

@app.get("/debug-search")
async def debug_search(query: str = "zippy"):
    """Debug search to see what's actually in the database."""
    try:
        print(f"🔍 Debug searching for: '{query}'")

        wattmonk_collection = chatbot.document_processor.wattmonk_collection

        all_docs = wattmonk_collection.get()

        print(f"Total Wattmonk documents: {len(all_docs['documents'])}")
        matching_docs = []
        for i, doc in enumerate(all_docs['documents']):
            if query.lower() in doc.lower():
                matching_docs.append({
                    "index": i,
                    "content": doc,
                    "metadata": all_docs['metadatas'][i] if all_docs['metadatas'] else {}
                })

        print(f"Found {len(matching_docs)} documents containing '{query}'")

        search_results = chatbot.search_knowledge_base(f"Wattmonk {query}", "wattmonk", 5)

        return {
            "query": query,
            "total_documents": len(all_docs['documents']),
            "direct_matches": len(matching_docs),
            "matching_documents": matching_docs[:3],
            "search_results": search_results
        }

    except Exception as e:
        print(f"❌ Debug search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
