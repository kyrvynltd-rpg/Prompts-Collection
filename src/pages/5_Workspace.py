"""Pro: personal prompt workspace and templates."""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import session  # noqa: E402
import ui  # noqa: E402
from tiers import allows  # noqa: E402
from workspace import Workspace, WorkspaceError  # noqa: E402

ui.setup("Workspace", "🗂️")
ui.header("🗂️ Workspace", "Your own prompts and the template pack. A Pro feature.")

user = session.current_user()
if user is None:
    st.info("Sign in on the Account page first.")
    st.stop()
if not allows(session.current_tier(), "pro"):
    st.warning("The workspace and template pack are part of Pro. See plans on the Account page.")
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
        with st.expander(item["title"]):
            st.code(item["body"], language=None)
            if item["tags"]:
                st.caption("Tags: " + ", ".join(item["tags"]))
            if st.button("Delete", key=f"del_{item['id']}"):
                ws.delete(user.id, item["id"])
                st.rerun()
    if items:
        c1, c2 = st.columns(2)
        c1.download_button("Export Markdown", ws.export_markdown(user.id), "my-prompts.md", "text/markdown")
        c2.download_button("Export JSON", ws.export_json(user.id), "my-prompts.json", "application/json")

with tab_tpl:
    path = Path(__file__).resolve().parent.parent.parent / "data" / "templates.json"
    for t in json.loads(path.read_text(encoding="utf-8"))["templates"]:
        with st.expander(f"{t['title']}  ·  {t['category']}"):
            st.code(t["body"], language=None)
            if st.button("Copy to my workspace", key=f"cp_{t['id']}"):
                ws.save(user.id, t["title"], t["body"], t["category"])
                st.success("Saved to your prompts.")

ui.footer()
