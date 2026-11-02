"""Practice mode: write a prompt for a realistic student task and get rubric feedback."""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ui  # noqa: E402
from practice import load_exercises, score_prompt  # noqa: E402

ui.setup("Practice", "🎯")
ui.header("🎯 Prompt Practice", "Write a prompt for a real student task. Get instant feedback on what is missing. Nothing is sent to an AI.")

data = load_exercises()
exercises = data["exercises"]
levels = {lv["id"]: lv for lv in data["levels"]}

st.session_state.setdefault("progress", {})
progress = st.session_state["progress"]

done = sum(1 for p in progress.values() if p["best"] >= 70)
c1, c2, c3 = st.columns(3)
c1.metric("Completed", f"{done}/{len(exercises)}")
c2.metric("Attempts", sum(p["attempts"] for p in progress.values()))
c3.metric("Average best score", f"{round(sum(p['best'] for p in progress.values()) / len(progress)) if progress else 0}%")
st.progress(done / len(exercises))

level_names = {lv["id"]: f"Level {lv['id']}: {lv['name']} - {lv['goal']}" for lv in data["levels"]}
level_id = st.radio("Level", list(level_names), format_func=level_names.get, horizontal=False, key="level")
subset = [e for e in exercises if e["level"] == level_id]
labels = {e["id"]: f"{e['title']}" + (" ✅" if progress.get(e["id"], {}).get("best", 0) >= 70 else "") for e in subset}
ex_id = st.selectbox("Exercise", list(labels), format_func=labels.get, key=f"ex_{level_id}")
ex = next(e for e in subset if e["id"] == ex_id)

st.subheader(ex["title"])
st.write(ex["scenario"])
st.markdown("**A weak prompt would be:**")
st.markdown(f"<div class='pl-weak'>{ex['weak_prompt']}</div>", unsafe_allow_html=True)
st.markdown("")

attempt = st.text_area("Your prompt", height=170, key=f"attempt_{ex_id}",
                       placeholder="Write a better prompt for this task. Say who you are, what you want, limits, and the format.")
if st.button("Check my prompt", type="primary", use_container_width=True, key=f"check_{ex_id}"):
    if not attempt.strip():
        st.warning("Write a prompt first.")
    else:
        res = score_prompt(attempt, ex)
        p = progress.setdefault(ex_id, {"best": 0, "attempts": 0})
        p["attempts"] += 1
        p["best"] = max(p["best"], res.score)
        st.session_state[f"result_{ex_id}"] = res

res = st.session_state.get(f"result_{ex_id}")
if res:
    if res.score >= 70:
        ui.render_confetti()
    ui.render_health_gauge(res.score, res.checks)
    col_a, col_b = st.columns([1, 2])
    col_a.metric("Practice Mastery Score", f"{res.score}%", res.level)
    with col_b:
        if res.missing_terms:
            st.markdown("**Critical Terms Missing:**")
            for term in res.missing_terms:
                st.write(f"❌ Required topic term: `{term}`")
        else:
            st.success("✅ All required domain terms included!")
    for flag in res.flags:
        st.error(flag)
    if res.advice:
        st.markdown("**To improve:**")
        for a in res.advice:
            st.write("- " + a)
    else:
        st.success("Strong prompt. Compare it with the model answer below.")
    st.info("This checks structure, not truth. A high score does not guarantee a correct AI answer.")

with st.expander("Tip and model answer"):
    st.write(ex["tip"])
    st.code(ex["model_prompt"], language=None)

st.divider()
st.markdown("### Save your progress")
st.caption("Progress lives in this browser session. Download it to keep it, and upload it next time.")
st.download_button("Download progress", json.dumps(progress, indent=2), file_name="prompt-practice-progress.json",
                   mime="application/json", use_container_width=True)
up = st.file_uploader("Restore progress", type=["json"], key="restore")
if up is not None:
    try:
        loaded = json.loads(up.getvalue().decode("utf-8"))
        valid = {k: {"best": int(v["best"]), "attempts": int(v["attempts"])} for k, v in loaded.items()
                 if k in {e["id"] for e in exercises}}
        st.session_state["progress"] = {**valid, **{k: v for k, v in progress.items() if k not in valid}}
        st.success(f"Restored {len(valid)} exercises.")
    except (ValueError, KeyError, TypeError):
        st.error("That file is not a valid progress export.")

ui.footer()
