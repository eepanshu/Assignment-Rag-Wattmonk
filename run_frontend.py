#!/usr/bin/env python3
"""
Script to run the Streamlit frontend application
"""

import os
import sys
import subprocess
from pathlib import Path
import time
import requests

def check_backend_running():
    """Check if the backend is running."""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Run the frontend application."""
    frontend_dir = Path("Frontend")

    if not check_backend_running():
        print("⚠️  Backend server is not running!")
        print("Please start the backend first by running: python run_backend.py")
        print("Or start it manually: python Backend/main.py")
        
        response = input("\nDo you want to continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print("🎨 Starting RAG Chatbot Frontend...")
    print("📍 Frontend will be available at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the application")
    print("-" * 50)
    
    os.chdir(frontend_dir)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Frontend application stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
