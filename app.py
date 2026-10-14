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
# TRACEGATE CONFIG
# =========================================================

st.set_page_config(
    page_title="TraceGate | AI Safety",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# SUPABASE
# =========================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
)


# =========================================================
# PLAN CONFIGURATION
# =========================================================

PLANS = {
    "Starter": {
        "price": 0,
        "scan_limit": 3,
        "test_limit": 10,
        "description": "For trying TraceGate",
    },
    "Pro": {
        "price": 299,
        "scan_limit": 50,
        "test_limit": 200,
        "description": "For developers testing regularly",
    },
    "Team": {
        "price": 999,
        "scan_limit": 200,
        "test_limit": 1000,
        "description": "For teams and agencies",
    },
}


# =========================================================
# DARK TRACEGATE DESIGN
# =========================================================

st.markdown(
    """
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
        radial-gradient(
            ellipse at 48% 0%,
            #102d50 0%,
            transparent 48%
        ),
        linear-gradient(
            145deg,
            #061225 0%,
            #04101f 100%
        );

    color: var(--text);
}

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #061225,
            #08172b
        );

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
}

.tg-tagline {
    color: #8faed3;
    font-size: 12px;
    margin-bottom: 20px;
}

.tg-hero {
    background:
        radial-gradient(
            circle at 82% 40%,
            #193f78 0%,
            transparent 27%
        ),
        linear-gradient(
            115deg,
            #07152b,
            #0a2344 65%,
            #111b43
        );

    border: 1px solid #1464a8;
    border-radius: 18px;
    padding: 30px;
    margin-bottom: 18px;
}

.tg-hero h1 {
    font-size: clamp(32px, 4vw, 48px);
    margin: 0 0 5px 0;
}

.tg-gradient {
    background:
        linear-gradient(
            90deg,
            #ffffff,
            #61c5ff,
            #a78bfa
        );

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
}

.tg-card {
    background:
        linear-gradient(
            145deg,
            #0c203b,
            #07162a
        );

    border: 1px solid #19436b;
    border-radius: 15px;
    padding: 19px;
    margin-bottom: 14px;
    min-height: 115px;
}

.tg-card.blue {
    border-color: #1768ba;
}

.tg-card.green {
    border-color: #008d80;
    background:
        linear-gradient(
            145deg,
            #082c35,
            #07182a
        );
}

.tg-card.purple {
    border-color: #6240b5;
    background:
        linear-gradient(
            145deg,
            #19183e,
            #0b1730
        );
}

.tg-label {
    font-size: 12px;
    color: #a9bfdc;
    margin-bottom: 8px;
}

.tg-number {
    font-size: 29px;
    line-height: 1.25;
    font-weight: 800;
    color: white;
}

.tg-small {
    color: #8ea8ca;
    font-size: 12px;
    margin-top: 8px;
}

.tg-panel {
    background:
        linear-gradient(
            150deg,
            #081a30,
            #071529
        );

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
    background:
        linear-gradient(
            150deg,
            #0d2548,
            #08182d
        );

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

.tg-plan {
    background:
        linear-gradient(
            145deg,
            #0c203b,
            #07162a
        );

    border: 1px solid #19436b;
    border-radius: 16px;
    padding: 22px;
    min-height: 390px;
}

.tg-plan.featured {
    border: 2px solid #27d8ff;
    background:
        linear-gradient(
            145deg,
            #0b2941,
            #07182a
        );
}

.tg-plan-title {
    color: #eef5ff;
    font-size: 22px;
    font-weight: 800;
}

.tg-plan-price {
    color: white;
    font-size: 34px;
    font-weight: 800;
    margin: 18px 0;
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

input,
textarea {
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

div.stButton > button {
    border: 1px solid #2866a9;
    background:
        linear-gradient(
            100deg,
            #1469ec,
            #4b48ec
        );

    color: white;
    border-radius: 9px;
    font-weight: 600;
    min-height: 42px;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "user": None,
    "profile": None,
    "page": "Overview",
    "latest_scan": None,
    "test_runs": [],
    "baseline": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# AUTH HELPERS
# =========================================================

def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state["user"] = None
    st.session_state["profile"] = None
    st.session_state["test_runs"] = []
    st.session_state["latest_scan"] = None
    st.session_state["baseline"] = None
    st.rerun()


def create_or_load_profile(user):
    """
    Creates a Starter profile if the user does not have one.

    Paid plans are NEVER assigned here.
    """

    user_id = str(user.id)

    try:
        result = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

        # New users always start as Starter.
        new_profile = {
            "id": user_id,
            "plan": "Starter",
            "payment_status": "none",
        }

        inserted = (
            supabase
            .table("profiles")
            .insert(new_profile)
            .execute()
        )

        if inserted.data:
            return inserted.data[0]

    except Exception:
        pass

    return {
        "id": user_id,
        "plan": "Starter",
        "payment_status": "none",
    }


def get_effective_plan(profile):
    """
    Security rule:

    Starter is the default.

    Pro/Team are active ONLY when payment_status is verified.
    """

    if not profile:
        return "Starter"

    requested_plan = profile.get("plan", "Starter")
    payment_status = profile.get("payment_status", "none")

    if requested_plan in ("Pro", "Team") and payment_status == "verified":
        return requested_plan

    return "Starter"


def get_user_id():
    user = st.session_state.get("user")

    if not user:
        return None

    return str(user.id)


def get_usage_count(table_name):
    """
    Counts this user's records.

    RLS ensures the authenticated user can only see
    their own records.
    """

    user_id = get_user_id()

    if not user_id:
        return 0

    try:
        result = (
            supabase
            .table(table_name)
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )

        return result.count or 0

    except Exception:
        return 0


def can_use(feature):
    profile = st.session_state.get("profile")
    plan = get_effective_plan(profile)

    limit_key = {
        "scan": "scan_limit",
        "test": "test_limit",
    }[feature]

    table_key = {
        "scan": "scan_runs",
        "test": "test_runs",
    }[feature]

    limit = PLANS[plan][limit_key]
    current = get_usage_count(table_key)

    if current >= limit:
        st.error(
            f"Your {plan} plan has reached its {feature} limit "
            f"({limit} per month)."
        )

        if plan == "Starter":
            st.info(
                "Upgrade to Pro when verified payments are enabled."
            )

        return False

    return True


# =========================================================
# LOGIN PAGE
# =========================================================

if st.session_state["user"] is None:

    st.markdown(
        """
        <div class="tg-hero">
            <div class="tg-shield">🛡️</div>
            <h1>
                <span class="tg-gradient">TraceGate</span>
            </h1>
            <div class="tg-subtitle">
                AI Application Pre-release Testing
            </div>
            <p class="tg-description">
                Sign in to scan projects, run tests, and keep
                your TraceGate history connected to your account.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, signup_tab = st.tabs(
        ["🔐 Login", "✨ Create account"]
    )

    with login_tab:

        email = st.text_input(
            "Email",
            key="login_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
        ):

            if not email.strip() or not password:
                st.error("Enter your email and password.")

            else:
                try:
                    response = supabase.auth.sign_in_with_password(
                        {
                            "email": email.strip(),
                            "password": password,
                        }
                    )

                    if response.user:

                        st.session_state["user"] = response.user

                        profile = create_or_load_profile(
                            response.user
                        )

                        st.session_state["profile"] = profile

                        st.success("Login successful.")

                        st.rerun()

                except Exception:
                    st.error(
                        "Login failed. Check your email and password."
                    )

    with signup_tab:

        new_email = st.text_input(
            "Email",
            key="signup_email",
        )

        new_password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="signup_confirm",
        )

        if st.button(
            "Create account",
            type="primary",
            use_container_width=True,
        ):

            if not new_email.strip():
                st.error("Enter your email.")

            elif len(new_password) < 8:
                st.error(
                    "Password must contain at least 8 characters."
                )

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            else:
                try:

                    response = supabase.auth.sign_up(
                        {
                            "email": new_email.strip(),
                            "password": new_password,
                        }
                    )

                    if response.user:

                        # If email confirmation is disabled,
                        # the user may already have a session.
                        if response.session:

                            st.session_state["user"] = response.user

                            profile = create_or_load_profile(
                                response.user
                            )

                            st.session_state["profile"] = profile

                            st.success(
                                "Account created successfully."
                            )

                            st.rerun()

                        else:

                            st.success(
                                "Account created. Check your email "
                                "to confirm your account, then log in."
                            )

                except Exception as exc:

                    st.error(
                        "Could not create the account."
                    )

    st.stop()


