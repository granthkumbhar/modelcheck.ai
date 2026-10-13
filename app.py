
import io
import re
import stat
import zipfile
from pathlib import PurePosixPath
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client

# =========================================================
# TRACEGATE — PREMIUM DARK DASHBOARD
# =========================================================

st.set_page_config(
    page_title="TraceGate | AI Safety",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #061225;
    --panel: #091a31;
    --border: #164474;
    --blue: #2584ff;
    --cyan: #27d8ff;
    --purple: #8957ff;
    --green: #00d6a0;
    --orange: #ff922e;
    --text: #eef5ff;
    --muted: #9bb1cf;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(ellipse at 48% 0%, #102d50 0%, transparent 48%),
        linear-gradient(145deg, #061225 0%, #04101f 100%);
    color: var(--text);
}

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #061225, #08172b);
    border-right: 1px solid #143458;
}

[data-testid="stSidebar"] > div {
    padding-top: 1.3rem;
}

h1, h2, h3, p, label {
    color: var(--text);
}

h1 {
    font-weight: 800 !important;
    letter-spacing: -1.2px;
}

p, li, label {
    color: #c5d6ed;
}

.tg-brand {
    font-size: 27px;
    font-weight: 800;
    letter-spacing: -1px;
    color: white;
    margin-bottom: 0;
}

.tg-tagline {
    color: #8faed3;
    font-size: 12px;
    margin-bottom: 20px;
}

