"""Learn: structured modules with lessons, graded exercises and saved progress."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import session  # noqa: E402
import ui  # noqa: E402
from learning import grade, load_modules, module_summary, overall_percent  # noqa: E402

ui.setup("Learn", "🎓")
ui.header("🎓 Learn", "Short modules, graded exercises and a progress track. Grading runs locally and instantly. Nothing is sent to an AI.")


@st.cache_data
def _modules():
    return load_modules()


modules = _modules()
user = session.current_user()
ent = session.current_entitlement()
store = session.progress_store()
saved = store.for_user(user.id) if user else st.session_state.setdefault("guest_progress", {})

st.progress(overall_percent(modules, saved) / 100, text=f"Overall: {overall_percent(modules, saved)}%")
if not user:
    st.caption("Sign in on the Account page to keep your progress across visits.")

for m in modules:
    s = module_summary(m, saved)
    locked = m["access"] == "premium" and ent is None
    label = f"{'🔒 ' if locked else ''}{m['title']}  ({s['done']}/{s['total']})"
    with st.expander(label):
        st.write(m["summary"])
        if locked:
            st.warning("Premium module. Upgrade on the Account page to open it.")
            continue
        for lesson in m["lessons"]:
            st.markdown(f"**{lesson['title']}**  \n{lesson['body']}")
        for e in m["exercises"]:
            st.markdown(f"##### {e['title']}")
            st.write(e["scenario"])
            st.caption(e["task"])
            text = st.text_area("Your prompt", key=f"ta_{e['id']}", height=110)
            if st.button("Check my prompt", key=f"go_{e['id']}"):
                g = grade(e, text)
                if user:
                    store.record(user.id, e["id"], g.score, g.passed)
                else:
                    prev = saved.get(e["id"], {"best_score": 0, "attempts": 0, "passed": 0})
                    saved[e["id"]] = {"best_score": max(prev["best_score"], g.score), "attempts": prev["attempts"] + 1,
                                      "passed": int(bool(prev["passed"]) or g.passed)}
                (st.success if g.passed else st.warning)(f"Score {g.score}%  -  {'passed' if g.passed else 'not yet'}")
                for c in g.checks:
                    st.markdown(f"{'✅' if c.passed else '❌'} {c.label}" + ("" if c.passed else f"  \n&nbsp;&nbsp;&nbsp;_{c.hint}_"))
            if saved.get(e["id"]):
                st.caption(f"Best: {saved[e['id']]['best_score']}%  ·  Attempts: {saved[e['id']]['attempts']}")
            with st.expander("Show a model approach"):
                st.write(e["model_answer_tip"])
        if s["percent"] == 100:
            st.balloons()
            st.success("Module complete.")

ui.footer()
