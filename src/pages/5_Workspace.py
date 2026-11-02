"""Pro: personal prompt workspace and templates."""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import session  # noqa: E402
import ui  # noqa: E402
from tiers import allows, feature_tier  # noqa: E402
from workspace import Workspace, WorkspaceError  # noqa: E402

ui.setup("Workspace", "🗂️")
ui.header("🗂️ Workspace", "Your own prompts and the template pack. A Pro feature.")

user = session.current_user()
if user is None:
    st.info("Sign in on the Account page first.")
    st.stop()
need = feature_tier("workspace")
if not allows(session.current_tier(), need):
    st.warning(f"The workspace and template pack are part of {need.capitalize()}. See plans on the Account page.")
    st.stop()

ws = Workspace(session._db())
tab_mine, tab_tpl = st.tabs(["My prompts", "Templates"])

with tab_mine:
    with st.form("save_prompt", clear_on_submit=True):
        title = st.text_input("Title")
        body = st.text_area("Prompt", height=140)
        tags = st.text_input("Tags (comma separated)")
        if st.form_submit_button("Save prompt", type="primary"):
            try:
                ws.save(user.id, title, body, tags)
                st.rerun()
            except WorkspaceError as exc:
                st.error(str(exc))
    items = ws.list(user.id, st.text_input("Search my prompts", key="ws_search"))
    st.caption(f"{len(items)} saved")
    for item in items:
        with st.expander(f"📄 {item['title']}"):
            st.code(item["body"], language=None)
            if item["tags"]:
                tag_chips = " ".join([f"<span class='pl-chip'>{t}</span>" for t in item["tags"]])
                st.markdown(f"**Tags:** {tag_chips}", unsafe_allow_html=True)
            b1, b2 = st.columns([1, 1])
            with b1:
                if st.button("💡 Test in Analyser", key=f"test_{item['id']}", use_container_width=True):
                    st.session_state["prompt_input"] = item["body"]
                    try:
                        st.switch_page("src/app.py")
                    except Exception:
                        try:
                            st.switch_page("app.py")
                        except Exception:
                            st.success("Prompt loaded! Navigate to Prompt Analyser to run.")
            with b2:
                if st.button("🗑️ Delete Prompt", key=f"del_{item['id']}", use_container_width=True):
                    ws.delete(user.id, item["id"])
                    st.rerun()
    if items:
        c1, c2 = st.columns(2)
        c1.download_button("Export Markdown", ws.export_markdown(user.id), "my-prompts.md", "text/markdown")
        c2.download_button("Export JSON", ws.export_json(user.id), "my-prompts.json", "application/json")

with tab_tpl:
    path = Path(__file__).resolve().parent.parent.parent / "data" / "templates.json"
    for t in json.loads(path.read_text(encoding="utf-8"))["templates"]:
        with st.expander(f"📦 {t['title']}  ·  {t['category']}"):
            st.code(t["body"], language=None)
            tb1, tb2 = st.columns([1, 1])
            with tb1:
                if st.button("📥 Save to Workspace", key=f"cp_{t['id']}", use_container_width=True):
                    ws.save(user.id, t["title"], t["body"], t["category"])
                    st.success("Saved to your prompts.")
                    st.rerun()
            with tb2:
                if st.button("🚀 Test in Analyser", key=f"tpl_test_{t['id']}", use_container_width=True):
                    st.session_state["prompt_input"] = t["body"]
                    try:
                        st.switch_page("src/app.py")
                    except Exception:
                        try:
                            st.switch_page("app.py")
                        except Exception:
                            st.success("Prompt loaded! Navigate to Prompt Analyser to run.")

ui.footer()
