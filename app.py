
import io
import zipfile
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TraceGate | AI Testing",
    page_icon="🛡️",
    layout="wide",
)

# -----------------------------
# Session state
# -----------------------------
if "test_history" not in st.session_state:
    st.session_state.test_history = []

if "scan_history" not in st.session_state:
    st.session_state.scan_history = []

if "last_scan" not in st.session_state:
    st.session_state.last_scan = None


def add_history(record):
    st.session_state.test_history.insert(0, record)
    st.session_state.test_history = st.session_state.test_history[:100]


def scan_zip(uploaded_file):
    """Inspect ZIP contents without executing uploaded code."""
    findings = []
    file_rows = []

    source_extensions = (
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".json", ".yaml", ".yml", ".toml", ".env", ".txt",
    )

    patterns = {
        "Possible hard-coded secret": [
            "api_key =", "api_key=", "secret_key =",
            "secret_key=", "password =", "password=",
            "OPENAI_API_KEY=", "ghp_",
        ],
        "Potential unsafe execution": [
            "eval(", "exec(", "os.system(",
            "subprocess.Popen(",
        ],
        "Potential prompt-injection wording": [
            "ignore all previous instructions",
            "ignore previous instructions",
            "reveal your system prompt",
        ],
    }

    try:
        with zipfile.ZipFile(io.BytesIO(uploaded_file.getvalue())) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]

            for member in members:
                name = member.filename

                file_rows.append({
                    "File": name,
                    "Size (KB)": round(member.file_size / 1024, 2),
                })

                if name.lower().endswith((".env", ".pem", ".key")):
                    findings.append({
                        "Severity": "High",
                        "File": name,
                        "Finding": "Sensitive-looking file in archive",
                        "Details": "Check whether this file should be included.",
                    })

                if (
                    member.file_size > 1_000_000
                    or not name.lower().endswith(source_extensions)
                ):
                    continue

                text = archive.read(member).decode("utf-8", errors="ignore")
                lower_text = text.lower()

                for category, matches in patterns.items():
                    found = [
                        pattern for pattern in matches
                        if pattern.lower() in lower_text
                    ]

                    if found:
                        severity = (
                            "High"
                            if category == "Possible hard-coded secret"
                            else "Medium"
                        )
                        findings.append({
                            "Severity": severity,
                            "File": name,
                            "Finding": category,
                            "Details": "Matched: " + ", ".join(found[:5]),
                        })

    except zipfile.BadZipFile:
        raise ValueError("The uploaded file is not a valid ZIP archive.")

    # Remove duplicate findings.
    unique = []
    seen = set()

    for finding in findings:
        key = tuple(finding.items())
        if key not in seen:
            seen.add(key)
            unique.append(finding)

    return file_rows, unique


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## 🛡️ TraceGate")
    st.caption("AI application testing workspace")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Upload & Scan",
            "Run a Test",
            "Test History",
            "Regression Report",
        ],
    )

    st.divider()
    st.caption("Static scan mode")
    st.caption("Uploaded code is inspected, never executed.")


