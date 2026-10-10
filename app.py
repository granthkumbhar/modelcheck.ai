
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ModelCheck", page_icon="🧪", layout="wide")

st.title("🧪 ModelCheck")
st.subheader("Test AI quality, safety and regressions")
st.caption("Prototype v0.1 — manual evaluation; not an automated safety certification.")

if "runs" not in st.session_state:
    st.session_state.runs = []
if "baseline" not in st.session_state:
    st.session_state.baseline = {}

st.header("1. Create a test")

test_name = st.text_input("Test name / unique ID", "support-refund-policy-01")
test_type = st.selectbox(
    "Test type",
    ["Quality", "Regression", "Safety / red team"]
)
question = st.text_area("Prompt sent to the AI")
expected = st.text_area("Expected behavior / pass criteria")

a, b = st.columns(2)

with a:
    st.subheader("Model A")
    model_a = st.text_input("Model A label", "GPT")
    answer_a = st.text_area("Paste its answer", height=150)
    correctness_a = st.slider("Correctness A", 1, 5, 3)
    relevance_a = st.slider("Relevance A", 1, 5, 3)
    instructions_a = st.slider("Instruction-following A", 1, 5, 3)
    safe_a = st.radio("Safety A", ["Pass", "Fail", "Not checked"])

with b:
    st.subheader("Model B")
    model_b = st.text_input("Model B label", "Claude")
    answer_b = st.text_area("Paste its answer", height=150)
    correctness_b = st.slider("Correctness B", 1, 5, 3)
    relevance_b = st.slider("Relevance B", 1, 5, 3)
    instructions_b = st.slider("Instruction-following B", 1, 5, 3)
    safe_b = st.radio("Safety B", ["Pass", "Fail", "Not checked"])

score_a = round((correctness_a + relevance_a + instructions_a) / 3, 2)
score_b = round((correctness_b + relevance_b + instructions_b) / 3, 2)

st.write(f"**Current scores:** {model_a} {score_a}/5 · {model_b} {score_b}/5")

if st.button("Save test run", type="primary"):
    if not test_name.strip() or not question.strip():
        st.error("Enter a test name and prompt.")
    elif not answer_a.strip() or not answer_b.strip():
        st.error("Paste both model answers before saving.")
    else:
        st.session_state.runs.append({
            "time": datetime.now().isoformat(timespec="seconds"),
            "test": test_name,
            "type": test_type,
            "prompt": question,
            "expected": expected,
            "model_a": model_a,
            "answer_a": answer_a,
            "score_a": score_a,
            "safety_a": safe_a,
            "model_b": model_b,
            "answer_b": answer_b,
            "score_b": score_b,
            "safety_b": safe_b,
        })
        st.success("Run saved for this session.")

st.divider()
st.header("2. Regression report")

if st.session_state.runs:
    latest = {}
    for run in st.session_state.runs:
        latest[run["test"]] = run

    if st.button("Set latest runs as baseline"):
        st.session_state.baseline = {
            test: {
                "score_a": run["score_a"],
                "score_b": run["score_b"],
                "model_a": run["model_a"],
                "model_b": run["model_b"],
            }
            for test, run in latest.items()
        }
        st.success("Baseline updated.")

    if st.session_state.baseline:
        report = []
        for test, run in latest.items():
            base = st.session_state.baseline.get(test)
            if base:
                delta_a = round(run["score_a"] - base["score_a"], 2)
                delta_b = round(run["score_b"] - base["score_b"], 2)
                report.append({
                    "Test": test,
                    "Model A": run["model_a"],
                    "A score change": delta_a,
                    "Model B": run["model_b"],
                    "B score change": delta_b,
                    "Safety A": run["safety_a"],
                    "Safety B": run["safety_b"],
                })
        if report:
            st.dataframe(pd.DataFrame(report), use_container_width=True)
            st.caption(
                "A negative score change flags a possible regression. "
                "Scores are human-entered ratings, not proof of correctness."
            )
    else:
        st.info("Save some test runs, then set a baseline before changing a prompt or model.")

    st.divider()
    st.header("3. Test history")
    history = pd.DataFrame(st.session_state.runs)
    st.dataframe(
        history[["time", "test", "type", "model_a", "score_a",
                 "safety_a", "model_b", "score_b", "safety_b"]],
        use_container_width=True
    )
    st.download_button(
        "Download results as CSV",
        history.to_csv(index=False).encode("utf-8-sig"),
        file_name="modelcheck-results.csv",
        mime="text/csv"
    )
else:
    st.info("No test runs yet. Add your first comparison above.")

st.caption("Prototype: session data may disappear when the app restarts. Export your CSV to keep a copy.")
