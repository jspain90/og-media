#!/usr/bin/env python
"""
Production script to run the backend server as a Windows service
"""
import uvicorn
import logging
from pathlib import Path

# Configure logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",  # Only localhost - Cloudflare tunnel handles external access
        port=8003,
        reload=False,  # Disable reload for production
        log_level="info",
        access_log=True,
        log_config=None,  # Use default uvicorn logging
    )
