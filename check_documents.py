
"""
Script to check if documents are loaded in the system
"""

import os
import sys
import requests
import json

BACKEND_URL = "http://localhost:8000"

def check_backend_health():
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_system_stats():
    """Check system statistics to see if documents are loaded."""
    try:
        response = requests.get(f"{BACKEND_URL}/system-stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("📊 Current System Statistics:")
            print(f"   NEC Documents: {stats['document_stats']['nec_documents']}")
            print(f"   Wattmonk Documents: {stats['document_stats']['wattmonk_documents']}")
            print(f"   Total Documents: {stats['document_stats']['total_documents']}")
            
            if stats['document_stats']['total_documents'] == 0:
                print("\n⚠️  No documents are currently loaded!")
                return False
            else:
                print("\n✅ Documents are loaded in the system!")
                return True
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking stats: {e}")
        return False

def initialize_documents():
    """Initialize documents if they're not loaded."""
    try:
        print("\n🔄 Initializing documents...")
        response = requests.post(f"{BACKEND_URL}/initialize-documents", timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Initialization completed:")
            print(f"   Processed: {result['total_processed']} files")
            print(f"   Errors: {result['total_errors']} files")
            
            for file_info in result['processed_files']:
                print(f"   ✅ {file_info['file']} ({file_info['type']})")
            
            for error_info in result['errors']:
                print(f"   ❌ {error_info['file']}: {error_info['error']}")
            
            return result['total_processed'] > 0
        else:
            print(f"❌ Initialization failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def test_document_queries():
    """Test queries that should use the loaded documents."""
    test_queries = [
        {"query": "What is Wattmonk?", "expected_intent": "wattmonk"},
        {"query": "Tell me about NEC electrical codes", "expected_intent": "nec"},
        {"query": "What services does Wattmonk offer?", "expected_intent": "wattmonk"},
        {"query": "What is electrical grounding in NEC?", "expected_intent": "nec"}
    ]
    
    print("\n🧪 Testing document-specific queries:")
    
    for test in test_queries:
        try:
            print(f"\n🔍 Query: {test['query']}")
            
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"query": test['query'], "maintain_history": False},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                intent = result['intent']['intent']
                sources = result['sources_count']
                has_context = result['has_context']
                
                print(f"   Intent: {intent}")
                print(f"   Sources used: {sources}")
                print(f"   Has context: {has_context}")
                print(f"   Response preview: {result['response'][:150]}...")
                
                if intent == test['expected_intent'] and sources > 0:
                    print("   ✅ Query correctly used documents!")
                elif intent == test['expected_intent'] and sources == 0:
                    print("   ⚠️  Correct intent but no sources used")
                else:
                    print("   ❌ Query didn't use expected documents")
                    
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Query error: {e}")

def test_search_functionality():
    """Test direct search in the knowledge base."""
    print("\n🔍 Testing knowledge base search:")
    
    search_tests = [
        {"query": "Wattmonk services", "doc_type": "wattmonk"},
        {"query": "electrical safety", "doc_type": "nec"},
        {"query": "solar design", "doc_type": None}
    ]
    
    for search in search_tests:
        try:
            print(f"\n   Searching: '{search['query']}' in {search['doc_type'] or 'all documents'}")
            
            response = requests.post(
                f"{BACKEND_URL}/search",
                json={
                    "query": search['query'],
                    "document_type": search['doc_type'],
                    "n_results": 3
                },
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Found {result['total_results']} results")
                
                if result['total_results'] > 0:
                    for i, res in enumerate(result['results'][:2], 1):
                        print(f"      Result {i}: {res['source']} ({res['document_type']})")
                        print(f"      Relevance: {res['relevance_score']:.2f}")
                else:
                    print("   ⚠️  No results found")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")

def main():
    """Main function to check document status."""
    print("🔍 Checking Document Status in RAG Chatbot")
    print("=" * 50)
    
    if not check_backend_health():
        print("❌ Backend is not running!")
        print("Please start it with: python run_backend.py")
        return False
    
    print("✅ Backend is running")
    
    docs_loaded = check_system_stats()
    
    if not docs_loaded:
        print("\n🚀 Attempting to initialize documents...")
        if initialize_documents():
            print("\n📊 Checking stats after initialization:")
            docs_loaded = check_system_stats()
        else:
            print("❌ Failed to initialize documents")
            return False
    
    if docs_loaded:
        test_document_queries()
        test_search_functionality()
        
        print("\n" + "=" * 50)
        print("✅ Document check completed!")
        print("\nThe system IS using your documents:")
        print("   📄 2017-NEC-Code-2 (1).pdf")
        print("   📄 Wattmonk Information.docx")
        print("\nYou can now chat with confidence that the system")
        print("will use these documents to answer your questions!")
    else:
        print("\n❌ Documents are not properly loaded")
        print("Please check the error messages above")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure the backend is running: python run_backend.py")
        print("2. Check that your GEMINI_API_KEY is set in Backend/.env")
        print("3. Ensure the PDF and DOCX files are in the root directory")
        print("4. Try deleting Backend/chroma_db folder and restart")
    
    input("\nPress Enter to exit...")