# -----------------------------
# Overview
# -----------------------------
if page == "Overview":
    st.title("🛡️ TraceGate")
    st.subheader("Test AI applications before they reach users.")
    st.write(
        "Inspect project ZIP files, compare model responses, "
        "and review saved test results."
    )

    total_tests = len(st.session_state.test_history)
    total_scans = len(st.session_state.scan_history)

    failures = sum(
        item["result"] == "Fail"
        for item in st.session_state.test_history
    )

    pass_rate = (
        (total_tests - failures) / total_tests * 100
        if total_tests else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Manual tests", total_tests)
    col2.metric("ZIP scans", total_scans)
    col3.metric(
        "Pass rate",
        f"{pass_rate:.0f}%" if total_tests else "—",
    )

    st.divider()
    st.markdown("### Get started")
    st.markdown("- **Upload & Scan:** Inspect a project ZIP.")
    st.markdown("- **Run a Test:** Compare expected and actual AI behavior.")
    st.markdown("- **Test History:** Review saved tests.")
    st.markdown("- **Regression Report:** Summarize pass and fail results.")

    if st.session_state.test_history:
        st.markdown("### Recent tests")
        st.dataframe(
            pd.DataFrame(st.session_state.test_history).head(5),
            use_container_width=True,
            hide_index=True,
        )


# -----------------------------
# Upload & Scan
# -----------------------------
elif page == "Upload & Scan":
    st.title("📦 Upload & Scan")
    st.write(
        "Upload a ZIP archive to check for common warning signs "
        "in filenames and source text."
    )
    st.caption("This is a static scan. Uploaded code is not executed.")

    uploaded_file = st.file_uploader(
        "Choose your project ZIP",
        type=["zip"],
    )

    if uploaded_file is not None:
        st.write(
            f"Selected: **{uploaded_file.name}** "
            f"({uploaded_file.size / 1024:.1f} KB)"
        )

        if st.button("Scan ZIP", type="primary"):
            try:
                with st.spinner("Inspecting archive..."):
                    file_rows, findings = scan_zip(uploaded_file)

                st.session_state.last_scan = {
                    "filename": uploaded_file.name,
                    "files": file_rows,
                    "findings": findings,
                }

                counts = sum(
                    item["Severity"] == "High"
                    for item in findings
                )

                st.session_state.scan_history.insert(0, {
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Filename": uploaded_file.name,
                    "Files": len(file_rows),
                    "Findings": len(findings),
                    "High severity": counts,
                })

                st.session_state.scan_history = (
                    st.session_state.scan_history[:100]
                )

            except ValueError as exc:
                st.error(str(exc))

    result = st.session_state.last_scan

    if result:
        st.divider()
        st.subheader(f"Results: {result['filename']}")

        files = result["files"]
        findings = result["findings"]

        high_count = sum(
            item["Severity"] == "High"
            for item in findings
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Files inspected", len(files))
        col2.metric("Findings", len(findings))
        col3.metric("High severity", high_count)

        if findings:
            st.warning(
                "Review these heuristic matches. "
                "Some findings may be false positives."
            )
            findings_df = pd.DataFrame(findings)
            st.dataframe(
                findings_df,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "Download findings CSV",
                data=findings_df.to_csv(index=False).encode("utf-8"),
                file_name="tracegate_scan_findings.csv",
                mime="text/csv",
            )
        else:
            st.success(
                "No matching warning patterns were found "
                "by this basic scanner."
            )

        with st.expander("View ZIP file list"):
            st.dataframe(
                pd.DataFrame(files),
                use_container_width=True,
                hide_index=True,
            )


# -----------------------------
# Run a Test
# -----------------------------
elif page == "Run a Test":
    st.title("🧪 Run a Test")
    st.write(
        "Record a manual comparison between expected AI behavior "
        "and the response you observed."
    )
    st.caption("This form does not call a model API automatically.")

    with st.form("manual_test_form"):
        test_name = st.text_input(
            "Test name",
            placeholder="e.g. Refuses request for private data",
        )

        category = st.selectbox(
            "Test category",
            [
                "Correctness",
                "Safety",
                "Prompt injection",
                "Privacy",
                "Reliability",
                "Other",
            ],
        )

        prompt = st.text_area("Prompt / test input")
        expected = st.text_area("Expected response or behavior")
        actual = st.text_area("Actual model response")
        notes = st.text_area("Notes (optional)")

        result = st.radio(
            "Result",
            ["Pass", "Fail", "Needs review"],
            horizontal=True,
        )

        submitted = st.form_submit_button(
            "Save test",
            type="primary",
        )

    if submitted:
        if not test_name.strip():
            st.error("Please enter a test name.")
        elif not prompt.strip():
            st.error("Please enter a prompt or test input.")
        else:
            add_history({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "test_name": test_name.strip(),
                "category": category,
                "result": result,
                "prompt": prompt.strip(),
                "expected": expected.strip(),
                "actual": actual.strip(),
                "notes": notes.strip(),
            })

            st.success("Test saved to this session's history.")

    st.divider()
    st.subheader("Quick text comparison")

    col1, col2 = st.columns(2)

    with col1:
        quick_expected = st.text_area(
            "Expected text",
            key="quick_expected",
        )

    with col2:
        quick_actual = st.text_area(
            "Observed text",
            key="quick_actual",
        )

    if st.button("Compare text"):
        if not quick_expected.strip() or not quick_actual.strip():
            st.info("Enter both texts before comparing.")
        elif quick_expected.strip() == quick_actual.strip():
            st.success("The texts match exactly.")
        else:
            st.warning(
                "The texts differ. Review them manually; "
                "this simple comparison does not judge meaning."
            )


# -----------------------------
# Test History
# -----------------------------
elif page == "Test History":
    st.title("📚 Test History")

    history = st.session_state.test_history

    if not history:
        st.info("No tests have been saved in this session yet.")
    else:
        df = pd.DataFrame(history)

        col1, col2 = st.columns(2)

        with col1:
            result_filter = st.selectbox(
                "Filter by result",
                ["All", "Pass", "Fail", "Needs review"],
            )

        with col2:
            categories = ["All"] + sorted(
                df["category"].dropna().unique().tolist()
            )
            category_filter = st.selectbox(
                "Filter by category",
                categories,
            )

        filtered = df.copy()

        if result_filter != "All":
            filtered = filtered[
                filtered["result"] == result_filter
            ]

        if category_filter != "All":
            filtered = filtered[
                filtered["category"] == category_filter
            ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Export history as CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="tracegate_test_history.csv",
            mime="text/csv",
        )

        with st.expander("View a test's details"):
            if not filtered.empty:
                chosen = st.selectbox(
                    "Choose a test",
                    filtered.index,
                    format_func=lambda index: filtered.loc[
                        index, "test_name"
                    ],
                )

                row = filtered.loc[chosen]

                st.write("**Result:**", row["result"])
                st.write("**Category:**", row["category"])
                st.write("**Prompt:**", row["prompt"])
                st.write("**Expected:**", row["expected"] or "(Not provided)")
                st.write("**Actual:**", row["actual"] or "(Not provided)")
                st.write("**Notes:**", row["notes"] or "(None)")


# -----------------------------
# Regression Report
# -----------------------------
elif page == "Regression Report":
    st.title("📈 Regression Report")
    st.write("Summarize the manual tests recorded in this session.")

    history = st.session_state.test_history

    if not history:
        st.info("Save some tests first to generate a report.")
    else:
        df = pd.DataFrame(history)

        total = len(df)
        passed = int((df["result"] == "Pass").sum())
        failed = int((df["result"] == "Fail").sum())
        review = int((df["result"] == "Needs review").sum())

        pass_rate = passed / total * 100 if total else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total tests", total)
        col2.metric("Passed", passed)
        col3.metric("Failed", failed)
        col4.metric("Pass rate", f"{pass_rate:.1f}%")

        st.subheader("Results by category")

        summary = (
            df.groupby(["category", "result"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Tests needing attention")

        attention = df[
            df["result"].isin(["Fail", "Needs review"])
        ]

        if attention.empty:
            st.success("No failed or review-needed tests in this session.")
        else:
            st.dataframe(
                attention[
                    ["time", "test_name", "category", "result", "notes"]
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.download_button(
            "Download regression report CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="tracegate_regression_report.csv",
            mime="text/csv",
        )


st.divider()
st.caption(
    "TraceGate prototype · Scan results are heuristic indicators, "
    "not a security guarantee."
)
