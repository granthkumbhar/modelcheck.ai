
import io
import re
import stat
import zipfile
from pathlib import PurePosixPath
from datetime import datetime, timezone

import pandas as pd
import streamlit as st


# ==================================================
# TRACEGATE - AI APPLICATION TESTING
# ==================================================

st.set_page_config(
    page_title="TraceGate | AI Testing",
    page_icon="🛡️",
    layout="wide",
)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_FILES = 500
MAX_TOTAL_EXPANDED = 50 * 1024 * 1024
MAX_TEXT_FILE = 2 * 1024 * 1024

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json",
    ".yaml", ".yml", ".toml", ".txt", ".md", ".html",
    ".sql", ".sh", ".cfg", ".ini", ".xml", ".css",
}

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}

AI_MARKERS = [
    "openai", "anthropic", "google.generativeai",
    "langchain", "llamaindex", "litellm",
    "transformers", "ollama",
]

SECRET_PATTERNS = [
    ("Possible API key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Possible GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    (
        "Private key marker",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "Possible hard-coded credential",
        re.compile(r"""(?i)\b(?:api_key|api-key|secret_key|password|access_token)\s*[:=]\s*['"][^'"]{8,}['"]"""),
    ),
]

RISK_PATTERNS = [
    ("Dynamic code execution", re.compile(r"\beval\s*\(|\bexec\s*\(")),
    (
        "Shell execution",
        re.compile(r"\bos\.system\s*\(|\bsubprocess\.(?:run|Popen|call)\s*\("),
    ),
    ("Deserialization", re.compile(r"\bpickle\.loads?\s*\(")),
    ("Potentially unsafe YAML loading", re.compile(r"\byaml\.load\s*\(")),
]


