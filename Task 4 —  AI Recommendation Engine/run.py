import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
VENV_PYTHON = BACKEND_DIR / "venv" / "Scripts" / "python.exe"

def main():
    print("=================================================================")
    print("Starting CineMatch AI - Recommendation Engine System")
    print("Backend API: Isolated venv + Security Middleware")
    print("Frontend: Cleanly Decoupled Interface")
    print("=================================================================")

    if not VENV_PYTHON.exists():
        print(f"[!] Backend venv not found at {VENV_PYTHON}!")
        print("Please run: python -m venv backend/venv && backend/venv/Scripts/pip install -r backend/requirements.txt")
        sys.exit(1)

    # Launch Backend REST API in background
    print("Launching Backend API on http://127.0.0.1:5000...")
    api_process = subprocess.Popen(
        [str(VENV_PYTHON), "app.py"],
        cwd=str(BACKEND_DIR)
    )

    time.sleep(1.5)

    # Open Frontend
    frontend_index = FRONTEND_DIR / "index.html"
    print(f"Opening Frontend at: {frontend_index}")
    webbrowser.open(frontend_index.as_uri())

    try:
        api_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down CineMatch AI...")
        api_process.terminate()

if __name__ == "__main__":
    main()
