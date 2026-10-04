"""Searchable prompt library with filters, free/premium labels and favourites."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ui  # noqa: E402
from entitlements import can_view, preview
from library import STUDENT_CATEGORY, access_of, category_counts, search_prompts  # noqa: E402
from prompt_loader import get_all_prompts  # noqa: E402

ui.setup("Library", "📚")
ui.header("📚 Prompt Library", "Search the full collection. Student Success prompts are built for study, not for writing assessed work.")


@st.cache_data
def _load():
    return get_all_prompts()


prompts = _load()
st.session_state.setdefault("favorites", [])
fav_titles = {(f["category"], f["title"]) for f in st.session_state.favorites}

query = st.text_input("Search", placeholder="Try: essay, revision, debugging, referencing", key="lib_query")
counts = category_counts(prompts)
f1, f2, f3 = st.columns(3)
category = f1.selectbox("Category", ["All"] + list(counts), index=0, key="lib_cat",
                        format_func=lambda c: c if c == "All" else f"{c} ({counts[c]})")
difficulty = f2.selectbox("Difficulty", ["Any", "beginner", "intermediate", "expert"], key="lib_diff")
access = f3.selectbox("Access", ["Any", "free", "premium"], key="lib_access")

results = search_prompts(prompts, query, category, difficulty, access)
if not query and category == "All" and access == "Any":
    results.sort(key=lambda p: (p.get("category") != STUDENT_CATEGORY, p.get("category", ""), p.get("title", "")))
st.caption(f"{len(results)} prompts")

limit = st.session_state.setdefault("lib_limit", 12)
for i, p in enumerate(results[:limit]):
    acc = access_of(p)
    with st.expander(f"{p['title']}  ·  {p['category']}  ·  {p.get('difficulty_level', '')}"):
        st.markdown(ui.badge(acc), unsafe_allow_html=True)
        st.write(p.get("description", ""))
        if can_view(p, st.session_state.get("entitlement")):
            st.code(p["prompt"], language=None)
        else:
            st.code(preview(p["prompt"]), language=None)
            st.warning("🔒 Premium prompt. Enter an access code on the Account page to see the full text.")
        if p.get("integrity_note"):
            st.info("Integrity: " + p["integrity_note"])
        if p.get("example_input"):
            st.caption("Example: " + p["example_input"])
        st.caption("Tags: " + ", ".join(p.get("tags", [])))
        key = (p["category"], p["title"])
        if key in fav_titles:
            st.caption("⭐ In your favourites")
        elif st.button("⭐ Save to favourites", key=f"fav_{i}_{p['title']}"):
            st.session_state.favorites.append({"title": p["title"], "category": p["category"]})
            st.rerun()

if len(results) > limit:
    if st.button(f"Show more ({len(results) - limit} left)", use_container_width=True):
        st.session_state["lib_limit"] = limit + 12
        st.rerun()

ui.footer()