def scan_project_zip(uploaded_bytes):
    if len(uploaded_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("ZIP exceeds the 20 MB upload limit.")

    findings = []
    inventory = []
    ai_markers_found = set()
    source_count = 0
    total_expanded = 0

    def add_finding(severity, file_name, line_number, message):
        findings.append({
            "Severity": severity,
            "File": file_name,
            "Line": line_number,
            "Finding": message,
        })

    try:
        archive = zipfile.ZipFile(io.BytesIO(uploaded_bytes))
    except (zipfile.BadZipFile, OSError):
        raise ValueError("This is not a valid ZIP archive.")

    with archive:
        members = archive.infolist()

        if len(members) > MAX_FILES:
            raise ValueError("ZIP contains too many entries. Limit: 500.")

        for info in members:
            if info.is_dir():
                continue

            name = info.filename.replace("\\", "/")
            path = PurePosixPath(name)

            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Unsafe file path detected. Scan cancelled.")

            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError("Symbolic links are not accepted.")

            if info.file_size < 0:
                raise ValueError("Invalid file size in ZIP archive.")

            total_expanded += info.file_size
            if total_expanded > MAX_TOTAL_EXPANDED:
                raise ValueError("Expanded ZIP exceeds the 50 MB limit.")

            inventory.append(name)
            suffix = path.suffix.lower()

            if suffix in SOURCE_EXTENSIONS:
                source_count += 1

            if info.file_size > MAX_TEXT_FILE:
                add_finding(
                    "Review", name, 0,
                    "File too large for text inspection; not scanned.",
                )
                continue

            if info.file_size > 1_000_000:
                if info.compress_size == 0:
                    raise ValueError("Suspicious ZIP compression.")

                if info.file_size / info.compress_size > 200:
                    raise ValueError("Suspicious compression ratio.")

            if suffix not in TEXT_EXTENSIONS:
                continue

            try:
                content = archive.read(info).decode("utf-8", errors="replace")
            except (OSError, RuntimeError, zipfile.BadZipFile):
                add_finding(
                    "Review", name, 0,
                    "Could not safely read this file.",
                )
                continue

            lower_content = content.lower()
            for marker in AI_MARKERS:
                if marker in lower_content:
                    ai_markers_found.add(marker)

            for line_number, line in enumerate(content.splitlines(), start=1):
                for label, pattern in SECRET_PATTERNS:
                    if pattern.search(line):
                        add_finding(
                            "High", name, line_number,
                            label + ". Verify and revoke the credential if exposed.",
                        )

                for label, pattern in RISK_PATTERNS:
                    if pattern.search(line):
                        add_finding(
                            "Review", name, line_number,
                            label + " pattern detected; human review required.",
                        )

    if not findings:
        findings.append({
            "Severity": "Info",
            "File": "",
            "Line": 0,
            "Finding": "No configured patterns detected. This does not prove the project is safe.",
        })

    return {
        "files": inventory,
        "findings": findings,
        "source_count": source_count,
        "ai_markers": sorted(ai_markers_found),
    }


# ==================================================
# SESSION DATA
# ==================================================

if "test_runs" not in st.session_state:
    st.session_state.test_runs = []

if "baseline" not in st.session_state:
    st.session_state.baseline = None

if "latest_scan" not in st.session_state:
    st.session_state.latest_scan = None


# ==================================================
# NAVIGATION
# ==================================================

st.sidebar.title("🛡️ TraceGate")
st.sidebar.caption("AI application testing workspace")

page = st.sidebar.radio(
    "WORKSPACE",
    [
        "Overview",
        "Upload & Scan",
        "Run a test",
        "Test history",
        "Regression report",
    ],
)

st.sidebar.divider()
st.sidebar.caption("Prototype version")
st.sidebar.caption("Uploaded code is never executed.")


# ==================================================
# OVERVIEW
# ==================================================

if page == "Overview":
    st.title("TraceGate")
    st.subheader("AI Application Pre-release Testing")

    st.write(
        "Inspect an AI project, record manual test results, "
        "and compare test scores before releasing an application."
    )

    st.info(
        "Start with Upload & Scan to inspect your project ZIP. "
        "Automated runtime testing is not implemented yet."
    )

    runs = st.session_state.test_runs

    col1, col2, col3 = st.columns(3)
    col1.metric("Recorded test runs", len(runs))

    if runs:
        latest = runs[-1]
        col2.metric("Latest average score", f"{latest['Average Score']:.1f}/10")
        col3.metric("Latest result", latest["Result"])
    else:
        col2.metric("Latest average score", "—")
        col3.metric("Latest result", "No tests yet")

    st.markdown("### Features")
    st.markdown(
        "- **Upload & Scan:** Inspect ZIP files for selected code patterns.\n"
        "- **Run a test:** Record and score two AI answers manually.\n"
        "- **Test history:** Review saved results in the current session.\n"
        "- **Regression report:** Compare results with the initial baseline."
    )

    st.warning(
        "This prototype is not a security certification and cannot guarantee an application is safe."
    )


# ==================================================
# UPLOAD AND SCAN
# ==================================================

elif page == "Upload & Scan":
    st.title("Upload & Scan")
    st.subheader("AI Application ZIP Inspector")

    st.write(
        "Upload a ZIP to inventory source files and detect selected "
        "patterns that may need review."
    )

    st.warning(
        "Safety notice: TraceGate does not run, install, or import uploaded project code. Do not upload confidential projects or real credentials to this prototype."
    )

    uploaded = st.file_uploader(
        "Upload your AI project (.zip)",
        type=["zip"],
        help="Maximum upload size: 20 MB.",
    )

    if uploaded is not None:
        st.caption("Selected file: " + uploaded.name)

        if st.button("Scan project", type="primary"):
            try:
                with st.spinner("Inspecting ZIP contents..."):
                    report = scan_project_zip(uploaded.getvalue())

                st.session_state.latest_scan = report
                st.success("Source inspection completed.")

            except (ValueError, OSError, RuntimeError) as error:
                st.session_state.latest_scan = None
                st.error(str(error))

    report = st.session_state.latest_scan

    if report is not None:
        st.divider()
        st.markdown("### Scan summary")

        col1, col2, col3 = st.columns(3)
        col1.metric("Files inventoried", len(report["files"]))
        col2.metric("Source files", report["source_count"])
        col3.metric("AI indicators", len(report["ai_markers"]))

        st.markdown("### AI library indicators")
        st.write(report["ai_markers"] or "No configured AI library indicators detected.")

        st.markdown("### File inventory")
        st.caption("Showing up to 100 files.")
        st.dataframe(
            pd.DataFrame({"File": report["files"][:100]}),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Findings")
        results_df = pd.DataFrame(report["findings"])

        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download scan report (CSV)",
            data=results_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="tracegate-scan-report.csv",
            mime="text/csv",
        )

        st.caption(
            "These are heuristic text-pattern checks. They can miss risks "
            "and can flag harmless code."
        )


# ==================================================
# MANUAL TESTING
# ==================================================

elif page == "Run a test":
    st.title("Run a test")

    st.info(
        "This page records a manual comparison. It does not connect to "
        "AI providers or automatically run prompts."
    )

    test_name = st.text_input("Test name", value="General quality check")
    prompt = st.text_area("Test prompt", height=120)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Model A")
        answer_a = st.text_area("Model A answer", height=180)
        quality_a = st.slider("Model A quality score", 0, 10, 5)

    with col2:
        st.markdown("### Model B")
        answer_b = st.text_area("Model B answer", height=180)
        quality_b = st.slider("Model B quality score", 0, 10, 5)

    if st.button("Save test result", type="primary"):
        if not test_name.strip():
            st.error("Please enter a test name.")
        elif not prompt.strip():
            st.error("Please enter the test prompt.")
        elif not answer_a.strip() or not answer_b.strip():
            st.error("Please enter both model answers.")
        else:
            average_score = (quality_a + quality_b) / 2

            if quality_a > quality_b:
                result = "Model A scored higher"
            elif quality_b > quality_a:
                result = "Model B scored higher"
            else:
                result = "Tie"

            run = {
                "Run ID": len(st.session_state.test_runs) + 1,
                "Date (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "Test Name": test_name.strip(),
                "Prompt": prompt.strip(),
                "Model A Answer": answer_a.strip(),
                "Model B Answer": answer_b.strip(),
                "Model A Score": quality_a,
                "Model B Score": quality_b,
                "Average Score": average_score,
                "Result": result,
            }

            st.session_state.test_runs.append(run)

            if st.session_state.baseline is None:
                st.session_state.baseline = {
                    "Test Name": run["Test Name"],
                    "Model A Score": quality_a,
                    "Model B Score": quality_b,
                    "Average Score": average_score,
                }

            st.success("Test result saved for this session.")

    if st.session_state.test_runs:
        latest = st.session_state.test_runs[-1]
        st.markdown("### Latest result")

        col1, col2, col3 = st.columns(3)
        col1.metric("Model A", f"{latest['Model A Score']}/10")
        col2.metric("Model B", f"{latest['Model B Score']}/10")
        col3.metric("Average", f"{latest['Average Score']:.1f}/10")

        st.write("**Comparison:** " + latest["Result"])


# ==================================================
# TEST HISTORY
# ==================================================

elif page == "Test history":
    st.title("Test history")
    runs = st.session_state.test_runs

    if not runs:
        st.info("No test results recorded yet. Run a test first.")
    else:
        history_df = pd.DataFrame(runs)

        columns = [
            "Run ID",
            "Date (UTC)",
            "Test Name",
            "Model A Score",
            "Model B Score",
            "Average Score",
            "Result",
        ]

        st.dataframe(
            history_df[columns],
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download test history (CSV)",
            data=history_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="tracegate-test-history.csv",
            mime="text/csv",
        )

        st.caption(
            "History is temporary and may disappear when the app session resets."
        )


# ==================================================
# REGRESSION REPORT
# ==================================================

elif page == "Regression report":
    st.title("Regression report")

    runs = st.session_state.test_runs
    baseline = st.session_state.baseline

    if not runs or baseline is None:
        st.info("Save a test result first to establish a baseline.")
    else:
        latest = runs[-1]

        comparison_df = pd.DataFrame([
            {
                "Metric": "Model A score",
                "Baseline": baseline["Model A Score"],
                "Latest": latest["Model A Score"],
            },
            {
                "Metric": "Model B score",
                "Baseline": baseline["Model B Score"],
                "Latest": latest["Model B Score"],
            },
            {
                "Metric": "Average score",
                "Baseline": baseline["Average Score"],
                "Latest": latest["Average Score"],
            },
        ])

        comparison_df["Change"] = (
            comparison_df["Latest"] - comparison_df["Baseline"]
        )

        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True,
        )

        average_change = (
            latest["Average Score"] - baseline["Average Score"]
        )

        if average_change > 0:
            st.success(f"Average score increased by {average_change:.1f} points.")
        elif average_change < 0:
            st.warning(f"Average score decreased by {abs(average_change):.1f} points.")
        else:
            st.info("Average score is unchanged from the baseline.")

        st.download_button(
            "Download regression report (CSV)",
            data=comparison_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="tracegate-regression-report.csv",
            mime="text/csv",
        )

        st.caption(
            "This compares manually entered scores; it is not an automated security test."
        )