.tg-hero {
    background:
        radial-gradient(circle at 82% 40%, #193f78 0%, transparent 27%),
        linear-gradient(115deg, #07152b, #0a2344 65%, #111b43);
    border: 1px solid #1464a8;
    border-radius: 18px;
    padding: 30px 30px;
    margin-bottom: 18px;
    box-shadow: 0 0 30px #087bff0c;
}

.tg-hero h1 {
    font-size: clamp(32px, 4vw, 48px);
    margin: 0 0 5px 0;
}

.tg-gradient {
    background: linear-gradient(90deg, #ffffff, #61c5ff, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.tg-subtitle {
    color: #b9d9fa;
    font-size: 18px;
    font-weight: 600;
}

.tg-description {
    color: #a9c0df;
    max-width: 650px;
    line-height: 1.7;
}

.tg-shield {
    font-size: 70px;
    text-align: center;
    filter: drop-shadow(0 0 20px #2584ff70);
}

.tg-card {
    background: linear-gradient(145deg, #0c203b, #07162a);
    border: 1px solid #19436b;
    border-radius: 15px;
    padding: 19px;
    margin-bottom: 14px;
    min-height: 115px;
}

.tg-card.blue { border-color: #1768ba; }
.tg-card.green { border-color: #008d80; background: linear-gradient(145deg,#082c35,#07182a); }
.tg-card.purple { border-color: #6240b5; background: linear-gradient(145deg,#19183e,#0b1730); }
.tg-card.orange { border-color: #9b5423; }

.tg-label {
    font-size: 12px;
    color: #a9bfdc;
    margin-bottom: 8px;
}

.tg-number {
    font-size: 29px;
    line-height: 1.25;
    font-weight: 800;
    color: #ffffff;
}

.tg-small {
    color: #8ea8ca;
    font-size: 12px;
    margin-top: 8px;
}

.tg-panel {
    background: linear-gradient(150deg, #081a30, #071529);
    border: 1px solid #16436e;
    border-radius: 16px;
    padding: 21px;
    margin: 8px 0 17px 0;
}

.tg-panel-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 3px;
}

.tg-panel-sub {
    color: #91aacb;
    font-size: 12px;
    margin-bottom: 17px;
}

.tg-action {
    background: linear-gradient(150deg, #0d2548, #08182d);
    border: 1px solid #20558a;
    border-radius: 13px;
    padding: 17px;
    min-height: 165px;
}

.tg-action-icon {
    font-size: 28px;
    margin-bottom: 8px;
}

.tg-action-title {
    color: #f4f8ff;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 7px;
}

.tg-action-desc {
    color: #a9bfdc;
    font-size: 12px;
    line-height: 1.6;
}

.tg-pill {
    display: inline-block;
    border: 1px solid #087e75;
    color: #52f2c2;
    background: #06362f;
    border-radius: 30px;
    padding: 5px 10px;
    font-size: 11px;
}

.tg-row {
    background: #091b30;
    border: 1px solid #183b60;
    border-radius: 10px;
    padding: 12px;
    margin: 7px 0;
}

.tg-muted {
    color: #92a9c9;
    font-size: 12px;
}

.tg-footer {
    text-align: center;
    padding: 24px 8px;
    color: #8ca7c8;
    font-size: 12px;
}

div.stButton > button {
    border: 1px solid #2866a9;
    background: linear-gradient(100deg, #1469ec, #4b48ec);
    color: white;
    border-radius: 9px;
    font-weight: 600;
    min-height: 42px;
    transition: all 0.2s ease;
}

div.stButton > button:hover {
    border-color: #69c8ff;
    color: white;
    box-shadow: 0 0 18px #248bff35;
}

div[data-testid="stDownloadButton"] button {
    border-radius: 9px;
}

input, textarea {
    background-color: #07172b !important;
    color: white !important;
}

[data-testid="stFileUploader"] {
    background: #07172b;
    border: 1px dashed #2584ff;
    border-radius: 12px;
    padding: 12px;
}

[data-testid="stMetric"] {
    background: #0a1b30;
    border: 1px solid #19436b;
    padding: 13px;
    border-radius: 12px;
}

[data-testid="stDataFrame"] {
    border: 1px solid #183c61;
    border-radius: 10px;
}

hr {
    border-color: #183858;
}

.stAlert {
    border-radius: 10px;
}

@media (max-width: 768px) {
    .tg-hero { padding: 20px; }
    .tg-panel { padding: 14px; }
}

/* Pricing page — matched to TraceGate's existing dark navy/blue theme */
.tg-pricing-hero {
    text-align: center;
    padding: 18px 8px 24px;
}
.tg-pricing-kicker {
    display: inline-block;
    color: #52f2e0;
    background: #06362f;
    border: 1px solid #087e75;
    border-radius: 30px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}
.tg-pricing-hero h1 {
    margin: 14px 0 8px;
}
.tg-pricing-hero p {
    color: #a9c0df;
    max-width: 760px;
    margin: 0 auto;
}
.tg-plan {
    background: linear-gradient(145deg, #0c203b, #07162a);
    border: 1px solid #19436b;
    border-radius: 16px;
    padding: 22px;
    min-height: 410px;
    margin-bottom: 12px;
}
.tg-plan.featured {
    border: 2px solid #27d8ff;
    background: linear-gradient(145deg, #0b2941, #07182a);
    box-shadow: 0 0 24px #27d8ff12;
}
.tg-plan-title {
    color: #eef5ff;
    font-size: 22px;
    font-weight: 800;
}
.tg-plan-desc {
    color: #9bb1cf;
    font-size: 13px;
    min-height: 38px;
    margin-top: 6px;
}
.tg-plan-price {
    color: #ffffff;
    font-size: 34px;
    font-weight: 800;
    margin: 18px 0 0;
}
.tg-plan-period {
    color: #9bb1cf;
    font-size: 13px;
    font-weight: 500;
}
.tg-plan-feature {
    color: #c5d6ed;
    font-size: 13px;
    margin: 10px 0;
}
.tg-plan-check {
    color: #27d8ff;
    font-weight: 800;
    margin-right: 8px;
}
.tg-plan-badge {
    color: #52f2c2;
    background: #06362f;
    border: 1px solid #087e75;
    border-radius: 30px;
    display: inline-block;
    padding: 4px 9px;
    font-size: 10px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# ZIP SCANNER — DOES NOT EXECUTE UPLOADED CODE
# =========================================================

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
        re.compile(
            r"""(?i)\b(?:api_key|api-key|secret_key|password|access_token)\s*[:=]\s*['"][^'"]{8,}['"]"""
        ),
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
    ai_found = set()
    source_count = 0
    total_expanded = 0

    def add_finding(severity, file_name, line, message):
        findings.append({
            "Severity": severity,
            "File": file_name,
            "Line": line,
            "Finding": message,
        })

    try:
        archive = zipfile.ZipFile(io.BytesIO(uploaded_bytes))
    except (zipfile.BadZipFile, OSError):
        raise ValueError("Invalid ZIP archive.")

    with archive:
        members = archive.infolist()

        if len(members) > MAX_FILES:
            raise ValueError("Too many files in ZIP. Maximum: 500.")

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
                add_finding("Review", name, 0, "Could not read this file.")
                continue

            lower_content = content.lower()

            for marker in AI_MARKERS:
                if marker in lower_content:
                    ai_found.add(marker)

            for line_no, line in enumerate(content.splitlines(), 1):
                for label, pattern in SECRET_PATTERNS:
                    if pattern.search(line):
                        add_finding(
                            "High", name, line_no,
                            label + ". Verify and revoke if a real credential is exposed.",
                        )

                for label, pattern in RISK_PATTERNS:
                    if pattern.search(line):
                        add_finding(
                            "Review", name, line_no,
                            label + " pattern detected; review the code.",
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
        "ai_markers": sorted(ai_found),
    }


# =========================================================
# SESSION STATE
# =========================================================

for key, default in {
    "test_runs": [],
    "baseline": None,
    "latest_scan": None,
    "page": "Overview",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def go_to(page_name):
    st.session_state.page = page_name


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown(
        '<div class="tg-brand">🛡️ TraceGate</div>'
        '<div class="tg-tagline">AI Safety. Before You Ship.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="tg-muted">WORKSPACE</div>', unsafe_allow_html=True)

    st.radio(
        "Navigation",
        [
            "Overview",
            "Upload & Scan",
            "Run a Test",
            "Test History",
            "Regression Report",
            "Pricing",
        ],
        key="page",
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown(
        """
        <div class="tg-row">
        🔒 <b>Privacy first</b><br>
        <span class="tg-muted">Uploaded code is never executed.</span>
        </div>
        <div class="tg-row">
        <span class="tg-pill">● Prototype v1.0</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


page = st.session_state.page


# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":
    runs = st.session_state.test_runs
    latest = runs[-1] if runs else None
    scan = st.session_state.latest_scan

    st.markdown(
        """
        <div class="tg-hero">
          <div class="tg-shield">🛡️</div>
          <h1><span class="tg-gradient">TraceGate</span></h1>
          <div class="tg-subtitle">AI Application Pre-release Testing</div>
          <p class="tg-description">
            Inspect your AI project, identify potential risks, and track
            test results before release. Build safer, more reliable AI.
          </p>
          <span class="tg-pill">SCAN &nbsp; ● &nbsp; TEST &nbsp; ● &nbsp; REPORT</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    a, b, c = st.columns(3)

    with a:
        st.markdown(
            f"""
            <div class="tg-card blue">
              <div class="tg-label">RECORDED TEST RUNS</div>
              <div class="tg-number">{len(runs)}</div>
              <div class="tg-small">Manual comparisons saved this session</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with b:
        score = f"{latest['Average Score']:.1f}/10" if latest else "—"
        st.markdown(
            f"""
            <div class="tg-card green">
              <div class="tg-label">LATEST AVERAGE SCORE</div>
              <div class="tg-number">{score}</div>
              <div class="tg-small">Based on manually entered ratings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c:
        result = latest["Result"] if latest else "No tests yet"
        st.markdown(
            f"""
            <div class="tg-card purple">
              <div class="tg-label">LATEST TEST RESULT</div>
              <div style="font-size:17px;font-weight:700;margin-top:10px">{result}</div>
              <div class="tg-small">Not an automated release decision</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="tg-panel">'
        '<div class="tg-panel-title">⚡ Quick Actions</div>'
        '<div class="tg-panel-sub">Jump into the tools you need.</div>',
        unsafe_allow_html=True,
    )

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        st.markdown(
            '<div class="tg-action"><div class="tg-action-icon">📤</div>'
            '<div class="tg-action-title">Upload & Scan</div>'
            '<div class="tg-action-desc">Inspect your project ZIP for selected risk patterns.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Start Scan →", key="quick_scan", use_container_width=True):
            go_to("Upload & Scan")
            st.rerun()

    with q2:
        st.markdown(
            '<div class="tg-action"><div class="tg-action-icon">▶️</div>'
            '<div class="tg-action-title">Run a Test</div>'
            '<div class="tg-action-desc">Compare two AI answers and rate quality.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Run Test →", key="quick_test", use_container_width=True):
            go_to("Run a Test")
            st.rerun()

    with q3:
        st.markdown(
            '<div class="tg-action"><div class="tg-action-icon">📋</div>'
            '<div class="tg-action-title">Test History</div>'
            '<div class="tg-action-desc">Review your recorded test results.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("View History →", key="quick_history", use_container_width=True):
            go_to("Test History")
            st.rerun()

    with q4:
        st.markdown(
            '<div class="tg-action"><div class="tg-action-icon">📊</div>'
            '<div class="tg-action-title">Regression Report</div>'
            '<div class="tg-action-desc">Compare the latest scores with baseline.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("View Report →", key="quick_report", use_container_width=True):
            go_to("Regression Report")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="tg-panel">'
        '<div class="tg-panel-title">🕘 Recent Activity</div>'
        '<div class="tg-panel-sub">Your latest scan and test runs.</div>',
        unsafe_allow_html=True,
    )

    if scan:
        st.markdown(
            f'<div class="tg-row">📦 <b>Project scan</b>'
            f'<span style="float:right" class="tg-pill">Completed</span><br>'
            f'<span class="tg-muted">{len(scan["files"])} files inventoried · '
            f'{len(scan["findings"])} findings recorded</span></div>',
            unsafe_allow_html=True,
        )

    if runs:
        for item in reversed(runs[-5:]):
            st.markdown(
                f'<div class="tg-row">🧪 <b>{item["Test Name"]}</b>'
                f'<span style="float:right" class="tg-pill">Saved</span><br>'
                f'<span class="tg-muted">Average: {item["Average Score"]:.1f}/10 · '
                f'{item["Date (UTC)"]} UTC</span></div>',
                unsafe_allow_html=True,
            )
    elif not scan:
        st.caption("No activity yet. Start by scanning a ZIP project.")

    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1.3, 1])

    with left:
        st.markdown(
            """
            <div class="tg-panel">
            <div class="tg-panel-title">🛡️ Security approach</div>
            <p class="tg-muted">
            TraceGate currently performs static source inspection.
            It does not execute uploaded files, and it does not yet
            provide an isolated runtime environment.
            </p>
            <span class="tg-pill">Static inspection prototype</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="tg-panel">
            <div class="tg-panel-title">🤖 AI indicators</div>
            <div class="tg-muted">Library names found in the latest scan</div>
            """,
            unsafe_allow_html=True,
        )

        if scan and scan["ai_markers"]:
            for marker in scan["ai_markers"]:
                st.markdown(f"- `{marker}`")
        else:
            st.caption("No AI library indicators available yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="tg-footer">Better testing today. Safer AI tomorrow.<br>'
        'TraceGate Prototype · Built for safer AI releases</div>',
        unsafe_allow_html=True,
    )


# =========================================================
# UPLOAD & SCAN
# =========================================================

elif page == "Upload & Scan":
    st.title("📤 Upload & Scan")
    st.caption("Inspect a ZIP archive for selected source-code patterns.")

    st.caption(
    "🔒 Static scan mode · Uploaded code is inspected, never executed."
)

    uploaded = st.file_uploader(
        "Choose your AI project ZIP",
        type=["zip"],
        help="Maximum compressed upload size: 20 MB.",
    )

    if uploaded is not None:
        st.caption(f"Selected: {uploaded.name}")

        if st.button("🛡️ Scan Project", type="primary"):
            try:
                with st.spinner("Inspecting project files..."):
                    report = scan_project_zip(uploaded.getvalue())

                st.session_state.latest_scan = report
                st.success("Inspection completed.")

            except (ValueError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
                st.session_state.latest_scan = None
                st.error(str(exc))

    report = st.session_state.latest_scan

    if report:
        st.markdown("### Scan summary")

        x, y, z = st.columns(3)
        x.metric("Files inventoried", len(report["files"]))
        y.metric("Source files", report["source_count"])
        z.metric("AI indicators", len(report["ai_markers"]))

        st.markdown("### AI library indicators")
        st.write(", ".join(report["ai_markers"]) if report["ai_markers"] else "None detected.")

        st.markdown("### Project inventory")
        st.dataframe(
            pd.DataFrame({"File": report["files"][:100]}),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Findings")
        df = pd.DataFrame(report["findings"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Download scan report",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="tracegate-scan-report.csv",
            mime="text/csv",
        )

        st.caption(
            "Pattern matching may produce false positives and miss risks. "
            "A clean report does not establish that code is safe."
        )


# =========================================================
# RUN A TEST
# =========================================================

elif page == "Run a Test":
    st.title("🧪 Run a Test")
    st.caption("Manually compare two model answers.")

    st.info("This page does not connect to AI models or run prompts automatically.")

    test_name = st.text_input("Test name", value="General quality check")
    prompt = st.text_area("Test prompt", placeholder="Enter the prompt...", height=110)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 🔵 Model A")
        answer_a = st.text_area("Model A answer", height=170)
        score_a = st.slider("Model A quality score", 0, 10, 5)

    with c2:
        st.markdown("### 🟣 Model B")
        answer_b = st.text_area("Model B answer", height=170)
        score_b = st.slider("Model B quality score", 0, 10, 5)

    if st.button("Save Test Result", type="primary"):
        if not test_name.strip() or not prompt.strip():
            st.error("Enter both a test name and prompt.")
        elif not answer_a.strip() or not answer_b.strip():
            st.error("Enter both model answers.")
        else:
            avg = (score_a + score_b) / 2

            if score_a > score_b:
                result = "Model A scored higher"
            elif score_b > score_a:
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
                "Model A Score": score_a,
                "Model B Score": score_b,
                "Average Score": avg,
                "Result": result,
            }

            st.session_state.test_runs.append(run)

            if st.session_state.baseline is None:
                st.session_state.baseline = {
                    "Model A Score": score_a,
                    "Model B Score": score_b,
                    "Average Score": avg,
                }

            st.success("Test result saved for this session.")

            m1, m2, m3 = st.columns(3)
            m1.metric("Model A", f"{score_a}/10")
            m2.metric("Model B", f"{score_b}/10")
            m3.metric("Average", f"{avg:.1f}/10")

            st.write(result)


# =========================================================
# TEST HISTORY
# =========================================================

elif page == "Test History":
    st.title("📋 Test History")

    runs = st.session_state.test_runs

    if not runs:
        st.info("No test results yet. Open Run a Test to add one.")
    else:
        df = pd.DataFrame(runs)

        st.dataframe(
            df[
                [
                    "Run ID", "Date (UTC)", "Test Name",
                    "Model A Score", "Model B Score",
                    "Average Score", "Result",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Export test history",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="tracegate-test-history.csv",
            mime="text/csv",
        )

        st.caption("History is temporary and may disappear when the app session resets.")


# =========================================================
# REGRESSION REPORT
# =========================================================

elif page == "Regression Report":
    st.title("📊 Regression Report")
    st.caption("Compare the latest manually entered scores with the first saved run.")

    runs = st.session_state.test_runs
    baseline = st.session_state.baseline

    if not runs or baseline is None:
        st.info("Save a test result first to establish a baseline.")
    else:
        latest = runs[-1]

        df = pd.DataFrame([
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

        df["Change"] = df["Latest"] - df["Baseline"]

        st.dataframe(df, use_container_width=True, hide_index=True)

        change = latest["Average Score"] - baseline["Average Score"]

        if change > 0:
            st.success(f"Average score increased by {change:.1f} points.")
        elif change < 0:
            st.warning(f"Average score decreased by {abs(change):.1f} points.")
        else:
            st.info("Average score is unchanged from baseline.")

        st.download_button(
            "⬇️ Download regression report",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="tracegate-regression-report.csv",
            mime="text/csv",
        )

        st.caption(
            "This compares manually entered scores; it is not an automated "
            "regression test or release approval."
        )

# =========================================================
# PRICING — HONEST EARLY-ACCESS TIERS
# =========================================================

elif page == "Pricing":
    st.markdown(
        """
        <div class="tg-pricing-hero">
          <span class="tg-pricing-kicker">TRACEGATE PRICING</span>
          <h1>Simple pricing for <span class="tg-gradient">AI testing</span></h1>
          <p>
            Start free, validate your workflow, and upgrade only when the paid
            features you need are available. Checkout is not enabled yet.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Early-access pricing proposal. Payments, accounts, per-customer usage "
        "limits, and subscription enforcement are not connected in this prototype. "
        "Do not treat a button click as a purchase."
    )

    plans = [
        {
            "name": "Starter",
            "desc": "Try the current TraceGate prototype",
            "price": "₹0",
            "period": "forever",
            "badge": "AVAILABLE NOW",
            "features": [
                "ZIP source-pattern scan (20 MB upload cap)",
                "Selected secret and risky-code pattern checks",
                "Manual comparison of two AI answers",
                "Session-only test history and baseline",
                "CSV export for available reports",
            ],
            "cta": "Use free plan",
            "featured": False,
            "status": "available",
        },
        {
            "name": "Pro",
            "desc": "For developers testing projects regularly",
            "price": "₹299",
            "period": "/month · proposed",
            "badge": "EARLY-ACCESS PRICE",
            "features": [
                "Everything in Starter",
                "Persistent scan and test history",
                "Saved projects and named baselines",
                "Repeatable test suites and regression comparisons",
                "Downloadable report bundle (CSV/PDF)",
                "Higher usage limits per authenticated account",
            ],
            "cta": "Join Pro waitlist",
            "featured": True,
            "status": "planned",
        },
        {
            "name": "Team",
            "desc": "For small AI agencies and product teams",
            "price": "₹999",
            "period": "/month · proposed",
            "badge": "COMING SOON",
            "features": [
                "Everything planned for Pro",
                "Multiple team members and roles",
                "Shared projects, reports, and baselines",
                "Team usage and audit trail",
                "Centralized billing and workspace controls",
                "Priority support after launch",
            ],
            "cta": "Register interest",
            "featured": False,
            "status": "planned",
        },
    ]

    cols = st.columns(3, gap="medium")
    for col, plan in zip(cols, plans):
        with col:
            badge_html = '<div class="tg-plan-badge">' + plan["badge"] + '</div><br>'
            feature_html = "".join(
                '<div class="tg-plan-feature"><span class="tg-plan-check">✓</span>'
                + feature + '</div>' for feature in plan["features"]
            )
            featured_class = "featured" if plan["featured"] else ""
            card_html = (
                f'<div class="tg-plan {featured_class}">'
                + badge_html
                + f'<div class="tg-plan-title">{plan["name"]}</div>'
                + f'<div class="tg-plan-desc">{plan["desc"]}</div>'
                + f'<div class="tg-plan-price">{plan["price"]}<span class="tg-plan-period"> {plan["period"]}</span></div>'
                + '<hr>' + feature_html + '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button(
                plan["cta"],
                key="pricing_" + plan["name"],
                use_container_width=True,
                type="primary" if plan["featured"] else "secondary",
            ):
                if plan["status"] == "available":
                    st.session_state.page = "Overview"
                    st.rerun()
                else:
                    st.session_state["show_pricing_interest"] = plan["name"]

    if st.session_state.get("show_pricing_interest"):
        selected_plan = st.session_state["show_pricing_interest"]
        st.markdown(f"### Register interest in {selected_plan}")
        st.caption(
            "This prototype cannot send your enquiry yet. The form below prepares "
            "your details locally; connect a secure backend/email service before launch."
        )
        with st.form("tracegate_interest_form"):
            interest_name = st.text_input("Name")
            interest_email = st.text_input("Email")
            interest_use = st.text_area("What would you use TraceGate for?")
            interest_submit = st.form_submit_button("Validate details")
        if interest_submit:
            if not interest_name.strip() or "@" not in interest_email or not interest_use.strip():
                st.error("Enter your name, a valid email address, and how you plan to use TraceGate.")
            else:
                st.session_state["pricing_interest_draft"] = {
                    "plan": selected_plan,
                    "name": interest_name.strip(),
                    "email": interest_email.strip(),
                    "use_case": interest_use.strip(),
                }
                st.success("Details validated in this session only; no message was sent.")
                st.json(st.session_state["pricing_interest_draft"])

    st.markdown("### Feature availability")
    feature_status = pd.DataFrame([
        {"Feature": "ZIP static scan", "Status": "Available", "Notes": "Pattern-based; can miss issues or flag false positives."},
        {"Feature": "Manual answer comparison", "Status": "Available", "Notes": "User enters both answers and scores manually."},
        {"Feature": "CSV report export", "Status": "Available", "Notes": "Exports the report/history currently in the session."},
        {"Feature": "Persistent history across sessions", "Status": "Not implemented", "Notes": "Requires authenticated, durable storage."},
        {"Feature": "Automated prompt/model execution", "Status": "Not implemented", "Notes": "Current app does not call AI models."},
        {"Feature": "Payments and subscription enforcement", "Status": "Not implemented", "Notes": "Requires payment verification and account-level plan limits."},
        {"Feature": "Team accounts and shared workspaces", "Status": "Not implemented", "Notes": "Requires authentication, roles, and workspace isolation."},
    ])
    st.dataframe(feature_status, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <div class="tg-panel">
          <div class="tg-panel-title">Why TraceGate?</div>
          <div class="tg-panel-sub">A developer-focused starting point for inspecting AI projects, recording manual tests, and reviewing evidence before release.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("### 🛡️ Inspect")
        st.caption("Uploaded code is inspected as text; it is not executed.")
    with f2:
        st.markdown("### 🧪 Compare")
        st.caption("Record manually entered answers and quality scores.")
    with f3:
        st.markdown("### 📊 Report")
        st.caption("Export currently available findings and test history.")

    st.caption(
        "Prices are proposed for early validation, not active subscriptions. "
        "Before accepting payment, implement secure authentication, durable customer-isolated "
        "storage, per-account limits, payment verification, privacy/retention controls, "
        "and support/refund terms."
    )
