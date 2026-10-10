import io
import re
import stat
import zipfile
from pathlib import PurePosixPath
from datetime import datetime, timezone

import pandas as pd
import streamlit as st


# ============================================================
# TRACEGATE — AI APPLICATION PRE-RELEASE TESTING DASHBOARD
# ============================================================

st.set_page_config(
    page_title="TraceGate | AI Testing",
    page_icon="🛡️",
    layout="wide",
)

APP_NAME = "TraceGate"

# ZIP inspection limits
MAX_UPLOAD_BYTES = 20 * 1024 * 1024       # 20 MB compressed upload
MAX_FILES = 500
MAX_TOTAL_EXPANDED = 50 * 1024 * 1024     # 50 MB uncompressed
MAX_TEXT_FILE = 2 * 1024 * 1024            # 2 MB per text file

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".json", ".yaml", ".yml", ".toml",
    ".txt", ".md", ".html", ".sql",
    ".sh", ".cfg", ".ini", ".env.example",
    ".xml", ".css",
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
}

AI_MARKERS = [
    "openai",
    "anthropic",
    "google.generativeai",
    "langchain",
    "llamaindex",
    "litellm",
    "transformers",
    "ollama",
]

SECRET_PATTERNS = [
    (
        "Possible API key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    ),
    (
        "Possible GitHub token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    ),
    (
        "Private key marker",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        ),
    ),
    (
        "Possible hard-coded credential",
        re.compile(
            r"""(?i)\b(?:api_key|api-key|secret_key|password|access_token)"""
            r"""\s*[:=]\s*['"][^'"]{8,}['"]"""
        ),
    ),
]

RISK_PATTERNS = [
    (
        "Dynamic code execution",
        re.compile(r"\beval\s*\(|\bexec\s*\("),
    ),
    (
        "Shell execution",
        re.compile(
            r"\bos\.system\s*\(|\bsubprocess\.(?:run|Popen|call)\s*\("
        ),
    ),
    (
        "Deserialization",
        re.compile(r"\bpickle\.loads?\s*\("),
    ),
    (
        "Potentially unsafe YAML loading",
        re.compile(r"\byaml\.load\s*\("),
    ),
]


# ============================================================
# ZIP SCANNER
# This function inspects files. It NEVER executes uploaded code.
# ============================================================

def scan_project_zip(uploaded_bytes):
    if len(uploaded_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("ZIP exceeds the 20 MB upload limit.")

    try:
        archive = zipfile.ZipFile(io.BytesIO(uploaded_bytes))
    except (zipfile.BadZipFile, OSError):
        raise ValueError("This is not a valid ZIP archive.")

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

    with archive:
        members = archive.infolist()

        if len(members) > MAX_FILES:
            raise ValueError(
                f"ZIP contains too many entries. Limit: {MAX_FILES}."
            )

        for info in members:
            if info.is_dir():
                continue

            name = info.filename.replace("\\", "/")
            path = PurePosixPath(name)

            # Reject absolute paths and directory traversal paths.
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(
                    "Unsafe file path detected. Scan cancelled."
                )

            # Reject symbolic links.
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError(
                    "Symbolic links are not accepted. Scan cancelled."
                )

            # Reject suspicious or excessive expanded archives.
            if info.file_size < 0:
                raise ValueError("Invalid file size in ZIP archive.")

            total_expanded += info.file_size

            if total_expanded > MAX_TOTAL_EXPANDED:
                raise ValueError(
                    "Expanded ZIP exceeds the 50 MB safety limit."
                )

            inventory.append(name)
            suffix = path.suffix.lower()

            if suffix in SOURCE_EXTENSIONS:
                source_count += 1

            # Skip reading very large files, but keep them in inventory.
            if info.file_size > MAX_TEXT_FILE:
                add_finding(
                    "Review",
                    name,
                    0,
                    "File is too large for text inspection; not scanned.",
                )
                continue

            # Avoid extreme compression ratios for non-empty files.
            if info.file_size > 1_000_000:
                if info.compress_size == 0:
                    raise ValueError(
                        "Suspicious ZIP compression. Scan cancelled."
                    )

                ratio = info.file_size / info.compress_size

                if ratio > 200:
                    raise ValueError(
                        "Suspicious compression ratio. Scan cancelled."
                    )

            if suffix not in TEXT_EXTENSIONS:
                continue

            try:
                raw = archive.read(info)
                content = raw.decode("utf-8", errors="replace")
            except (OSError, RuntimeError, zipfile.BadZipFile):
                add_finding(
                    "Review",
                    name,
                    0,
                    "Could not safely read this file.",
                )
                continue

            lower_content = content.lower()

            for marker in AI_MARKERS:
                if marker in lower_content:
                    ai_markers_found.add(marker)

            for line_number, line in enumerate(
                content.splitlines(),
                start=1,
            ):
                for label, pattern in SECRET_PATTERNS:
                    if pattern.search(line):
                        add_finding(
                            "High",
                            name,
                            line_number,
                            f"{label}. Check the file and revoke exposed "
                            "credentials if confirmed.",
                        )

                for label, pattern in RISK_PATTERNS:
                    if pattern.search(line):
                        add_finding(
                            "Review",
                            name,
                            line_number,
                            f"{label} pattern detected. Human review required.",
                        )

    if not findings:
        findings.append({
            "Severity": "Info",
            "File": "",
            "Line": 0,
            "Finding": (
                "No configured patterns were detected. "
                "This does not prove the project is safe."
            ),
        })

    return {
        "files": inventory,
        "findings": findings,
        "source_count": source_count,
        "ai_markers": sorted(ai_markers_found),
    }


# ============================================================
# SESSION STATE
# Data is kept for the current app session only.
# ============================================================

if "test_runs" not in st.session_state:
    st.session_state.test_runs = []

if "baseline" not in st.session_state:
    st.session_state.baseline = None

if "latest_scan" not in st.session_state:
    st.session_state.latest_scan = None


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

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
st.sidebar.caption("Uploaded source code is not executed.")


# ============================================================
# PAGE 1 — OVERVIEW
# ============================================================

if page == "Overview":
    st.title("TraceGate")
    st.subheader("AI Application Pre-release Testing")

    st.write(
        "Inspect an AI project, record manual test results, and review "
        "changes between test runs before releasing an application."
    )

    st.info(
        "Start with Upload & Scan to inspect a ZIP project. "
        "Runtime testing is not yet implemented in this prototype."
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

    st.markdown("### Available features")

    st.markdown(
        """
        - **Upload & Scan:** Inspect a ZIP archive for selected code patterns.
        - **Run a test:** Record two answers and manually rate their quality.
        - **Test history:** Review previously recorded runs in this session.
        - **Regression report:** Compare the latest run against a baseline.
        """
    )

    st.warning(
        "This prototype is not a security certification. "
        "It cannot guarantee that an application is safe to release."
    )


# ============================================================
# PAGE 2 — UPLOAD & SCAN
# ============================================================

elif page == "Upload & Scan":
    st.title("Upload & Scan")
    st.subheader("AI Application ZIP Inspector")

    st.write(
        "Upload your source-code ZIP to inventory files and look for "
        "selected patterns that may deserve review."
    )

    st.warning(
        "Safety notice: TraceGate does not run, install, or import "
        "uploaded project code. Do not upload confidential projects or "
        "real credentials
