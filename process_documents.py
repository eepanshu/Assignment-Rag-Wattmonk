#!/usr/bin/env python3
"""
Independent document processing script for RAG Chatbot
This script processes documents from the data folder and stores them in ChromaDB
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add Backend directory to path so we can import modules
backend_dir = Path(__file__).parent / "Backend"
sys.path.insert(0, str(backend_dir))

from document_processor import DocumentProcessor

def main():
    """Main function to process documents."""
    print("🚀 Starting Document Processing...")
    
    # Load environment variables
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("❌ .env file not found in Backend directory")
        print("Please create Backend/.env with your GEMINI_API_KEY")
        sys.exit(1)
    
    load_dotenv(env_file)
    
    # Get API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        print("Please add your Gemini API key to Backend/.env")
        sys.exit(1)
    
    print("✅ API key loaded successfully")
    
    # Initialize document processor
    chroma_persist_directory = str(backend_dir / "chroma_db")
    print(f"📁 ChromaDB directory: {chroma_persist_directory}")
    
    try:
        processor = DocumentProcessor(gemini_api_key, chroma_persist_directory)
        print("✅ Document processor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize document processor: {e}")
        sys.exit(1)
    
    # Find documents in data folder
    data_dir = Path(__file__).parent / "data"
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        sys.exit(1)
    
    print(f"📁 Looking for documents in: {data_dir}")
    
    # Process documents
    processed_files = []
    errors = []
    
    # Process NEC PDF
    nec_file = data_dir / "2017-NEC-Code-2 (1).pdf"
    if nec_file.exists():
        print(f"📄 Processing NEC file: {nec_file}")
        print(f"📊 File size: {nec_file.stat().st_size / (1024*1024):.1f} MB")
        
        try:
            success = processor.process_document(str(nec_file), "nec")
            if success:
                processed_files.append({"file": nec_file.name, "type": "nec", "status": "success"})
                print("✅ NEC document processed successfully")
            else:
                errors.append({"file": nec_file.name, "type": "nec", "error": "Processing returned False"})
                print("❌ NEC document processing failed")
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            errors.append({"file": nec_file.name, "type": "nec", "error": error_msg})
            print(f"❌ NEC processing exception: {e}")
    else:
        errors.append({"file": "2017-NEC-Code-2 (1).pdf", "type": "nec", "error": "File not found"})
        print(f"❌ NEC file not found: {nec_file}")
    
    # Process Wattmonk DOCX
    wattmonk_file = data_dir / "Wattmonk Information.docx"
    if wattmonk_file.exists():
        print(f"📄 Processing Wattmonk file: {wattmonk_file}")
        print(f"📊 File size: {wattmonk_file.stat().st_size / 1024:.1f} KB")
        
        try:
            success = processor.process_document(str(wattmonk_file), "wattmonk")
            if success:
                processed_files.append({"file": wattmonk_file.name, "type": "wattmonk", "status": "success"})
                print("✅ Wattmonk document processed successfully")
            else:
                errors.append({"file": wattmonk_file.name, "type": "wattmonk", "error": "Processing returned False"})
                print("❌ Wattmonk document processing failed")
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            errors.append({"file": wattmonk_file.name, "type": "wattmonk", "error": error_msg})
            print(f"❌ Wattmonk processing exception: {e}")
    else:
        errors.append({"file": "Wattmonk Information.docx", "type": "wattmonk", "error": "File not found"})
        print(f"❌ Wattmonk file not found: {wattmonk_file}")
    
    # Get final statistics
    try:
        stats = processor.get_collection_stats()
        print(f"\n📊 Final Statistics:")
        print(f"   NEC documents: {stats['nec_documents']}")
        print(f"   Wattmonk documents: {stats['wattmonk_documents']}")
        print(f"   Total documents: {stats['total_documents']}")
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
    
    # Summary
    print(f"\n🎯 Processing Summary:")
    print(f"   ✅ Successfully processed: {len(processed_files)} files")
    print(f"   ❌ Errors: {len(errors)} files")
    
    if processed_files:
        print(f"\n✅ Processed files:")
        for file_info in processed_files:
            print(f"   - {file_info['file']} ({file_info['type']})")
    
    if errors:
        print(f"\n❌ Failed files:")
        for error_info in errors:
            print(f"   - {error_info['file']}: {error_info['error']}")
    
    if len(processed_files) > 0:
        print(f"\n🎉 Document processing completed successfully!")
        print(f"💡 You can now start the backend and ask questions about the processed documents.")
    else:
        print(f"\n⚠️ No documents were processed successfully.")
        sys.exit(1)

if __name__ == "__main__":
    main()
