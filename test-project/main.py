#!/usr/bin/env python3
"""
Test project main file.
"""

import sys
import os

def main():
    print("Hello from test-project!")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Simple FastAPI app for testing
    try:
        from fastapi import FastAPI
        app = FastAPI(title="Test Project API")
        
        @app.get("/")
        def read_root():
            return {"message": "Hello from test-project!", "version": "1.0.0"}
        
        @app.get("/health")
        def health():
            return {"status": "healthy", "service": "test-project"}
        
        print("FastAPI app created successfully!")
        return app
        
    except ImportError as e:
        print(f"FastAPI not available: {e}")
        return None

if __name__ == "__main__":
    app = main()
    if app:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
