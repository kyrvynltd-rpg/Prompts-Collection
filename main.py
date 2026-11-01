"""
Main entry point for the Prompt Improvement Tool.
Supports both `streamlit run main.py` (Streamlit Community Cloud default)
and `python main.py` (Docker / CLI).
"""

import os
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
app_path = src_path / "app.py"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def _running_inside_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


if _running_inside_streamlit():
    import streamlit as st

    import ui

    ui.sync_runtime_env()
    nav = st.navigation([
        st.Page("src/app.py", title="Prompt Analyser", icon="💡", default=True),
        st.Page("src/pages/1_Practice.py", title="Practice", icon="🎯", url_path="Practice"),
        st.Page("src/pages/2_Library.py", title="Library", icon="📚", url_path="Library"),
        st.Page("src/pages/3_Account.py", title="Account", icon="🔑", url_path="Account"),
        st.Page("src/pages/4_Learn.py", title="Learn", icon="🎓", url_path="Learn"),
        st.Page("src/pages/5_Workspace.py", title="Workspace", icon="🗂️", url_path="Workspace"),
        st.Page("src/pages/6_AI_Feedback.py", title="AI Feedback", icon="🤖", url_path="AI_Feedback"),
    ])
    nav.run()
elif __name__ == "__main__":
    os.chdir(project_root)
    port = os.getenv("PORT", "8501")
    address = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
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
        "true",
    ])
