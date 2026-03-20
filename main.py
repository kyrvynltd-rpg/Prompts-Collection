"""
Main entry point for the Prompt Improvement Tool
Runs the Streamlit application
"""

import subprocess
import sys
from pathlib import Path
import os

if __name__ == "__main__":
    # Get paths
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    app_path = src_path / "app.py"
    
    # Add src to Python path so imports work
    sys.path.insert(0, str(src_path))
    
    # Change to project root so relative paths work correctly
    os.chdir(project_root)

    # Cloud platforms typically provide PORT via environment variable
    # and require binding on all network interfaces.
    port = os.getenv("PORT", "8501")
    address = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
    
    # Run Streamlit with the app
    subprocess.run([
        sys.executable, 
        "-m", 
        "streamlit", 
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--server.address",
        address,
        "--server.headless",
        "true"
    ])