# =========================================================
# LOAD USER PROFILE
# =========================================================

user = st.session_state["user"]

if st.session_state["profile"] is None:
    st.session_state["profile"] = create_or_load_profile(user)

profile = st.session_state["profile"]

effective_plan = get_effective_plan(profile)

scan_limit = PLANS[effective_plan]["scan_limit"]
test_limit = PLANS[effective_plan]["test_limit"]

scan_usage = get_usage_count("scan_runs")
test_usage = get_usage_count("test_runs")


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="tg-brand">🛡️ TraceGate</div>'
        '<div class="tg-tagline">AI Safety. Before You Ship.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="tg-muted">ACCOUNT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="tg-row">
            👤 <b>{user.email}</b><br>
            <span class="tg-muted">
                User ID: {str(user.id)[:8]}...
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="tg-row">
            💳 <b>{effective_plan} Plan</b><br>
            <span class="tg-muted">
                Scans: {scan_usage}/{scan_limit}<br>
                Tests: {test_usage}/{test_limit}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🚪 Logout",
        use_container_width=True,
    ):
        logout()

    st.divider()

    st.markdown(
        '<div class="tg-muted">WORKSPACE</div>',
        unsafe_allow_html=True,
    )

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
            <span class="tg-muted">
                Uploaded code is never executed.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


