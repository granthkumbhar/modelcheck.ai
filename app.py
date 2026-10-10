
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="ModelCheck | AI Quality Lab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    .hero {
        padding: 1.5rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 18px;
        margin-bottom: 1.5rem;
    }
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.25);
        padding: 1rem;
        border-radius: 14px;
    }
</style>
""", unsafe_allow_html=True)

if "runs" not in st.session_state:
    st.session_state.runs = []

if "baseline" not in st.session_state:
    st.session_state.baseline = {}

st.sidebar.title("🧪 ModelCheck")
st.sidebar.caption("AI Quality & Reliability")
page = st.sidebar.radio(
    "WORKSPACE",
    ["Overview", "Run a test", "Test history", "Regression report"],
)
st.sidebar.divider()
st.sidebar.caption("Prototype v0.2 · Manual evaluations")

st.title("ModelCheck")
st.markdown(
    "Test AI responses. Compare models. Catch regressions before release."
)

runs = st.session_state.runs
latest = {}
for run in runs:
    latest[run["test"]] = run

if page == "Overview":
    st.markdown("### Your testing overview")

    total = len(runs)
    avg = (
        sum((r["score_a"] + r["score_b"]) / 2 for r in runs) / total
        if total else 0
    )
    safety_failures = sum(
        (r["safety_a"] == "Fail") + (r["safety_b"] == "Fail")
        for r in runs
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Saved test runs", total)
    c2.metric("Average quality", f"{avg:.2f}/5" if total else "—")
    c3.metric("Safety failures", safety_failures)

    st.markdown("### Quick actions")
    left, right = st.columns(2)
    with left:
        st.info("**Model comparison**\n\nCompare two AI answers using the same prompt and scoring criteria.")
        if st.button("＋ Start a test", use_container_width=True):
            st.session_state.page = "Run a test"
            st.rerun()
    with right:
        st.info("**Regression monitoring**\n\nCompare the latest scores with your saved baseline.")
        if st.button("View regression report", use_container_width=True):
            st.session_state.page = "Regression report"
            st.rerun()

    if "page" in st.session_state:
        target = st.session_state.pop("page")
        st.info(f"Choose **{target}** in the sidebar to continue.")

    st.markdown("### Recent activity")
    if runs:
        df = pd.DataFrame(runs)
        st.dataframe(
            df[["time", "test", "type", "model_a", "score_a",
                "model_b", "score_b"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No tests yet. Open Run a test to create your first comparison.")

elif page == "Run a test":
    st.markdown("### Create an evaluation")
    with st.form("evaluation_form"):
        test_name = st.text_input("Test ID", "support-policy-01")
        test_type = st.selectbox(
            "Evaluation type",
            ["Quality", "Regression", "Safety / red team"],
        )
        question = st.text_area("Prompt sent to both models")
        expected = st.text_area("Expected behavior / pass criteria")

        a, b = st.columns(2)
        with a:
            st.markdown("#### Model A")
            model_a = st.text_input("Model A name", "GPT")
            answer_a = st.text_area("Model A answer", height=150)
            ca = st.slider("Correctness A", 1, 5, 3)
            ra = st.slider("Relevance A", 1, 5, 3)
            ia = st.slider("Instruction following A", 1, 5, 3)
            sa = st.selectbox("Safety A", ["Not checked", "Pass", "Fail"])

        with b:
            st.markdown("#### Model B")
            model_b = st.text_input("Model B name", "Claude")
            answer_b = st.text_area("Model B answer", height=150)
            cb = st.slider("Correctness B", 1, 5, 3)
            rb = st.slider("Relevance B", 1, 5, 3)
            ib = st.slider("Instruction following B", 1, 5, 3)
            sb = st.selectbox("Safety B", ["Not checked", "Pass", "Fail"])

        submitted = st.form_submit_button(
            "Save evaluation", type="primary", use_container_width=True
        )

    if submitted:
        if not test_name.strip() or not question.strip():
            st.error("Enter both a test ID and a prompt.")
        elif not answer_a.strip() or not answer_b.strip():
            st.error("Paste both model answers before saving.")
        else:
            score_a = round((ca + ra + ia) / 3, 2)
            score_b = round((cb + rb + ib) / 3, 2)

            st.session_state.runs.append({
                "time": datetime.now().isoformat(timespec="seconds"),
                "test": test_name.strip(),
                "type": test_type,
                "prompt": question,
                "expected": expected,
                "model_a": model_a,
                "answer_a": answer_a,
                "score_a": score_a,
                "safety_a": sa,
                "model_b": model_b,
                "answer_b": answer_b,
                "score_b": score_b,
                "safety_b": sb,
            })
            st.success(
                f"Saved! {model_a}: {score_a}/5 · {model_b}: {score_b}/5"
            )
            if sa == "Fail" or sb == "Fail":
                st.warning("Safety failure recorded. Review the answers before release.")
            st.rerun()

elif page == "Test history":
    st.markdown("### Evaluation history")
    if runs:
        df = pd.DataFrame(runs)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download complete CSV report",
            df.to_csv(index=False).encode("utf-8-sig"),
            file_name="modelcheck-report.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Your saved evaluations will appear here.")

elif page == "Regression report":
    st.markdown("### Regression monitoring")
    st.caption(
        "Save a baseline, run the same test again, and compare the latest scores."
    )

    if latest:
        if st.button("Set latest results as baseline", type="primary"):
            st.session_state.baseline = {
                name: {
                    "score_a": r["score_a"],
                    "score_b": r["score_b"],
                    "model_a": r["model_a"],
                    "model_b": r["model_b"],
                    "safety_a": r["safety_a"],
                    "safety_b": r["safety_b"],
                }
                for name, r in latest.items()
            }
            st.success("Baseline saved for this session.")
            st.rerun()

        if st.session_state.baseline:
            rows = []
            for name, r in latest.items():
                base = st.session_state.baseline.get(name)
                if not base:
                    rows.append({
                        "Test": name,
                        "Status": "New test — no baseline",
                        "Change A": "—",
                        "Change B": "—",
                    })
                    continue

                da = round(r["score_a"] - base["score_a"], 2)
                db = round(r["score_b"] - base["score_b"], 2)
                safety_issue = (
                    r["safety_a"] == "Fail" or r["safety_b"] == "Fail"
                )
                regression = da < 0 or db < 0

                status = (
                    "Safety failure" if safety_issue
                    else "Review score drop" if regression
                    else "No score drop detected"
                )
                rows.append({
                    "Test": name,
                    "Status": status,
                    "Change A": da,
                    "Change B": db,
                })

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "These comparisons use manually entered ratings. "
                "No score drop does not guarantee that an AI system is safe."
            )
        else:
            st.info("Save test runs, then click Set latest results as baseline.")
    else:
        st.info("Run at least one evaluation to begin regression monitoring.")

st.divider()
st.caption(
    "ModelCheck is an early prototype. Scores are human ratings, "
    "and session data may disappear when the app restarts."
)
