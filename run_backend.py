#!/usr/bin/env python3
"""
Script to run the FastAPI backend server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the backend server."""
    backend_dir = Path("Backend")
    
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("❌ .env file not found in Backend directory")
        print("Please run setup.py first or create the .env file manually")
        sys.exit(1)
    
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not found in .env file")
        print("Please add your Gemini API key to Backend/.env")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    print("🚀 Starting RAG Chatbot Backend...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    os.chdir(backend_dir)
    
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