page = st.session_state["page"]


# =========================================================
# ZIP SCANNER
# =========================================================

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_FILES = 500
MAX_TOTAL_EXPANDED = 50 * 1024 * 1024
MAX_TEXT_FILE = 2 * 1024 * 1024

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".md",
    ".html",
    ".sql",
    ".sh",
    ".cfg",
    ".ini",
    ".xml",
    ".css",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
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
            r"""(?i)\b(?:api_key|api-key|secret_key|password|access_token)\s*[:=]\s*['"][^'"]{8,}['"]"""
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


def scan_project_zip(uploaded_bytes):

    if len(uploaded_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(
            "ZIP exceeds the 20 MB upload limit."
        )

    findings = []
    inventory = []
    ai_found = set()
    source_count = 0
    total_expanded = 0

    def add_finding(
        severity,
        file_name,
        line,
        message,
    ):

        findings.append(
            {
                "Severity": severity,
                "File": file_name,
                "Line": line,
                "Finding": message,
            }
        )

    try:

        archive = zipfile.ZipFile(
            io.BytesIO(uploaded_bytes)
        )

    except (
        zipfile.BadZipFile,
        OSError,
    ):

        raise ValueError(
            "Invalid ZIP archive."
        )

    with archive:

        members = archive.infolist()

        if len(members) > MAX_FILES:
            raise ValueError(
                "Too many files in ZIP. Maximum: 500."
            )

        for info in members:

            if info.is_dir():
                continue

            name = info.filename.replace(
                "\\",
                "/",
            )

            path = PurePosixPath(name)

            if (
                path.is_absolute()
                or ".." in path.parts
            ):
                raise ValueError(
                    "Unsafe file path detected. "
                    "Scan cancelled."
                )

            mode = (
                info.external_attr >> 16
            ) & 0o170000

            if mode == stat.S_IFLNK:
                raise ValueError(
                    "Symbolic links are not accepted."
                )

            total_expanded += info.file_size

            if total_expanded > MAX_TOTAL_EXPANDED:
                raise ValueError(
                    "Expanded ZIP exceeds the 50 MB limit."
                )

            inventory.append(name)

            suffix = path.suffix.lower()

            if suffix in SOURCE_EXTENSIONS:
                source_count += 1

            if info.file_size > MAX_TEXT_FILE:

                add_finding(
                    "Review",
                    name,
                    0,
                    "File too large for text inspection; "
                    "not scanned.",
                )

                continue

            if info.file_size > 1_000_000:

                if info.compress_size == 0:
                    raise ValueError(
                        "Suspicious ZIP compression."
                    )

                if (
                    info.file_size
                    / info.compress_size
                    > 200
                ):
                    raise ValueError(
                        "Suspicious compression ratio."
                    )

            if suffix not in TEXT_EXTENSIONS:
                continue

            try:

                content = archive.read(
                    info
                ).decode(
                    "utf-8",
                    errors="replace",
                )

            except (
                OSError,
                RuntimeError,
                zipfile.BadZipFile,
            ):

                add_finding(
                    "Review",
                    name,
                    0,
                    "Could not read this file.",
                )

                continue

            lower_content = content.lower()

            for marker in AI_MARKERS:

                if marker in lower_content:
                    ai_found.add(marker)

            for line_no, line in enumerate(
                content.splitlines(),
                1,
            ):

                for label, pattern in SECRET_PATTERNS:

                    if pattern.search(line):

                        add_finding(
                            "High",
                            name,
                            line_no,
                            label
                            + ". Verify and revoke "
                            + "if a real credential is exposed.",
                        )

                for label, pattern in RISK_PATTERNS:

                    if pattern.search(line):

                        add_finding(
                            "Review",
                            name,
                            line_no,
                            label
                            + " pattern detected; "
                            + "review the code.",
                        )

    if not findings:

        findings.append(
            {
                "Severity": "Info",
                "File": "",
                "Line": 0,
                "Finding":
                    "No configured patterns detected. "
                    "This does not prove the project is safe.",
            }
        )

    return {
        "files": inventory,
        "findings": findings,
        "source_count": source_count,
        "ai_markers": sorted(ai_found),
    }


# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":

    latest = (
        st.session_state["test_runs"][-1]
        if st.session_state["test_runs"]
        else None
    )

    scan = st.session_state["latest_scan"]

    st.markdown(
        """
        <div class="tg-hero">
            <div class="tg-shield">🛡️</div>
            <h1>
                <span class="tg-gradient">
                    TraceGate
                </span>
            </h1>
            <div class="tg-subtitle">
                AI Application Pre-release Testing
            </div>
            <p class="tg-description">
                Inspect your AI project, identify potential
                risks, and track test results before release.
            </p>
            <span class="tg-pill">
                SCAN · TEST · REPORT
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    a, b, c = st.columns(3)

    with a:

        st.markdown(
            f"""
            <div class="tg-card blue">
                <div class="tg-label">
                    TEST RUNS
                </div>
                <div class="tg-number">
                    {test_usage}/{test_limit}
                </div>
                <div class="tg-small">
                    Current {effective_plan} quota
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with b:

        score = (
            f"{latest['Average Score']:.1f}/10"
            if latest
            else "—"
        )

        st.markdown(
            f"""
            <div class="tg-card green">
                <div class="tg-label">
                    LATEST AVERAGE SCORE
                </div>
                <div class="tg-number">
                    {score}
                </div>
                <div class="tg-small">
                    Manually entered ratings
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c:

        result = (
            latest["Result"]
            if latest
            else "No tests yet"
        )

        st.markdown(
            f"""
            <div class="tg-card purple">
                <div class="tg-label">
                    LATEST RESULT
                </div>
                <div style="font-size:17px;font-weight:700">
                    {result}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="tg-panel">
            <div class="tg-panel-title">
                ⚡ Quick Actions
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    q1, q2, q3, q4 = st.columns(4)

    with q1:

        st.markdown(
            """
            <div class="tg-action">
                <div class="tg-action-icon">📤</div>
                <div class="tg-action-title">
                    Upload & Scan
                </div>
                <div class="tg-action-desc">
                    Inspect your project ZIP.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Start Scan →",
            key="quick_scan",
            use_container_width=True,
        ):

            st.session_state["page"] = "Upload & Scan"
            st.rerun()

    with q2:

        st.markdown(
            """
            <div class="tg-action">
                <div class="tg-action-icon">▶️</div>
                <div class="tg-action-title">
                    Run a Test
                </div>
                <div class="tg-action-desc">
                    Compare two AI answers.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Run Test →",
            key="quick_test",
            use_container_width=True,
        ):

            st.session_state["page"] = "Run a Test"
            st.rerun()

    with q3:

        st.markdown(
            """
            <div class="tg-action">
                <div class="tg-action-icon">📋</div>
                <div class="tg-action-title">
                    Test History
                </div>
                <div class="tg-action-desc">
                    Review your saved tests.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "View History →",
            key="quick_history",
            use_container_width=True,
        ):

            st.session_state["page"] = "Test History"
            st.rerun()

    with q4:

        st.markdown(
            """
            <div class="tg-action">
                <div class="tg-action-icon">📊</div>
                <div class="tg-action-title">
                    Regression Report
                </div>
                <div class="tg-action-desc">
                    Compare against baseline.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "View Report →",
            key="quick_report",
            use_container_width=True,
        ):

            st.session_state["page"] = "Regression Report"
            st.rerun()

    if scan:

        st.markdown(
            f"""
            <div class="tg-row">
                📦 <b>Latest project scan</b>
                <br>
                <span class="tg-muted">
                    {len(scan["files"])} files ·
                    {len(scan["findings"])} findings
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# UPLOAD & SCAN
# =========================================================

elif page == "Upload & Scan":

    st.title("📤 Upload & Scan")

    st.caption(
        "Inspect a ZIP archive for selected "
        "source-code patterns."
    )

    st.info(
        f"{effective_plan} plan: "
        f"{scan_usage}/{scan_limit} scans used."
    )

    uploaded = st.file_uploader(
        "Choose your AI project ZIP",
        type=["zip"],
        help="Maximum compressed upload size: 20 MB.",
    )

    if uploaded is not None:

        st.caption(
            f"Selected: {uploaded.name}"
        )

        if st.button(
            "🛡️ Scan Project",
            type="primary",
        ):

            if not can_use("scan"):
                st.stop()

            try:

                with st.spinner(
                    "Inspecting project files..."
                ):

                    report = scan_project_zip(
                        uploaded.getvalue()
                    )

                user_id = get_user_id()

                # Persistent user-isolated scan
                supabase.table(
                    "scan_runs"
                ).insert(
                    {
                        "user_id": user_id,
                        "file_count": len(
                            report["files"]
                        ),
                        "source_count": report[
                            "source_count"
                        ],
                        "finding_count": len(
                            report["findings"]
                        ),
                        "ai_marker_count": len(
                            report["ai_markers"]
                        ),
                        "report": report,
                    }
                ).execute()

                st.session_state[
                    "latest_scan"
                ] = report

                st.success(
                    "Inspection completed and saved."
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Scan could not be saved: {exc}"
                )

    report = st.session_state[
        "latest_scan"
    ]

    if report:

        st.markdown("### Scan summary")

        x, y, z = st.columns(3)

        x.metric(
            "Files inventoried",
            len(report["files"]),
        )

        y.metric(
            "Source files",
            report["source_count"],
        )

        z.metric(
            "AI indicators",
            len(report["ai_markers"]),
        )

        st.markdown(
            "### AI library indicators"
        )

        st.write(
            ", ".join(
                report["ai_markers"]
            )
            if report["ai_markers"]
            else "None detected."
        )

        st.markdown(
            "### Project inventory"
        )

        st.dataframe(
            pd.DataFrame(
                {
                    "File":
                        report["files"][:100]
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Findings")

        df = pd.DataFrame(
            report["findings"]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download scan report",
            data=df.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="tracegate-scan-report.csv",
            mime="text/csv",
        )


# =========================================================
# RUN A TEST
# =========================================================

elif page == "Run a Test":

    st.title("🧪 Run a Test")

    st.caption(
        "Manually compare two model answers."
    )

    st.info(
        f"{effective_plan} plan: "
        f"{test_usage}/{test_limit} tests used."
    )

    test_name = st.text_input(
        "Test name",
        value="General quality check",
    )

    prompt = st.text_area(
        "Test prompt",
        placeholder="Enter the prompt...",
        height=110,
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown("### 🔵 Model A")

        answer_a = st.text_area(
            "Model A answer",
            height=170,
        )

        score_a = st.slider(
            "Model A quality score",
            0,
            10,
            5,
        )

    with c2:

        st.markdown("### 🟣 Model B")

        answer_b = st.text_area(
            "Model B answer",
            height=170,
        )

        score_b = st.slider(
            "Model B quality score",
            0,
            10,
            5,
        )

    if st.button(
        "Save Test Result",
        type="primary",
    ):

        if not can_use("test"):
            st.stop()

        if not test_name.strip():
            st.error(
                "Enter a test name."
            )

        elif not prompt.strip():
            st.error(
                "Enter a test prompt."
            )

        elif not answer_a.strip():
            st.error(
                "Enter Model A answer."
            )

        elif not answer_b.strip():
            st.error(
                "Enter Model B answer."
            )

        else:

            avg = (
                score_a + score_b
            ) / 2

            if score_a > score_b:
                result = (
                    "Model A scored higher"
                )

            elif score_b > score_a:
                result = (
                    "Model B scored higher"
                )

            else:
                result = "Tie"

            user_id = get_user_id()

            # Server-side user identity
            # comes from authenticated session.
            insert_result = (
                supabase
                .table("test_runs")
                .insert(
                    {
                        "user_id": user_id,
                        "run_id": test_usage + 1,
                        "test_name":
                            test_name.strip(),
                        "prompt":
                            prompt.strip(),
                        "model_a_answer":
                            answer_a.strip(),
                        "model_b_answer":
                            answer_b.strip(),
                        "model_a_score":
                            score_a,
                        "model_b_score":
                            score_b,
                        "average_score":
                            avg,
                        "result":
                            result,
                    }
                )
                .execute()
            )

            if insert_result.data:

                run = {
                    "Run ID":
                        test_usage + 1,
                    "Date (UTC)":
                        datetime.now(
                            timezone.utc
                        ).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    "Test Name":
                        test_name.strip(),
                    "Prompt":
                        prompt.strip(),
                    "Model A Answer":
                        answer_a.strip(),
                    "Model B Answer":
                        answer_b.strip(),
                    "Model A Score":
                        score_a,
                    "Model B Score":
                        score_b,
                    "Average Score":
                        avg,
                    "Result":
                        result,
                }

                st.session_state[
                    "test_runs"
                ].append(run)

                if (
                    st.session_state[
                        "baseline"
                    ]
                    is None
                ):

                    st.session_state[
                        "baseline"
                    ] = {
                        "Model A Score":
                            score_a,
                        "Model B Score":
                            score_b,
                        "Average Score":
                            avg,
                    }

                st.success(
                    "Test result saved to your account."
                )

                m1, m2, m3 = st.columns(3)

                m1.metric(
                    "Model A",
                    f"{score_a}/10",
                )

                m2.metric(
                    "Model B",
                    f"{score_b}/10",
                )

                m3.metric(
                    "Average",
                    f"{avg:.1f}/10",
                )

                st.write(result)

            else:

                st.error(
                    "The test could not be saved."
                )


# =========================================================
# TEST HISTORY
# =========================================================

elif page == "Test History":

    st.title("📋 Test History")

    user_id = get_user_id()

    try:

        result = (
            supabase
            .table("test_runs")
            .select("*")
            .eq("user_id", user_id)
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        history_data = result.data or []

    except Exception as exc:

        st.error(
            f"Could not load your history: {exc}"
        )

        history_data = []

    if not history_data:

        st.info(
            "No test results yet. "
            "Open Run a Test to add one."
        )

    else:

        history = pd.DataFrame(
            history_data
        )

        display_columns = [
            "run_id",
            "created_at",
            "test_name",
            "model_a_score",
            "model_b_score",
            "average_score",
            "result",
        ]

        available = [
            c for c in display_columns
            if c in history.columns
        ]

        st.dataframe(
            history[available],
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Export test history",
            data=history.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="tracegate-test-history.csv",
            mime="text/csv",
        )


# =========================================================
# REGRESSION REPORT
# =========================================================

elif page == "Regression Report":

    st.title("📊 Regression Report")

    runs = st.session_state[
        "test_runs"
    ]

    baseline = st.session_state[
        "baseline"
    ]

    if not runs or baseline is None:

        st.info(
            "Save a test result first "
            "to establish a baseline."
        )

    else:

        latest = runs[-1]

        df = pd.DataFrame(
            [
                {
                    "Metric":
                        "Model A score",
                    "Baseline":
                        baseline[
                            "Model A Score"
                        ],
                    "Latest":
                        latest[
                            "Model A Score"
                        ],
                },
                {
                    "Metric":
                        "Model B score",
                    "Baseline":
                        baseline[
                            "Model B Score"
                        ],
                    "Latest":
                        latest[
                            "Model B Score"
                        ],
                },
                {
                    "Metric":
                        "Average score",
                    "Baseline":
                        baseline[
                            "Average Score"
                        ],
                    "Latest":
                        latest[
                            "Average Score"
                        ],
                },
            ]
        )

        df["Change"] = (
            df["Latest"]
            - df["Baseline"]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        change = (
            latest["Average Score"]
            - baseline["Average Score"]
        )

        if change > 0:

            st.success(
                f"Average score increased by "
                f"{change:.1f} points."
            )

        elif change < 0:

            st.warning(
                f"Average score decreased by "
                f"{abs(change):.1f} points."
            )

        else:

            st.info(
                "Average score is unchanged."
            )


# =========================================================
# PRICING
# =========================================================

elif page == "Pricing":

    st.markdown(
        """
        <div class="tg-hero">
            <div class="tg-shield">💳</div>
            <h1>
                <span class="tg-gradient">
                    TraceGate Pricing
                </span>
            </h1>
            <div class="tg-subtitle">
                Choose the plan that matches your usage.
            </div>
            <p class="tg-description">
                Payments are not connected yet.
                Paid access remains locked until a verified
                payment is recorded.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)

    for col, (
        plan_name,
        plan_data,
    ) in zip(
        cols,
        PLANS.items(),
    ):

        with col:

            featured = (
                plan_name == "Pro"
            )

            class_name = (
                "tg-plan featured"
                if featured
                else "tg-plan"
            )

            features = {
                "Starter": [
                    "3 scans/month",
                    "10 tests/month",
                    "ZIP static scanning",
                    "Test history",
                    "CSV export",
                ],
                "Pro": [
                    "50 scans/month",
                    "200 tests/month",
                    "Persistent history",
                    "Regression tracking",
                    "CSV reports",
                ],
                "Team": [
                    "200 scans/month",
                    "1,000 tests/month",
                    "Team workspaces",
                    "Audit trail",
                    "Priority support",
                ],
            }[plan_name]

            feature_html = ""

            for feature in features:

                feature_html += (
                    '<div class="tg-plan-feature">'
                    '<span class="tg-plan-check">✓</span>'
                    + feature
                    + "</div>"
                )

            st.markdown(
                f"""
                <div class="{class_name}">
                    <div class="tg-plan-title">
                        {plan_name}
                    </div>

                    <div class="tg-plan-price">
                        ₹{plan_data["price"]}
                        <span style="font-size:13px">
                            {" / month"
                            if plan_data["price"]
                            else " / forever"}
                        </span>
                    </div>

                    <p>
                        {plan_data["description"]}
                    </p>

                    <hr>

                    {feature_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

            if plan_name == effective_plan:

                st.success(
                    "Your current plan"
                )

            elif plan_name == "Starter":

                if st.button(
                    "Use Starter",
                    key="starter_plan",
                    use_container_width=True,
                ):

                    st.info(
                        "You are already eligible "
                        "for the free Starter plan."
                    )

            else:

                if st.button(
                    f"Upgrade to {plan_name}",
                    key=f"upgrade_{plan_name}",
                    use_container_width=True,
                ):

                    st.warning(
                        f"{plan_name} checkout is not "
                        "enabled yet. No payment has been "
                        "taken and your plan has not changed."
                    )

    st.markdown(
        """
        <div class="tg-panel">
            <div class="tg-panel-title">
                🔐 Payment protection
            </div>

            <div class="tg-panel-sub">
                TraceGate does not treat a button click as
                a purchase.
            </div>

            <p class="tg-muted">
                Pro and Team become active only when your
                database contains the corresponding plan
                together with payment_status = verified.
                Until then, the account is treated as Starter.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
