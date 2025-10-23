#!/usr/bin/env python3
"""
Reset ChromaDB database script
This script deletes the existing ChromaDB database to start fresh
"""

import os
import shutil
from pathlib import Path

def main():
    """Main function to reset the database."""
    print("🔄 Resetting ChromaDB Database...")
    
    # Find ChromaDB directory
    backend_dir = Path(__file__).parent / "Backend"
    chroma_dir = backend_dir / "chroma_db"
    
    print(f"📁 ChromaDB directory: {chroma_dir}")
    
    if chroma_dir.exists():
        try:
            shutil.rmtree(chroma_dir)
            print("✅ ChromaDB database deleted successfully")
        except Exception as e:
            print(f"❌ Error deleting database: {e}")
            return False
    else:
        print("ℹ️ ChromaDB database directory doesn't exist")
    
    print("🎉 Database reset completed!")
    print("💡 Run 'python process_documents.py' to process documents into the fresh database.")
    return True

if __name__ == "__main__":
    main()
