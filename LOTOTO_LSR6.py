
import streamlit as st
import psycopg2
from psycopg2 import IntegrityError
from supabase import create_client
import json
import pandas as pd
import os
import uuid
import hashlib
import secrets
import hmac
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ============================================================
# LOTOTO / LSR 6 - ENERGY ISOLATION SAFETY MANAGEMENT SYSTEM
# Based on the uploaded LSR 3rd Edition 2025:
# LSR 6 - Isolasi Energi (LOTOTO)
#
# LSR 6 sequence:
# 1. Identifikasi sumber energi
# 2. Beritahukan pihak-pihak terkait
# 3. Matikan mesin/alat dan/atau isolasi sumber energi
# 4. Terapkan penguncian (Lock Out)
# 5. Terapkan penandaan (Tag Out)
# 6. Lakukan uji/coba (Try Out)
# 7. Periksa dan mengembalikan seperti semula
# ============================================================

st.set_page_config(
    page_title="LSR 6 - LOTOTO Safety System",
    page_icon="🔒",
    layout="wide"
)


# ============================================================
# SIGN IN / SIGN UP - LIGHT INPUT BOX + BLACK TYPED TEXT
# ============================================================
st.markdown("""
<style>
/* Labels and headings remain dark on the light page */
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] *,
.stApp label,
.stApp label * {
    color: #29485B !important;
    -webkit-text-fill-color: #29485B !important;
    opacity: 1 !important;
    font-weight: 650 !important;
}

/* The entire visible input shell is WHITE */
.stApp [data-testid="stTextInput"] div[data-baseweb="input"],
.stApp [data-testid="stTextInput"] div[data-baseweb="base-input"],
.stApp div[data-baseweb="input"],
.stApp div[data-baseweb="base-input"] {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    border: 1px solid #C8D7DE !important;
    border-radius: 11px !important;
    box-shadow: none !important;
}

/* Typed characters are BLACK; input itself stays white */
.stApp [data-testid="stTextInput"] input,
.stApp [data-testid="stTextArea"] textarea,
.stApp div[data-baseweb="input"] input,
.stApp div[data-baseweb="base-input"] input,
.stApp input[type="text"],
.stApp input[type="password"],
.stApp input[type="email"],
.stApp textarea {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    opacity: 1 !important;
    font-weight: 600 !important;
    text-shadow: none !important;
    border-radius: 9px !important;
    box-shadow: none !important;
}

/* Keep the white surface when focused */
.stApp [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
.stApp [data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
.stApp div[data-baseweb="input"]:focus-within,
.stApp div[data-baseweb="base-input"]:focus-within {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    border: 2px solid #168B83 !important;
    box-shadow: 0 0 0 2px rgba(22,139,131,.12) !important;
}

/* Placeholder is medium gray, while typed text remains black */
.stApp input::placeholder,
.stApp textarea::placeholder {
    color: #7B8D97 !important;
    -webkit-text-fill-color: #7B8D97 !important;
    opacity: 1 !important;
    font-weight: 400 !important;
}

/* Tabs: light background, readable dark text */
.stApp [data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #EDF3F6 !important;
    border-bottom: 1px solid #D7E2E7 !important;
}
.stApp [data-testid="stTabs"] button[role="tab"],
.stApp [data-testid="stTabs"] button[role="tab"] *,
.stApp [data-testid="stTabs"] button[role="tab"] p {
    color: #29485B !important;
    -webkit-text-fill-color: #29485B !important;
    opacity: 1 !important;
    font-weight: 700 !important;
}
.stApp [data-testid="stTabs"] button[role="tab"][aria-selected="true"],
.stApp [data-testid="stTabs"] button[role="tab"][aria-selected="true"] *,
.stApp [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
    color: #087C75 !important;
    -webkit-text-fill-color: #087C75 !important;
    font-weight: 800 !important;
}

/* Helper/caption text */
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] * {
    color: #526B7B !important;
    -webkit-text-fill-color: #526B7B !important;
}

/* Buttons keep white lettering on teal background */
.stApp [data-testid="stFormSubmitButton"] button,
.stApp [data-testid="stFormSubmitButton"] button *,
.stApp [data-testid="stFormSubmitButton"] button p,
.stApp [data-testid="stFormSubmitButton"] button span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    opacity: 1 !important;
    font-weight: 750 !important;
}
.stApp [data-testid="stFormSubmitButton"] button:disabled {
    background: #168B83 !important;
    opacity: 1 !important;
}

/* Chrome autofill: white field with black autofilled text */
.stApp input:-webkit-autofill,
.stApp input:-webkit-autofill:hover,
.stApp input:-webkit-autofill:focus {
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
    -webkit-box-shadow: 0 0 0 1000px #FFFFFF inset !important;
    box-shadow: 0 0 0 1000px #FFFFFF inset !important;
}
</style>
""", unsafe_allow_html=True)








# ============================================================
# UI THEME - LIGHT INDUSTRIAL / SAFETY DASHBOARD
# ============================================================
st.markdown("""
<style>
:root {
    --lototo-ink: #183247;
    --lototo-muted: #667b8b;
    --lototo-teal: #168b83;
    --lototo-teal-dark: #0f6f6a;
    --lototo-amber: #f2ad45;
    --lototo-bg: #f3f7fa;
    --lototo-card: #ffffff;
    --lototo-line: #e1eaf0;
}
.stApp {
    background:
        radial-gradient(circle at 92% 2%, rgba(22,139,131,.08), transparent 25rem),
        linear-gradient(180deg, #f7fafc 0%, #f1f6f9 100%);
    color: var(--lototo-ink);
}
[data-testid="stHeader"] { background: rgba(247,250,252,.82); }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }
h1, h2, h3 { color: var(--lototo-ink); letter-spacing: -.025em; }
h1 { font-weight: 800 !important; }
h2, h3 { font-weight: 750 !important; }
p, label, [data-testid="stCaptionContainer"] { color: var(--lototo-muted); }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #eaf3f5 0%, #f5f8fa 100%);
    border-right: 1px solid #dce8ed;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.3rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 { color: #17384a; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > label {
    color: #456173; font-weight: 700;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
    background: #fff !important;
    border-color: #d7e3e9 !important;
    border-radius: 11px !important;
}
.stButton > button, .stFormSubmitButton > button {
    border-radius: 11px;
    border: 1px solid #168b83;
    background: linear-gradient(135deg, #168b83, #11766f);
    color: white;
    font-weight: 700;
    padding: .55rem 1rem;
    box-shadow: 0 5px 14px rgba(22,139,131,.13);
    transition: transform .15s ease, box-shadow .15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: #0f6f6a; color: white;
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(22,139,131,.2);
}
.stButton > button[kind="secondary"] {
    background: #fff; color: #24616a; border-color: #d5e3e8; box-shadow: none;
}
div[data-testid="stMetric"] {
    background: #fff; border: 1px solid var(--lototo-line);
    border-radius: 16px; padding: 17px 18px;
    box-shadow: 0 5px 18px rgba(29,66,85,.045);
}
div[data-testid="stMetricLabel"] { color: #627b89; font-weight: 650; }
div[data-testid="stMetricValue"] { color: #17384a; font-weight: 800; }
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px; background: #edf3f5; padding: 6px; border-radius: 13px;
}
[data-testid="stTabs"] button[role="tab"] {
    border-radius: 9px; color: #557080; font-weight: 700;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: #fff; color: #11766f; box-shadow: 0 2px 8px rgba(20,55,70,.08);
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid #e1eaf0; border-radius: 13px; overflow: hidden;
}
hr { border-color: #dce7ec; }
div[data-testid="stAlert"] { border-radius: 12px; }
.lototo-brand {
    background: linear-gradient(135deg, #153c50 0%, #187f7a 100%);
    color: white; padding: 18px 18px 16px; border-radius: 17px;
    box-shadow: 0 12px 26px rgba(21,60,80,.16); margin-bottom: 18px;
}
.lototo-brand .brand-kicker {
    color: #bfe8e2; font-size: .72rem; font-weight: 800;
    letter-spacing: .13em; text-transform: uppercase;
}
.lototo-brand .brand-title {
    color: white; font-size: 1.45rem; font-weight: 850;
    letter-spacing: -.035em; margin-top: 5px;
}
.lototo-brand .brand-sub { color: #d5e8ed; font-size: .84rem; margin-top: 3px; }
.lototo-login-shell {
    background: rgba(255,255,255,.92); border: 1px solid #e0eaf0;
    border-radius: 22px; padding: 1.6rem 1.6rem 1.25rem;
    box-shadow: 0 18px 50px rgba(31,69,88,.09);
}
.lototo-login-hero {
    background: linear-gradient(135deg, #173e52 0%, #187f7a 100%);
    border-radius: 20px; padding: 28px 28px 25px; color: white;
    min-height: 275px; display: flex; flex-direction: column; justify-content: space-between;
    box-shadow: 0 14px 30px rgba(20,69,83,.17);
}
.lototo-login-hero .eyebrow {
    color: #b9e9df; font-size: .72rem; font-weight: 800; letter-spacing: .15em;
}
.lototo-login-hero h2 { color: white !important; font-size: 2rem; line-height: 1.12; margin: 13px 0 10px; }
.lototo-login-hero p { color: #d9e9ec !important; line-height: 1.55; }
.lototo-login-hero .hero-foot {
    border-top: 1px solid rgba(255,255,255,.2); padding-top: 14px;
    color: #d9e9ec; font-size: .82rem;
}
.lototo-section-kicker {
    color: #168b83; text-transform: uppercase; letter-spacing: .12em;
    font-size: .72rem; font-weight: 850;
}
[data-testid="stForm"] {
    border: 1px solid #e3edf1; border-radius: 15px;
    padding: 1.1rem; background: #fff;
}
@media (max-width: 800px) {
    .block-container { padding-top: 1rem; }
    .lototo-login-hero { min-height: 190px; margin-bottom: 1rem; }
    .lototo-login-hero h2 { font-size: 1.55rem; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SUPABASE CONFIGURATION
# Local: .streamlit/secrets.toml
# Streamlit Cloud: App settings -> Secrets
# Never commit secrets.toml or expose server-side keys.
# ============================================================
def read_secret(name, default=None):
    """Read a setting from Streamlit Secrets, then environment variables."""
    try:
        value = st.secrets.get(name, None)
    except Exception:
        value = None
    if value is None or str(value).strip() == "":
        value = os.getenv(name, default)
    if value is None:
        return default
    return str(value).strip()

SUPABASE_URL = read_secret("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = read_secret("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_DB_URL = read_secret("SUPABASE_DB_URL")
SUPABASE_BUCKET = read_secret("SUPABASE_BUCKET", "lototo-evidence")

missing_settings = [
    name for name, value in [
        ("SUPABASE_URL", SUPABASE_URL),
        ("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY),
        ("SUPABASE_DB_URL", SUPABASE_DB_URL),
    ] if not value
]

if missing_settings:
    st.error(
        "Konfigurasi Supabase belum lengkap. Periksa .streamlit/secrets.toml "
        "atau Streamlit Cloud -> Settings -> Secrets. Variabel yang belum ada: "
        + ", ".join(missing_settings)
    )
    st.stop()

# create_client expects the base project URL, e.g. https://xxxx.supabase.co,
# not the REST endpoint ending in /rest/v1/.
SUPABASE_URL = SUPABASE_URL.rstrip("/")
if SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL[:-len("/rest/v1")]

@st.cache_resource(show_spinner=False)
def get_supabase_client(project_url, server_key):
    """Reuse the Supabase API client across Streamlit reruns."""
    return create_client(project_url, server_key)

try:
    supabase = get_supabase_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
except Exception as exc:
    st.error(
        "Gagal membuat client Supabase. Periksa SUPABASE_URL dan API key "
        f"server-side. Detail: {exc}"
    )
    st.stop()

# Reuse PostgreSQL connection across Streamlit reruns to avoid a new network
# handshake on every menu interaction. This simple shared connection is intended
# for a single-user/demo app; use a proper connection pool for concurrent users.
@st.cache_resource(show_spinner=False)
def get_database_connection(database_url):
    connection = psycopg2.connect(
        database_url,
        sslmode="require",
        connect_timeout=10,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=3,
    )
    connection.autocommit = False
    return connection

# The app uses PostgreSQL SQL queries (psycopg2), so SUPABASE_DB_URL must be
# the PostgreSQL connection URI from Supabase -> Connect, not the Project URL
# and not the REST API URL. Its database password is separate from the API key.
try:
    conn = get_database_connection(SUPABASE_DB_URL)
    # Recover a cached connection left INTRANS by a previous Streamlit rerun.
    # All write workflows below explicitly commit; an open transaction here is
    # therefore treated as an abandoned read transaction.
    if conn.get_transaction_status() != psycopg2.extensions.TRANSACTION_STATUS_IDLE:
        conn.rollback()
    cursor = conn.cursor()
except psycopg2.OperationalError as exc:
    error_text = str(exc).lower()
    if "password authentication failed" in error_text:
        st.error(
            "Password database Supabase ditolak. Perbarui SUPABASE_DB_URL "
            "menggunakan connection string terbaru dari Supabase -> Connect -> "
            "Connection string (URI), dengan password PostgreSQL yang benar. "
            "Password database bukan SUPABASE_SERVICE_ROLE_KEY."
        )
    elif "could not translate host name" in error_text or "name or service not known" in error_text:
        st.error("Host pada SUPABASE_DB_URL tidak valid. Salin ulang connection string URI dari Supabase -> Connect.")
    elif "timeout" in error_text or "network is unreachable" in error_text:
        st.error(
            "Koneksi ke PostgreSQL Supabase gagal karena jaringan/IPv6 atau timeout. "
            "Coba connection string Session Pooler dari menu Connect di Supabase, "
            "dan gunakan host, port, serta username persis seperti yang ditampilkan."
        )
    else:
        st.error(f"Gagal terhubung ke PostgreSQL Supabase: {exc}")
    st.stop()

# ============================================================
# PTW TYPES & CHECKLIST CONFIGURATION
# ============================================================

PTW_TYPES = [
    "Rotating Equipment",
    "Work at Height",
    "Confined Space",
    "Hot Area",
    "Hot Work",
    "Excavation",
    "Lifting Work",
]

PTW_CONFIG = {
    "Rotating Equipment": [
        "Pekerja sehat/fit.",
        "Safety briefing/kompetensi rotating equipment terpenuhi.",
        "Instruksi kerja aman telah dibuat dan dipahami.",
        "Peralatan tidak dalam kondisi beroperasi.",
        "Lokal switch OFF serta Lock Out, Tag Out, Try Out diterapkan.",
        "MCC breaker OFF serta Lock Out, Tag Out, Try Out diterapkan.",
        "CCR/CCP telah diinformasikan dan sistem OUT OF SERVICE.",
    ],
    "Work at Height": [
        "Pekerja sehat/fit.",
        "Induksi/briefing bekerja di ketinggian telah dilakukan.",
        "Pelatihan yang dipersyaratkan telah terpenuhi.",
        "Area telah disurvey dan potensi bahaya diidentifikasi.",
        "Peralatan ketinggian diperiksa dengan metode Look-Feel-Function.",
        "Tangga/portable ladder memenuhi standar.",
        "Jika terkait sumber energi, LOTOTO telah diterapkan.",
    ],
    "Confined Space": [
        "JSA tersedia.",
        "Kondisi atmosfer diuji sebelum masuk.",
        "Kadar oksigen diperiksa.",
        "Gas/uap mudah terbakar diperiksa.",
        "CO dan H2S diperiksa.",
        "Sumber energi terkait telah diisolasi dengan LOTOTO.",
        "LOTOTO diterapkan secara efektif.",
        "Kesiagaan darurat dan komunikasi telah disiapkan.",
    ],
    "Hot Area": [
        "Pekerja sehat/fit.",
        "Safety briefing area panas telah dilakukan.",
        "Sumber energi/material/gas panas ditutup/dimatikan dan LOTOTO diterapkan.",
        "APD pekerjaan area panas tersedia.",
        "Akses area kerja telah diamankan.",
        "Alat komunikasi tersedia dan berfungsi.",
        "Jalur evakuasi telah diketahui.",
        "Fire blanket tersedia bila diperlukan.",
    ],
    "Hot Work": [
        "Pekerja sehat/fit.",
        "Safety briefing pekerjaan panas telah dilakukan.",
        "Peralatan las dan perlengkapannya dalam kondisi baik.",
        "Pelindung tahan api tersedia.",
        "APAR siap digunakan.",
        "Area pekerjaan panas bersih dan kering.",
        "Ventilasi memadai.",
        "Fire Watcher tersedia bila dipersyaratkan.",
    ],
    "Excavation": [
        "Pekerja sehat/fit.",
        "Induksi/briefing penggalian telah dilakukan.",
        "Jika terkait sumber energi, LOTOTO telah diterapkan.",
        "Area telah disurvey dan utilitas bawah tanah diidentifikasi.",
        "Denah kabel/pipa atau existing utility tersedia dan disetujui.",
        "Peralatan penggalian diperiksa.",
        "Sertifikasi operator terpenuhi bila dipersyaratkan.",
        "Safety line dan papan peringatan tersedia.",
        "Kondisi cuaca memungkinkan pekerjaan.",
    ],
    "Lifting Work": [
        "Induksi/briefing pekerjaan pengangkatan telah dilakukan.",
        "Lisensi petugas masih berlaku.",
        "Peralatan pengangkatan memiliki izin yang berlaku.",
        "Method Statement/Lifting Plan telah disetujui.",
        "Lembar perhitungan pengangkatan tersedia.",
        "Skenario keadaan darurat telah ditetapkan.",
        "Crane diperiksa sesuai lifting plan.",
        "Area manuver crane telah diperiksa.",
        "Akses area diblokade dan diberi rambu.",
        "Area pengangkatan bebas rintangan.",
        "Sling/peralatan lifting diperiksa.",
        "Kondisi cuaca memungkinkan pekerjaan.",
        "Penerangan memadai untuk pekerjaan malam.",
    ],
}

# ============================================================
# DATABASE (Supabase PostgreSQL)
# Run schema checks/migrations once per app process, not on every rerun.
# ============================================================

@st.cache_resource(show_spinner=False)
def initialize_database(database_url):
    """Create required tables and add missing columns once per app process."""
    db_conn = get_database_connection(database_url)
    db_cursor = db_conn.cursor()
    db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS machines (
        id BIGSERIAL PRIMARY KEY,
        machine_id TEXT UNIQUE,
        machine_name TEXT NOT NULL,
        area TEXT,
        energy_source TEXT,
        isolation_point TEXT,
        status TEXT DEFAULT 'AVAILABLE'
    )
    """)
    db_cursor.execute("ALTER TABLE public.machines ADD COLUMN IF NOT EXISTS tag_padlock_total INTEGER")
    db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS public.equipment_lototo_matrix (
        working_machine_id TEXT NOT NULL REFERENCES public.machines(machine_id),
        lototo_machine_id TEXT NOT NULL REFERENCES public.machines(machine_id),
        PRIMARY KEY (working_machine_id, lototo_machine_id)
    )
    """)
    db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS lototo (
        id BIGSERIAL PRIMARY KEY,
        work_order TEXT NOT NULL,
        machine_id TEXT NOT NULL,
        technician TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        energy_identified INTEGER DEFAULT 0,
        parties_notified INTEGER DEFAULT 0,
        shutdown_isolated INTEGER DEFAULT 0,
        lock_out INTEGER DEFAULT 0,
        tag_out INTEGER DEFAULT 0,
        try_out INTEGER DEFAULT 0,
        checked_restored INTEGER DEFAULT 0,
        lock_photo TEXT,
        tag_photo TEXT,
        lock_photo_time TEXT,
        tag_photo_time TEXT,
        jsa_photo TEXT,
        dra_photo TEXT,
        ptw_photo TEXT,
        ptw_type TEXT,
        ptw_number TEXT,
        safety_briefing_photo TEXT,
        safety_briefing_photo_time TEXT,
        ptw_checklist_json TEXT,
        jsa_photo_time TEXT,
        dra_photo_time TEXT,
        ptw_photo_time TEXT,
        end_lock_photo TEXT,
        end_tag_photo TEXT,
        end_lock_photo_time TEXT,
        end_tag_photo_time TEXT,
        lototo_status TEXT DEFAULT 'NOT STARTED',
        work_status TEXT DEFAULT 'ACTIVE',
        end_confirmation INTEGER DEFAULT 0
    )
    """)
    db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS public.lototo_equipment_items (
        id BIGSERIAL PRIMARY KEY,
        lototo_id BIGINT NOT NULL REFERENCES public.lototo(id) ON DELETE CASCADE,
        working_machine_id TEXT NOT NULL,
        equipment_machine_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        started_at TEXT,
        ended_at TEXT,
        end_lock_photo TEXT,
        end_tag_photo TEXT,
        end_evidence_time TEXT,
        UNIQUE (lototo_id, equipment_machine_id)
    )
    """)
    db_cursor.execute("CREATE INDEX IF NOT EXISTS idx_lototo_equipment_parent ON public.lototo_equipment_items (lototo_id, status)")
    db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS public.app_users (
        id BIGSERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        is_active BOOLEAN NOT NULL DEFAULT TRUE
    )
    """)
    db_conn.commit()

    migration_columns = {
        "energy_identified": "INTEGER DEFAULT 0",
        "parties_notified": "INTEGER DEFAULT 0",
        "shutdown_isolated": "INTEGER DEFAULT 0",
        "lock_out": "INTEGER DEFAULT 0",
        "tag_out": "INTEGER DEFAULT 0",
        "try_out": "INTEGER DEFAULT 0",
        "checked_restored": "INTEGER DEFAULT 0",
        "lock_photo": "TEXT", "tag_photo": "TEXT",
        "lock_photo_time": "TEXT", "tag_photo_time": "TEXT",
        "jsa_photo": "TEXT", "dra_photo": "TEXT", "ptw_photo": "TEXT",
        "ptw_type": "TEXT", "ptw_number": "TEXT",
        "safety_briefing_photo": "TEXT", "safety_briefing_photo_time": "TEXT",
        "ptw_checklist_json": "TEXT", "jsa_photo_time": "TEXT",
        "dra_photo_time": "TEXT", "ptw_photo_time": "TEXT",
        "end_lock_photo": "TEXT", "end_tag_photo": "TEXT",
        "end_lock_photo_time": "TEXT", "end_tag_photo_time": "TEXT",
        "lototo_status": "TEXT DEFAULT 'NOT STARTED'",
        "work_status": "TEXT DEFAULT 'ACTIVE'",
        "end_confirmation": "INTEGER DEFAULT 0",
    }
    for column, definition in migration_columns.items():
        db_cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s AND column_name = %s",
            ("lototo", column),
        )
        if db_cursor.fetchone() is None:
            db_cursor.execute(f'ALTER TABLE "lototo" ADD COLUMN "{column}" {definition}')
    db_cursor.execute("CREATE INDEX IF NOT EXISTS idx_lototo_work_status ON lototo (work_status)")
    db_cursor.execute("CREATE INDEX IF NOT EXISTS idx_lototo_start_time ON lototo (start_time DESC)")
    db_cursor.execute("CREATE INDEX IF NOT EXISTS idx_lototo_end_time ON lototo (end_time DESC)")
    db_conn.commit()
    db_cursor.close()
    return True

try:
    initialize_database(SUPABASE_DB_URL)
except Exception as exc:
    st.error(f"Gagal menyiapkan tabel Supabase: {exc}")
    st.stop()

# Create a fresh cursor for this script run. Schema initialization above is cached.
cursor = conn.cursor()

# ============================================================
# FUNCTIONS
# ============================================================

def read_sql_df(query, params=None):
    """Run a read-only query and always close its PostgreSQL transaction."""
    try:
        result = pd.read_sql_query(query, conn, params=params)
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
        return result


def get_machines():
    return read_sql_df(
        """
        SELECT *
        FROM machines
        ORDER BY machine_id
        """
    )


def get_lototo():
    return read_sql_df(
        """
        SELECT *
        FROM lototo
        ORDER BY id DESC
        """
    )


def get_active_lototo():
    return read_sql_df(
        """
        SELECT *
        FROM lototo
        WHERE work_status = 'ACTIVE'
        ORDER BY start_time DESC
        """
    )


def get_history():
    return read_sql_df(
        """
        SELECT *
        FROM lototo
        WHERE work_status = 'COMPLETED'
        ORDER BY end_time DESC
        """
    )


def calculate_lototo_status(row):
    """
    LSR 6 status is based on the seven LSR steps.
    Photo evidence is required for Lock Out and Tag Out.
    """
    steps = [
        row["energy_identified"],
        row["parties_notified"],
        row["shutdown_isolated"],
        row["lock_out"],
        row["tag_out"],
        row["try_out"],
        row["checked_restored"],
    ]

    if all(steps):
        return "LSR 6 COMPLETE"

    if any(steps):
        return "IN PROGRESS"

    return "NOT STARTED"


def save_uploaded_file(uploaded_file, work_order, evidence_type):
    """Upload evidence to persistent Supabase Storage and return its object path."""
    if uploaded_file is None:
        return None
    extension = os.path.splitext(uploaded_file.name)[1].lower()
    unique_id = uuid.uuid4().hex[:12]
    safe_work_order = "".join(c if c.isalnum() or c in "-_" else "_" for c in work_order)
    filename = f"{safe_work_order}_{evidence_type}_{unique_id}{extension}"
    object_path = f"{datetime.now().strftime('%Y/%m')}/{filename}"
    content_type = getattr(uploaded_file, "type", None) or "application/octet-stream"
    try:
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            object_path,
            uploaded_file.getvalue(),
            {"content-type": content_type, "upsert": "false"}
        )
    except Exception as exc:
        st.error(f"Gagal mengunggah evidence ke Supabase Storage: {exc}")
        raise
    return object_path


def save_uploaded_files_parallel(items, work_order, max_workers=4):
    """Upload independent evidence files concurrently to reduce network wait.

    items is a sequence of (evidence_type, uploaded_file) pairs. Returns a
    dict mapping each evidence_type to its Supabase Storage object path.
    If any upload fails, the exception is raised so the LOTOTO record is not
    inserted/updated as if all required evidence had been saved successfully.
    """
    items = [(kind, file_obj) for kind, file_obj in items if file_obj is not None]
    if not items:
        return {}

    with ThreadPoolExecutor(max_workers=min(max_workers, len(items))) as executor:
        futures = {
            kind: executor.submit(save_uploaded_file, file_obj, work_order, kind)
            for kind, file_obj in items
        }
        # Resolve all results; propagate errors to the caller.
        return {kind: future.result() for kind, future in futures.items()}


def evidence_exists(path):
    # Database stores the object path, not a local filesystem path.
    return isinstance(path, str) and bool(path.strip())


def evidence_url(path):
    """Create a short-lived URL for a private evidence object."""
    if not evidence_exists(path):
        return None
    try:
        result = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(path, 3600)
        return result.get("signedURL") or result.get("signedUrl")
    except Exception:
        return None


def show_evidence(path, width=400, caption=None):
    url = evidence_url(path)
    if url:
        st.image(url, width=width, caption=caption)
    else:
        st.info("Bukti foto tidak tersedia atau gagal diakses.")


def duration_between(start_time, end_time):
    if not start_time or not end_time:
        return ""

    start = pd.to_datetime(start_time)
    end = pd.to_datetime(end_time)

    return str(end - start)


# ============================================================
# EQUIPMENT CATALOG + LOTOTO MATRIX
# Imported from all five sheets in the uploaded workbook: 131 equipment, 339 V mappings.
# ============================================================

WORKING_EQUIPMENT_CATALOG = [{'machine_id': 'N6021BE01', 'machine_name': 'BUCKET ELEVATOR LINE 1', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021VC01', 'machine_name': 'VIBRATING CONVEYOR LINE 1', 'points': 2, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021SG01', 'machine_name': 'THROTTLE VALVE', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021BA01', 'machine_name': 'BAG APPLICATOR', 'points': 1, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021RA01', 'machine_name': 'ROTARY FEEDER LINE 1', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021CV01', 'machine_name': 'CHAIN CONVEYOR', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021RY01', 'machine_name': 'ROTARY SCREEN', 'points': 2, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021BF01', 'machine_name': 'SMALL BAG FILTER 1', 'points': 2, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021FN01', 'machine_name': 'SMALL BAG FILTER FAN 1', 'points': 2, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021BF02', 'machine_name': 'SMALL BAG FILTER 2', 'points': 2, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021FN02', 'machine_name': 'SMALL BAG FILTER FAN 2', 'points': 2, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021PM01', 'machine_name': 'PACKER MACHINE 1', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021BC01', 'machine_name': 'BELT CONVEYOR 1', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021NS01', 'machine_name': 'BELT BAG CLEANER', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021BC02', 'machine_name': 'BELT CONVEYOR 2', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021CW01', 'machine_name': 'BELT CHECK WEIGHT', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021BR01', 'machine_name': 'BELT REJECT', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021BC03', 'machine_name': 'BELT CONVEYOR 3', 'points': 2, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021YD01', 'machine_name': 'BELT DIVERTER', 'points': 2, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021BC04', 'machine_name': 'BELT CONVEYOR 4', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021RB01', 'machine_name': 'GRAVITY ROLLER', 'points': 3, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021PA01', 'machine_name': 'PALLETIZER 1', 'points': 1, 'area': 'PH LINE 1'},
 {'machine_id': 'N6021GK01',
  'machine_name': 'ROLLER CURVE TO PALLETIZER 3',
  'points': 2,
  'area': 'PH LINE 1'},
 {'machine_id': 'N6022BE01', 'machine_name': 'BUCKET ELEVATOR LINE 2', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022VC01', 'machine_name': 'VIBRATING CONVEYOR LINE 2', 'points': 2, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022SG01', 'machine_name': 'THROTTLE VALVE', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022BA01', 'machine_name': 'BAG APPLICATOR', 'points': 1, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022RA01', 'machine_name': 'ROTARY FEEDER LINE 2', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022CV01', 'machine_name': 'CHAIN CONVEYOR', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022RY01', 'machine_name': 'ROTARY SCREEN', 'points': 2, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022BF01', 'machine_name': 'SMALL BAG FILTER 1', 'points': 2, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022FN01', 'machine_name': 'SMALL BAG FILTER FAN 1', 'points': 2, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022BF02', 'machine_name': 'SMALL BAG FILTER 2', 'points': 2, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022FN02', 'machine_name': 'SMALL BAG FILTER FAN 2', 'points': 2, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022PM01', 'machine_name': 'PACKER MACHINE 2', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022BC01', 'machine_name': 'BELT CONVEYOR 1', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022NS01', 'machine_name': 'BELT BAG CLEANER', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022BC02', 'machine_name': 'BELT CONVEYOR 2', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022CW01', 'machine_name': 'BELT CHECK WEIGHT', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022BR01', 'machine_name': 'BELT REJECT', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022BC03', 'machine_name': 'BELT CONVEYOR 3', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022GK01', 'machine_name': 'ROLLER CURVE 1', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022BC04', 'machine_name': 'BELT CONVEYOR 4', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022GK02', 'machine_name': 'ROLLER CURVE 2', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N60222BC05', 'machine_name': 'BELT CONVEYOR 5', 'points': 4, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022YD01', 'machine_name': 'BELT DIVERTER', 'points': 2, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022GK03', 'machine_name': 'ROLLER CURVE 3', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022BC06', 'machine_name': 'BELT CONVEYOR 6', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022RB01', 'machine_name': 'GRAVITY ROLLER', 'points': 3, 'area': 'PH LINE 2'},
 {'machine_id': 'N6022PA01', 'machine_name': 'PALLETIZER 2', 'points': 1, 'area': 'PH LINE 2'},
 {'machine_id': 'N6023BE01', 'machine_name': 'BUCKET ELEVATOR LINE 3', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023VC01', 'machine_name': 'VIBRATING CONVEYOR LINE 3', 'points': 2, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023SG01', 'machine_name': 'THROTTLE VALVE', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023BA01', 'machine_name': 'BAG APPLICATOR', 'points': 1, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023RA01', 'machine_name': 'ROTARY FEEDER LINE 3', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023CV01', 'machine_name': 'CHAIN CONVEYOR', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023RY01', 'machine_name': 'ROTARY SCREEN', 'points': 2, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023BF01', 'machine_name': 'SMALL BAG FILTER 1', 'points': 2, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023FN01', 'machine_name': 'SMALL BAG FILTER FAN 1', 'points': 2, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023BF02', 'machine_name': 'SMALL BAG FILTER 2', 'points': 2, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023FN02', 'machine_name': 'SMALL BAG FILTER FAN 2', 'points': 2, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023PM01', 'machine_name': 'PACKER MACHINE 3', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023BC01', 'machine_name': 'BELT CONVEYOR 1', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023NS01', 'machine_name': 'BELT BAG CLEANER', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023BC02', 'machine_name': 'BELT CONVEYOR 2', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023CW01', 'machine_name': 'BELT CHECK WEIGHT', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023BR01', 'machine_name': 'BELT REJECT', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023BC03', 'machine_name': 'BELT CONVEYOR 3', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023GK01', 'machine_name': 'ROLLER CURVE 1', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023BC04', 'machine_name': 'BELT CONVEYOR 4', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023GK02', 'machine_name': 'ROLLER CURVE 2', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N60232BC05', 'machine_name': 'BELT CONVEYOR 5', 'points': 4, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023YD01', 'machine_name': 'BELT DIVERTER', 'points': 2, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023GK03', 'machine_name': 'ROLLER CURVE 3', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023BC06', 'machine_name': 'BELT CONVEYOR 6', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023RB01', 'machine_name': 'GRAVITY ROLLER', 'points': 3, 'area': 'PH LINE 3'},
 {'machine_id': 'N6023PA01', 'machine_name': 'PALLETIZER 3', 'points': 1, 'area': 'PH LINE 3'},
 {'machine_id': 'N6024BE01', 'machine_name': 'BUCKET ELEVATOR LINE 4', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024VC01', 'machine_name': 'VIBRATING CONVEYOR LINE 4', 'points': 2, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024SG01', 'machine_name': 'THROTTLE VALVE', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024BA01', 'machine_name': 'BAG APPLICATOR', 'points': 1, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024RA01', 'machine_name': 'ROTARY FEEDER LINE 4', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024CV01', 'machine_name': 'CHAIN CONVEYOR', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024RY01', 'machine_name': 'ROTARY SCREEN', 'points': 2, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024BF01', 'machine_name': 'SMALL BAG FILTER 1', 'points': 2, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024FN01', 'machine_name': 'SMALL BAG FILTER FAN 1', 'points': 2, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024BF02', 'machine_name': 'SMALL BAG FILTER 2', 'points': 2, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024FN02', 'machine_name': 'SMALL BAG FILTER FAN 2', 'points': 2, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024PM01', 'machine_name': 'PACKER MACHINE 4', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024BC01', 'machine_name': 'BELT CONVEYOR 1', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024NS01', 'machine_name': 'BELT BAG CLEANER', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024BC02', 'machine_name': 'BELT CONVEYOR 2', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024CW01', 'machine_name': 'BELT CHECK WEIGHT', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024BR01', 'machine_name': 'BELT REJECT', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024BC03', 'machine_name': 'BELT CONVEYOR 3', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024GK01', 'machine_name': 'ROLLER CURVE 1', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024BC04', 'machine_name': 'BELT CONVEYOR 4', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024GK02', 'machine_name': 'ROLLER CURVE 2', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N60242BC05', 'machine_name': 'BELT CONVEYOR 5', 'points': 4, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024YD01', 'machine_name': 'BELT DIVERTER', 'points': 2, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024GK03', 'machine_name': 'ROLLER CURVE 3', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024BC06', 'machine_name': 'BELT CONVEYOR 6', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024RB01', 'machine_name': 'GRAVITY ROLLER', 'points': 3, 'area': 'PH LINE 4'},
 {'machine_id': 'N6024PA01', 'machine_name': 'PALLETIZER 4', 'points': 1, 'area': 'PH LINE 4'},
 {'machine_id': 'N6025BE01', 'machine_name': 'BUCKET ELEVATOR LINE 5', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025VC01', 'machine_name': 'VIBRATING CONVEYOR LINE 5', 'points': 2, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025SG01', 'machine_name': 'THROTTLE VALVE', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025BA01', 'machine_name': 'BAG APPLICATOR', 'points': None, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025RA01', 'machine_name': 'ROTARY FEEDER LINE 5', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025CV01', 'machine_name': 'CHAIN CONVEYOR', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025RY01', 'machine_name': 'ROTARY SCREEN', 'points': 2, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025BF01', 'machine_name': 'SMALL BAG FILTER 1', 'points': 2, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025FN01', 'machine_name': 'SMALL BAG FILTER FAN 1', 'points': 2, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025BF02', 'machine_name': 'SMALL BAG FILTER 2', 'points': 2, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025FN02', 'machine_name': 'SMALL BAG FILTER FAN 2', 'points': 2, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025PM01', 'machine_name': 'PACKER MACHINE 5', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025BC01', 'machine_name': 'BELT CONVEYOR 1', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025NS01', 'machine_name': 'BELT BAG CLEANER', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025BC02', 'machine_name': 'BELT CONVEYOR 2', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025CW01', 'machine_name': 'BELT CHECK WEIGHT', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025BR01', 'machine_name': 'BELT REJECT', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025BC03', 'machine_name': 'BELT CONVEYOR 3', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025GK01', 'machine_name': 'ROLLER CURVE 1', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025BC04', 'machine_name': 'BELT CONVEYOR 4', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025GK02', 'machine_name': 'ROLLER CURVE 2', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N60252BC05', 'machine_name': 'BELT CONVEYOR 5', 'points': 4, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025YD01', 'machine_name': 'BELT DIVERTER', 'points': 2, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025GK03', 'machine_name': 'ROLLER CURVE 3', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025BC06', 'machine_name': 'BELT CONVEYOR 6', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025RB01', 'machine_name': 'GRAVITY ROLLER', 'points': 3, 'area': 'PH LINE 5'},
 {'machine_id': 'N6025PA01', 'machine_name': 'PALLETIZER 5', 'points': 1, 'area': 'PH LINE 5'}]

WORKING_TO_LOTOTO = {'N6021BE01': ['N6021BE01', 'N6021VC01', 'N6021CV01'],
 'N6021VC01': ['N6021BE01', 'N6021VC01'],
 'N6021SG01': ['N6021VC01', 'N6021SG01', 'N6021RA01'],
 'N6021BA01': ['N6021BA01'],
 'N6021RA01': ['N6021SG01', 'N6021RA01', 'N6021PM01'],
 'N6021CV01': ['N6021BE01', 'N6021CV01', 'N6021RY01'],
 'N6021RY01': ['N6021RY01', 'N6021BR01'],
 'N6021BF01': ['N6021BF01', 'N6021FN01'],
 'N6021FN01': ['N6021BF01', 'N6021FN01'],
 'N6021BF02': ['N6021BF02', 'N6021FN02'],
 'N6021FN02': ['N6021BF02', 'N6021FN02'],
 'N6021PM01': ['N6021RA01', 'N6021PM01', 'N6021BC01'],
 'N6021BC01': ['N6021PM01', 'N6021BC01', 'N6021NS01'],
 'N6021NS01': ['N6021BC01', 'N6021NS01', 'N6021BC02'],
 'N6021BC02': ['N6021NS01', 'N6021BC02', 'N6021CW01'],
 'N6021CW01': ['N6021BC02', 'N6021CW01', 'N6021BR01'],
 'N6021BR01': ['N6021CW01', 'N6021BR01', 'N6021BC03'],
 'N6021BC03': ['N6021BR01', 'N6021BC03'],
 'N6021YD01': ['N6021BC03', 'N6021YD01'],
 'N6021BC04': ['N6021BC03', 'N6021BC04', 'N6021RB01'],
 'N6021RB01': ['N6021BC04', 'N6021RB01', 'N6021PA01'],
 'N6021PA01': ['N6021PA01'],
 'N6021GK01': ['N6021BC03', 'N6021GK01'],
 'N6022BE01': ['N6022BE01', 'N6022VC01', 'N6022CV01'],
 'N6022VC01': ['N6022BE01', 'N6022VC01'],
 'N6022SG01': ['N6022VC01', 'N6022SG01', 'N6022RA01'],
 'N6022BA01': ['N6022BA01'],
 'N6022RA01': ['N6022SG01', 'N6022RA01', 'N6022PM01'],
 'N6022CV01': ['N6022BE01', 'N6022CV01', 'N6022RY01'],
 'N6022RY01': ['N6022RY01', 'N6022BR01'],
 'N6022BF01': ['N6022BF01', 'N6022FN01'],
 'N6022FN01': ['N6022BF01', 'N6022FN01'],
 'N6022BF02': ['N6022BF02', 'N6022FN02'],
 'N6022FN02': ['N6022BF02', 'N6022FN02'],
 'N6022PM01': ['N6022RA01', 'N6022PM01', 'N6022BC01'],
 'N6022BC01': ['N6022PM01', 'N6022BC01', 'N6022NS01'],
 'N6022NS01': ['N6022BC01', 'N6022NS01', 'N6022BC02'],
 'N6022BC02': ['N6022NS01', 'N6022BC02', 'N6022CW01'],
 'N6022CW01': ['N6022BC02', 'N6022CW01', 'N6022BR01'],
 'N6022BR01': ['N6022CW01', 'N6022BR01', 'N6022BC03'],
 'N6022BC03': ['N6022BR01', 'N6022BC03', 'N6022GK01'],
 'N6022GK01': ['N6022BC03', 'N6022GK01', 'N6022BC04'],
 'N6022BC04': ['N6022GK01', 'N6022BC04', 'N6022GK02'],
 'N6022GK02': ['N6022BC04', 'N6022GK02', 'N60222BC05'],
 'N60222BC05': ['N6022GK02', 'N60222BC05', 'N6022YD01', 'N6022GK03'],
 'N6022YD01': ['N60222BC05', 'N6022YD01'],
 'N6022GK03': ['N60222BC05', 'N6022GK03', 'N6022BC06'],
 'N6022BC06': ['N6022GK03', 'N6022BC06', 'N6022RB01'],
 'N6022RB01': ['N6022BC06', 'N6022RB01', 'N6022PA01'],
 'N6022PA01': ['N6022PA01'],
 'N6023BE01': ['N6023BE01', 'N6023VC01', 'N6023CV01'],
 'N6023VC01': ['N6023BE01', 'N6023VC01'],
 'N6023SG01': ['N6023VC01', 'N6023SG01', 'N6023RA01'],
 'N6023BA01': ['N6023BA01'],
 'N6023RA01': ['N6023SG01', 'N6023RA01', 'N6023PM01'],
 'N6023CV01': ['N6023BE01', 'N6023CV01', 'N6023RY01'],
 'N6023RY01': ['N6023RY01', 'N6023BR01'],
 'N6023BF01': ['N6023BF01', 'N6023FN01'],
 'N6023FN01': ['N6023BF01', 'N6023FN01'],
 'N6023BF02': ['N6023BF02', 'N6023FN02'],
 'N6023FN02': ['N6023BF02', 'N6023FN02'],
 'N6023PM01': ['N6023RA01', 'N6023PM01', 'N6023BC01'],
 'N6023BC01': ['N6023PM01', 'N6023BC01', 'N6023NS01'],
 'N6023NS01': ['N6023BC01', 'N6023NS01', 'N6023BC02'],
 'N6023BC02': ['N6023NS01', 'N6023BC02', 'N6023CW01'],
 'N6023CW01': ['N6023BC02', 'N6023CW01', 'N6023BR01'],
 'N6023BR01': ['N6023CW01', 'N6023BR01', 'N6023BC03'],
 'N6023BC03': ['N6023BR01', 'N6023BC03', 'N6023GK01'],
 'N6023GK01': ['N6023BC03', 'N6023GK01', 'N6023BC04'],
 'N6023BC04': ['N6023GK01', 'N6023BC04', 'N6023GK02'],
 'N6023GK02': ['N6023BC04', 'N6023GK02', 'N60232BC05'],
 'N60232BC05': ['N6023GK02', 'N60232BC05', 'N6023YD01', 'N6023GK03'],
 'N6023YD01': ['N60232BC05', 'N6023YD01'],
 'N6023GK03': ['N60232BC05', 'N6023GK03', 'N6023BC06'],
 'N6023BC06': ['N6023GK03', 'N6023BC06', 'N6023RB01'],
 'N6023RB01': ['N6023BC06', 'N6023RB01', 'N6023PA01'],
 'N6023PA01': ['N6023PA01'],
 'N6024BE01': ['N6024BE01', 'N6024VC01', 'N6024CV01'],
 'N6024VC01': ['N6024BE01', 'N6024VC01'],
 'N6024SG01': ['N6024VC01', 'N6024SG01', 'N6024RA01'],
 'N6024BA01': ['N6024BA01'],
 'N6024RA01': ['N6024SG01', 'N6024RA01', 'N6024PM01'],
 'N6024CV01': ['N6024BE01', 'N6024CV01', 'N6024RY01'],
 'N6024RY01': ['N6024RY01', 'N6024BR01'],
 'N6024BF01': ['N6024BF01', 'N6024FN01'],
 'N6024FN01': ['N6024BF01', 'N6024FN01'],
 'N6024BF02': ['N6024BF02', 'N6024FN02'],
 'N6024FN02': ['N6024BF02', 'N6024FN02'],
 'N6024PM01': ['N6024RA01', 'N6024PM01', 'N6024BC01'],
 'N6024BC01': ['N6024PM01', 'N6024BC01', 'N6024NS01'],
 'N6024NS01': ['N6024BC01', 'N6024NS01', 'N6024BC02'],
 'N6024BC02': ['N6024NS01', 'N6024BC02', 'N6024CW01'],
 'N6024CW01': ['N6024BC02', 'N6024CW01', 'N6024BR01'],
 'N6024BR01': ['N6024CW01', 'N6024BR01', 'N6024BC03'],
 'N6024BC03': ['N6024BR01', 'N6024BC03', 'N6024GK01'],
 'N6024GK01': ['N6024BC03', 'N6024GK01', 'N6024BC04'],
 'N6024BC04': ['N6024GK01', 'N6024BC04', 'N6024GK02'],
 'N6024GK02': ['N6024BC04', 'N6024GK02', 'N60242BC05'],
 'N60242BC05': ['N6024GK02', 'N60242BC05', 'N6024YD01', 'N6024GK03'],
 'N6024YD01': ['N60242BC05', 'N6024YD01'],
 'N6024GK03': ['N60242BC05', 'N6024GK03', 'N6024BC06'],
 'N6024BC06': ['N6024GK03', 'N6024BC06', 'N6024RB01'],
 'N6024RB01': ['N6024BC06', 'N6024RB01', 'N6024PA01'],
 'N6024PA01': ['N6024PA01'],
 'N6025BE01': ['N6024BE01', 'N6024VC01', 'N6024CV01'],
 'N6025VC01': ['N6024BE01', 'N6024VC01'],
 'N6025SG01': ['N6024VC01', 'N6024SG01', 'N6024RA01'],
 'N6025BA01': [],
 'N6025RA01': ['N6024SG01', 'N6024RA01', 'N6024PM01'],
 'N6025CV01': ['N6024BE01', 'N6024CV01', 'N6024RY01'],
 'N6025RY01': ['N6024RY01', 'N6024BR01'],
 'N6025BF01': ['N6024BF01', 'N6024FN01'],
 'N6025FN01': ['N6024BF01', 'N6024FN01'],
 'N6025BF02': ['N6024BF02', 'N6024FN02'],
 'N6025FN02': ['N6024BF02', 'N6024FN02'],
 'N6025PM01': ['N6024RA01', 'N6024PM01', 'N6024BC01'],
 'N6025BC01': ['N6024PM01', 'N6024BC01', 'N6024NS01'],
 'N6025NS01': ['N6024BC01', 'N6024NS01', 'N6024BC02'],
 'N6025BC02': ['N6024NS01', 'N6024BC02', 'N6024CW01'],
 'N6025CW01': ['N6024BC02', 'N6024CW01', 'N6024BR01'],
 'N6025BR01': ['N6024CW01', 'N6024BR01', 'N6024BC03'],
 'N6025BC03': ['N6024BR01', 'N6024BC03', 'N6024GK01'],
 'N6025GK01': ['N6024BC03', 'N6024GK01', 'N6024BC04'],
 'N6025BC04': ['N6024GK01', 'N6024BC04', 'N6024GK02'],
 'N6025GK02': ['N6024BC04', 'N6024GK02', 'N60242BC05'],
 'N60252BC05': ['N6024GK02', 'N60242BC05', 'N6024YD01', 'N6024GK03'],
 'N6025YD01': ['N60242BC05', 'N6024YD01'],
 'N6025GK03': ['N60242BC05', 'N6024GK03', 'N6024BC06'],
 'N6025BC06': ['N6024GK03', 'N6024BC06', 'N6024RB01'],
 'N6025RB01': ['N6024BC06', 'N6024RB01', 'N6024PA01'],
 'N6025PA01': ['N6024PA01']}

@st.cache_resource(show_spinner=False)
def seed_working_equipment():
    """Seed machine master and all Working-to-LOTOTO relationships once per app process."""
    seed_cursor = conn.cursor()
    for item in WORKING_EQUIPMENT_CATALOG:
        seed_cursor.execute(
            """
            INSERT INTO public.machines
                (machine_id, machine_name, area, energy_source, isolation_point, status, tag_padlock_total)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (machine_id) DO UPDATE SET
                machine_name = EXCLUDED.machine_name,
                area = EXCLUDED.area,
                tag_padlock_total = EXCLUDED.tag_padlock_total
            """,
            (item["machine_id"], item["machine_name"], item["area"],
             "Perlu verifikasi lapangan",
             "Mengacu LOTOTO Matrix; verifikasi titik isolasi di lapangan",
             "AVAILABLE", item["points"])
        )
    seed_cursor.execute("DELETE FROM public.equipment_lototo_matrix")
    for working_id, lototo_ids in WORKING_TO_LOTOTO.items():
        for lototo_id in lototo_ids:
            seed_cursor.execute(
                """
                INSERT INTO public.equipment_lototo_matrix
                    (working_machine_id, lototo_machine_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (working_id, lototo_id)
            )
    conn.commit()
    seed_cursor.close()

# ============================================================
# USER AUTHENTICATION (Sign Up / Sign In)
# Passwords are stored as PBKDF2-HMAC-SHA256 hashes, never as plain text.
# ============================================================
AUTH_ITERATIONS = 310_000


def hash_user_password(password: str, salt_hex: str | None = None):
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, AUTH_ITERATIONS
    )
    return salt.hex(), digest.hex()


def verify_user_password(password: str, salt_hex: str, expected_hash: str) -> bool:
    _, candidate_hash = hash_user_password(password, salt_hex)
    return hmac.compare_digest(candidate_hash, expected_hash)


def create_app_user(username: str, full_name: str, password: str):
    salt_hex, password_hash = hash_user_password(password)
    auth_cursor = conn.cursor()
    try:
        auth_cursor.execute(
            """INSERT INTO public.app_users
               (username, full_name, password_hash, password_salt)
               VALUES (%s, %s, %s, %s)""",
            (username, full_name, password_hash, salt_hex)
        )
        conn.commit()
        return True, "Akun berhasil dibuat. Silakan sign in."
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "Username sudah digunakan. Silakan pilih username lain."
    except Exception:
        conn.rollback()
        raise
    finally:
        auth_cursor.close()


def authenticate_app_user(username: str, password: str):
    auth_cursor = conn.cursor()
    try:
        auth_cursor.execute(
            """SELECT id, username, full_name, password_hash, password_salt
               FROM public.app_users
               WHERE username = %s AND is_active = TRUE""",
            (username,)
        )
        user_row = auth_cursor.fetchone()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        auth_cursor.close()

    if not user_row:
        return None
    if not verify_user_password(password, user_row[4], user_row[3]):
        return None
    return {"id": user_row[0], "username": user_row[1], "full_name": user_row[2]}


if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    left_space, hero_col, auth_col, right_space = st.columns([0.45, 1.0, 1.05, 0.45], gap="large")
    with hero_col:
        st.markdown("""
        <div class="lototo-login-hero">
          <div>
            <div class="eyebrow">SAFETY • CONTROL • COMPLIANCE</div>
            <h2>LOTOTO<br>Safety System</h2>
            <p>Energy isolation management untuk membantu memastikan setiap pekerjaan dilakukan dengan proses isolasi energi yang terkontrol.</p>
          </div>
          <div class="hero-foot">🔒 Lock Out&nbsp;&nbsp; • &nbsp;&nbsp;🏷️ Tag Out&nbsp;&nbsp; • &nbsp;&nbsp;⚙️ Try Out</div>
        </div>
        """, unsafe_allow_html=True)
    with auth_col:
        st.markdown("## Welcome")
        st.caption("Masuk ke akun Anda atau buat akun baru untuk melanjutkan.")
        login_tab, signup_tab = st.tabs(["Sign In", "Create Account"])

        with login_tab:
            with st.form("lototo_signin_form", clear_on_submit=False):
                login_username = st.text_input("Username", key="signin_username")
                login_password = st.text_input("Password", type="password", key="signin_password")
                login_submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            if login_submit:
                if not login_username.strip() or not login_password:
                    st.error("Masukkan username dan password.")
                else:
                    try:
                        logged_user = authenticate_app_user(login_username.strip().lower(), login_password)
                        if logged_user:
                            st.session_state.authenticated_user = logged_user
                            st.success("Sign in berhasil. Membuka aplikasi LOTOTO...")
                            st.rerun()
                        else:
                            st.error("Username atau password salah, atau akun tidak aktif.")
                    except Exception as exc:
                        st.error(f"Gagal memeriksa akun: {exc}")

        with signup_tab:
            with st.form("lototo_signup_form", clear_on_submit=True):
                signup_name = st.text_input("Nama lengkap", key="signup_full_name")
                signup_username = st.text_input("Buat username", key="signup_username")
                signup_password = st.text_input("Buat password", type="password", key="signup_password")
                signup_confirm = st.text_input("Konfirmasi password", type="password", key="signup_confirm")
                signup_submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            if signup_submit:
                clean_name = signup_name.strip()
                clean_username = signup_username.strip().lower()
                if not clean_name or not clean_username or not signup_password:
                    st.error("Semua kolom wajib diisi.")
                elif len(clean_username) < 4 or not clean_username.replace("_", "").replace(".", "").isalnum():
                    st.error("Username minimal 4 karakter; gunakan huruf, angka, titik, atau underscore.")
                elif len(signup_password) < 10:
                    st.error("Password minimal 10 karakter.")
                elif signup_password != signup_confirm:
                    st.error("Konfirmasi password tidak cocok.")
                else:
                    try:
                        created, message = create_app_user(clean_username, clean_name, signup_password)
                        if created:
                            st.success(message + " Silakan buka tab Sign In.")
                        else:
                            st.error(message)
                    except Exception as exc:
                        st.error(f"Gagal membuat akun: {exc}")

    st.markdown(
        "<div style='text-align:center;color:#8094a0;font-size:.78rem;margin-top:1.1rem;'>"
        "LSR 6 • Energy Isolation Management</div>",
        unsafe_allow_html=True
    )
    st.stop()

# User is authenticated; only now seed equipment data and expose app navigation.
seed_working_equipment()


def get_mapped_equipment(working_machine_id):
    mapping_cursor = conn.cursor()
    mapping_cursor.execute(
        """
        SELECT lototo_machine_id
        FROM public.equipment_lototo_matrix
        WHERE working_machine_id = %s
        ORDER BY lototo_machine_id
        """,
        (str(working_machine_id),)
    )
    mapped = [row[0] for row in mapping_cursor.fetchall()]
    conn.commit()
    mapping_cursor.close()
    return mapped

def get_equipment_items(lototo_id):
    return read_sql_df(
        """
        SELECT ei.*, m.machine_name, m.tag_padlock_total
        FROM public.lototo_equipment_items ei
        LEFT JOIN public.machines m ON m.machine_id = ei.equipment_machine_id
        WHERE ei.lototo_id = %s ORDER BY m.machine_name
        """, params=(lototo_id,)
    )

def ensure_lototo_equipment_items(lototo_id, working_machine_id, started_at):
    """
    Pastikan hanya Equipment for LOTOTO yang identik dengan Equipment for
    Working (ID dan nama sama) yang dibuat sebagai item LOTOTO.

    Jika Equipment for Working lain juga memetakan Equipment for LOTOTO
    identik tersebut, statusnya akan terlihat pada baris Equipment for LOTOTO
    yang sama di Matrix melalui status global per equipment_machine_id.
    Equipment LOTOTO lain milik Working tersebut tidak otomatis diaktifkan.
    """
    state_cursor = conn.cursor()
    state_cursor.execute(
        "SELECT work_status, end_time FROM public.lototo WHERE id = %s",
        (lototo_id,)
    )
    parent_state = state_cursor.fetchone()
    if not parent_state:
        conn.commit()
        state_cursor.close()
        return

    working_id = str(working_machine_id)
    mapped_ids = {str(item) for item in get_mapped_equipment(working_id)}

    # Identitas harus cocok pada ID dan nama master.
    # ID yang sama merujuk satu nama master yang sama di tabel machines.
    state_cursor.execute(
        """
        SELECT machine_id, machine_name
        FROM public.machines
        WHERE machine_id = %s
        """,
        (working_id,)
    )
    working_machine = state_cursor.fetchone()

    if working_machine and working_id in mapped_ids:
        working_machine_name = str(working_machine[1]).strip()
        state_cursor.execute(
            """
            SELECT machine_id
            FROM public.machines
            WHERE machine_id = %s
              AND TRIM(machine_name) = %s
            """,
            (working_id, working_machine_name)
        )
        identical_lototo = state_cursor.fetchone()

        if identical_lototo:
            parent_status, parent_end_time = parent_state
            child_status = "COMPLETED" if parent_status == "COMPLETED" else "ACTIVE"
            state_cursor.execute(
                """
                INSERT INTO public.lototo_equipment_items
                    (lototo_id, working_machine_id, equipment_machine_id,
                     status, started_at, ended_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (lototo_id, equipment_machine_id) DO NOTHING
                """,
                (lototo_id, working_id, working_id, child_status,
                 started_at, parent_end_time)
            )

    conn.commit()
    state_cursor.close()


# ============================================================
# HEADER
# ============================================================

# Safety guard: Streamlit can recreate session state when a browser session
# changes. Never access authenticated_user as a dictionary unless it exists.
current_user = st.session_state.get("authenticated_user")
if not isinstance(current_user, dict) or not current_user.get("full_name"):
    # Fail closed: an invalid session must not access protected pages.
    st.session_state["authenticated_user"] = None
    st.info("Sesi login tidak ditemukan atau sudah berakhir. Silakan sign in kembali.")
    st.stop()

# Defensive display value; sidebar never indexes or calls .get() on None.
sidebar_user_name = (
    current_user.get("full_name", "User")
    if isinstance(current_user, dict)
    else "User"
)

st.sidebar.markdown("""
<div class="lototo-brand">
  <div class="brand-kicker">Safety Management</div>
  <div class="brand-title">🔒 LOTOTO</div>
  <div class="brand-sub">LSR 6 • Energy Isolation</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("**SIGNED IN AS**")
st.sidebar.markdown(f"👤 {sidebar_user_name}")
if st.sidebar.button("Sign Out", use_container_width=True):
    st.session_state.authenticated_user = None
    st.query_params.clear()
    st.rerun()

st.sidebar.markdown(
    "<div style='font-size:.72rem;font-weight:850;color:#6d8795;"
    "letter-spacing:.12em;margin:18px 0 5px;'>WORKSPACE MENU</div>",
    unsafe_allow_html=True
)
menu = st.sidebar.selectbox(
    "Pilih halaman",
    [
        "Dashboard",
        "Data Mesin",
        "Start LOTOTO",
        "LOTOTO Matrix",
        "Active LOTOTO",
        "End LOTOTO",
        "History"
    ]
)


def render_open_detail_buttons(dataframe, key_prefix="detail"):
    """Render Open Detail buttons that navigate within the current app tab."""
    if dataframe.empty:
        return
    header = st.columns([0.55, 1.0, 1.0, 1.0, 1.0])
    header[0].markdown("**Detail**")
    for idx, (_, row) in enumerate(dataframe.iterrows()):
        cols = st.columns([0.55, 1.0, 1.0, 1.0, 1.0])
        record_id = int(row["id"])
        if cols[0].button("Open", key=f"{key_prefix}_{record_id}_{idx}"):
            st.session_state["detail_return_menu"] = st.session_state.get("Menu", "Active LOTOTO")
            st.query_params["page"] = "detail"
            st.query_params["id"] = str(record_id)
            st.rerun()
        cols[1].write(str(row.get("work_order", "-")))
        cols[2].write(str(row.get("machine_id", "-")))
        cols[3].write(str(row.get("technician", "-")))
        cols[4].write(str(row.get("work_status", "-")))


# ============================================================
# HYPERLINK DETAIL PAGE
# ============================================================

query_params = st.query_params
detail_page = query_params.get("page")
detail_id = query_params.get("id")

if detail_page == "detail" and detail_id:

    try:
        detail_id = int(detail_id)
    except ValueError:
        detail_id = None

    if detail_id is not None:

        detail = read_sql_df(
            """
            SELECT *
            FROM lototo
            WHERE id = %s
            """,
            params=(detail_id,)
        )

        if len(detail):

            selected = detail.iloc[0]

            st.title("🔎 LOTOTO Detail")
            st.caption(
                "Detail record dari Active LOTOTO / History"
            )

            if st.button("← Kembali"):
                st.query_params.clear()
                st.rerun()

            st.divider()

            c1, c2, c3 = st.columns(3)

            c1.metric("Work Order", selected["work_order"])
            c2.metric("Machine", selected["machine_id"])
            c3.metric("Status", selected["work_status"])

            st.write(
                f"**Technician:** {selected['technician']}"
            )
            st.write(
                f"**Start:** {selected['start_time']}"
            )
            st.write(
                f"**End:** {selected['end_time'] or '-'}"
            )

            if selected["end_time"]:
                st.write(
                    f"**Duration:** "
                    f"{duration_between(selected['start_time'], selected['end_time'])}"
                )

            st.divider()

            st.subheader("🟨 Equipment for LOTOTO")
            ensure_lototo_equipment_items(detail_id, str(selected["machine_id"]), selected["start_time"])
            detail_equipment_state = get_equipment_items(detail_id)
            if not detail_equipment_state.empty:
                detail_equipment_view = detail_equipment_state[[
                    "equipment_machine_id", "machine_name", "status", "started_at", "ended_at"
                ]].copy()
                detail_equipment_view.columns = ["Equipment ID", "Equipment for LOTOTO", "Status", "Start", "End"]
                detail_equipment_view["Status"] = detail_equipment_view["Status"].map(
                    {"ACTIVE": "🟢 ACTIVE / TERISOLASI", "COMPLETED": "⚪ ENDED"}
                ).fillna(detail_equipment_view["Status"])
                st.dataframe(detail_equipment_view, use_container_width=True, hide_index=True)

            st.divider()

            st.subheader("📋 LSR 6 Checklist")

            checklist = [
                ("1. Identifikasi sumber energi", selected["energy_identified"]),
                ("2. Beritahukan pihak terkait", selected["parties_notified"]),
                ("3. Matikan / isolasi sumber energi", selected["shutdown_isolated"]),
                ("4. Lock Out", selected["lock_out"]),
                ("5. Tag Out", selected["tag_out"]),
                ("6. Try Out", selected["try_out"]),
                ("7. Periksa dan mengembalikan seperti semula", selected["checked_restored"]),
            ]

            for label, value in checklist:
                if value:
                    st.success(f"✅ {label}")
                else:
                    st.warning(f"⬜ {label}")

            st.divider()

            st.subheader("📷 Start Evidence")

            c1, c2 = st.columns(2)

            with c1:
                st.write("🔒 Lock Out")
                if evidence_exists(selected["lock_photo"]):
                    show_evidence(selected["lock_photo"], width=400)
                    st.caption(
                        f"Evidence time: {selected['lock_photo_time']}"
                    )
                else:
                    st.info("Tidak tersedia.")

            with c2:
                st.write("🏷️ Tag Out")
                if evidence_exists(selected["tag_photo"]):
                    show_evidence(selected["tag_photo"], width=400)
                    st.caption(
                        f"Evidence time: {selected['tag_photo_time']}"
                    )
                else:
                    st.info("Tidak tersedia.")

            st.divider()

            st.subheader("📄 Step 2 Evidence - JSA / DRA / PTW / Safety Briefing")

            e1, e2, e3, e4 = st.columns(4)

            for column, label, field, time_field in [
                (e1, "JSA", "jsa_photo", "jsa_photo_time"),
                (e2, "DRA", "dra_photo", "dra_photo_time"),
                (e3, "PTW", "ptw_photo", "ptw_photo_time"),
                (e4, "Safety Briefing", "safety_briefing_photo", "safety_briefing_photo_time"),
            ]:
                with column:
                    st.write(f"**{label}**")
                    if evidence_exists(selected[field]):
                        show_evidence(selected[field], width=260)
                        st.caption(f"Evidence time: {selected[time_field]}")
                    else:
                        st.info("Tidak tersedia.")

            st.divider()

            st.subheader("📄 PTW & Safety Briefing")
            st.write(f"**Jenis PTW:** {selected['ptw_type'] or '-'}")
            st.write(f"**Nomor PTW:** {selected['ptw_number'] or '-'}")
            # Foto PTW dan Safety Briefing sudah ditampilkan pada bagian Start Evidence.
            # Bagian ini hanya menampilkan informasi PTW agar foto tidak duplikat.

            st.divider()

            st.subheader("📷 End Evidence - Lock Out / Tag Out")

            c1, c2 = st.columns(2)

            with c1:
                st.write("🔒 End Lock Out")
                if evidence_exists(selected["end_lock_photo"]):
                    show_evidence(selected["end_lock_photo"], width=400)
                    st.caption(
                        f"Evidence time: {selected['end_lock_photo_time']}"
                    )
                else:
                    st.info("Belum ada evidence End Lock Out.")

            with c2:
                st.write("🏷️ End Tag Out")
                if evidence_exists(selected["end_tag_photo"]):
                    show_evidence(selected["end_tag_photo"], width=400)
                    st.caption(
                        f"Evidence time: {selected['end_tag_photo_time']}"
                    )
                else:
                    st.info("Belum ada evidence End Tag Out.")

            # --------------------------------------------------------
            # END LOTOTO FROM DETAIL
            # Active records can be ended directly from Open Detail.
            # The same detail page can be opened from both Active and
            # End LOTOTO menus, so there are two navigation paths to
            # the same End LOTOTO process.
            # --------------------------------------------------------
            if selected["work_status"] == "ACTIVE":

                st.divider()
                st.subheader("⏹️ End LOTOTO per Equipment for LOTOTO")
                st.caption("Semua Equipment for LOTOTO yang masih ACTIVE pada aktivitas ini akan di-END.")

                ensure_lototo_equipment_items(detail_id, str(selected["machine_id"]), selected["start_time"])
                equipment_state = get_equipment_items(detail_id)
                active_equipment = equipment_state[equipment_state["status"] == "ACTIVE"].copy()

                if not active_equipment.empty:
                    # Tidak perlu menampilkan pilihan Equipment for LOTOTO.
                    # Semua item ACTIVE yang terikat pada aktivitas ini diproses saat END.
                    selected_to_end = active_equipment["equipment_machine_id"].astype(str).tolist()
                    with st.form(f"end_lototo_detail_{detail_id}"):
                        end_lock_photo = st.file_uploader(
                            "📷 Upload Foto End Lock Out", type=["jpg", "jpeg", "png"],
                            key=f"detail_end_lock_{detail_id}"
                        )
                        end_tag_photo = st.file_uploader(
                            "📷 Upload Foto End Tag Out", type=["jpg", "jpeg", "png"],
                            key=f"detail_end_tag_{detail_id}"
                        )
                        checked_restored = st.checkbox(
                            "LSR 6 Step 7 telah diperiksa dan proses pengembalian dilakukan sesuai prosedur.",
                            key=f"detail_checked_restored_{detail_id}"
                        )
                        confirmation = st.checkbox(
                            "Saya memastikan equipment yang dipilih telah selesai dan aman untuk END.",
                            key=f"detail_end_confirmation_{detail_id}"
                        )
                        end_button = st.form_submit_button("⏹️ END LOTOTO")

                    if end_button:
                        if end_lock_photo is None or end_tag_photo is None:
                            st.error("Foto End Lock Out dan End Tag Out wajib diupload.")
                        elif not checked_restored:
                            st.error("LSR 6 Step 7 belum diverifikasi.")
                        elif not confirmation:
                            st.error("Konfirmasi END belum dilakukan.")
                        else:
                            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            end_paths = save_uploaded_files_parallel(
                                [("END_LOCK", end_lock_photo), ("END_TAG", end_tag_photo)],
                                selected["work_order"], max_workers=2
                            )
                            for equipment_id in selected_to_end:
                                cursor.execute(
                                    """
                                    UPDATE public.lototo_equipment_items
                                    SET status = 'COMPLETED', ended_at = %s,
                                        end_lock_photo = %s, end_tag_photo = %s,
                                        end_evidence_time = %s
                                    WHERE lototo_id = %s AND equipment_machine_id = %s
                                      AND status = 'ACTIVE'
                                    """,
                                    (end_time, end_paths["END_LOCK"], end_paths["END_TAG"],
                                     end_time, detail_id, equipment_id)
                                )

                            cursor.execute(
                                "SELECT COUNT(*) FROM public.lototo_equipment_items WHERE lototo_id = %s AND status = 'ACTIVE'",
                                (detail_id,)
                            )
                            remaining_active = cursor.fetchone()[0]
                            if remaining_active == 0:
                                cursor.execute(
                                    """
                                    UPDATE public.lototo
                                    SET end_time = %s, checked_restored = 1,
                                        end_confirmation = 1, end_lock_photo = %s,
                                        end_tag_photo = %s, end_lock_photo_time = %s,
                                        end_tag_photo_time = %s,
                                        lototo_status = 'LSR 6 COMPLETE',
                                        work_status = 'COMPLETED'
                                    WHERE id = %s
                                    """,
                                    (end_time, end_paths["END_LOCK"], end_paths["END_TAG"],
                                     end_time, end_time, detail_id)
                                )
                            else:
                                cursor.execute(
                                    """
                                    UPDATE public.lototo
                                    SET end_lock_photo = %s, end_tag_photo = %s,
                                        end_lock_photo_time = %s, end_tag_photo_time = %s
                                    WHERE id = %s
                                    """,
                                    (end_paths["END_LOCK"], end_paths["END_TAG"],
                                     end_time, end_time, detail_id)
                                )
                            conn.commit()
                            if remaining_active == 0:
                                st.success("Semua Equipment for LOTOTO sudah ENDED. Working equipment selesai.")
                            else:
                                st.warning(f"{len(selected_to_end)} equipment berhasil di-END. {remaining_active} equipment lainnya masih ACTIVE.")
                            st.rerun()
                else:
                    st.success("Semua Equipment for LOTOTO sudah ENDED.")

                st.subheader("Status Equipment for LOTOTO")
                state_display = equipment_state[[
                    "equipment_machine_id", "machine_name", "status", "started_at", "ended_at"
                ]].copy()
                state_display.columns = ["Equipment ID", "Equipment for LOTOTO", "Status", "Start", "End"]
                state_display["Status"] = state_display["Status"].map(
                    {"ACTIVE": "🟢 ACTIVE", "COMPLETED": "⚪ ENDED"}
                ).fillna(state_display["Status"])
                st.dataframe(state_display, use_container_width=True, hide_index=True)

            st.stop()

        else:
            st.error("Record LOTOTO tidak ditemukan.")
            st.stop()


# ============================================================
# DASHBOARD
# ============================================================

if menu == "Dashboard":

    st.title("🔒 LSR 6 - LOTOTO Dashboard")
    st.caption("Isolasi Energi - Lock Out, Tag Out & Try Out")

    machines = get_machines()
    records = get_lototo()
    active = get_active_lototo()

    total_machine = len(machines)
    total_lototo = len(records)
    total_active = len(active)

    # Dashboard intentionally focuses on current workload.
    # Completed and compliance are available from History instead.

    col1, col2, col3 = st.columns(3)

    col1.metric("🏭 Total Mesin", total_machine)
    col2.metric("📋 Total LOTOTO", total_lototo)
    col3.metric("🔴 Active", total_active)

    st.divider()

    st.subheader("🔴 Active LOTOTO")

    if len(active):
        display = active[
            [
                "id",
                "work_order",
                "machine_id",
                "technician",
                "ptw_type",
                "ptw_number",
                "start_time",
                "lototo_status",
                "work_status"
            ]
        ].copy()

        display["Work Order"] = display["id"].apply(
            lambda x: f"?page=detail&id={x}"
        )

        display = display[
            [
                "id",
                "Work Order",
                "machine_id",
                "technician",
                "ptw_type",
                "ptw_number",
                "start_time",
                "lototo_status",
                "work_status"
            ]
        ]

        display.columns = [
            "ID",
            "Work Order",
            "Machine",
            "Technician",
            "PTW Type",
            "PTW No.",
            "Start Time",
            "LSR 6 Status",
            "Work Status"
        ]

        st.dataframe(
            display.drop(columns=["Work Order"], errors="ignore"),
            hide_index=True,
            use_container_width=True
        )
        st.caption("Buka detail pada tab aplikasi yang sama:")
        render_open_detail_buttons(
            active,
            key_prefix="open_detail"
        )
    else:
        st.success("Tidak ada pekerjaan LOTOTO yang sedang aktif.")


# ============================================================
# DATA MESIN
# ============================================================

elif menu == "Data Mesin":

    st.title("🏭 Data Mesin")
    st.caption("Seluruh Equipment for Working dimuat otomatis dari lima sheet Excel Packing House.")
    machines = get_machines()
    st.subheader("🟨 Equipment for Working")
    if not machines.empty:
        working_view = machines[["machine_id", "machine_name", "area", "tag_padlock_total"]].copy()
        working_view.columns = ["Equipment ID", "Equipment for Working", "Area", "Jumlah titik Tag & Padlock"]
        st.dataframe(working_view, use_container_width=True, hide_index=True)
        st.caption(f"Total {len(working_view)} equipment dimuat dari workbook.")
    else:
        st.warning("Data Equipment for Working belum tersedia.")
    st.divider()
    st.subheader("🟨 Equipment for LOTOTO")
    st.caption("Equipment for LOTOTO memakai ID dan nama master yang sama dengan Equipment for Working; relasi hanya berisi Equipment for LOTOTO yang diberi tanda V pada baris Equipment for Working di Excel.")
    st.info("Buka menu LOTOTO Matrix untuk melihat seluruh relasi dan status setiap equipment.")

elif menu == "LOTOTO Matrix":

    st.title("🟨 LOTOTO Matrix")
    st.caption(
        "Setiap Equipment for Working ditampilkan sebagai satu grup, "
        "dengan hanya Equipment for LOTOTO yang memiliki tanda V pada baris tersebut di workbook Excel."
    )

    catalog_by_id = {str(item["machine_id"]): item for item in WORKING_EQUIPMENT_CATALOG}
    total_relations = sum(len(WORKING_TO_LOTOTO.get(str(item["machine_id"]), [])) for item in WORKING_EQUIPMENT_CATALOG)
    st.metric("Total relasi Working → LOTOTO", total_relations)
    st.caption("ID dan nama Equipment for LOTOTO ditampilkan pada setiap grup. Status mengikuti catatan LOTOTO per equipment.")

    for item in WORKING_EQUIPMENT_CATALOG:
        working_id = str(item["machine_id"])
        working_name = item["machine_name"]
        mapped_ids = [str(eid) for eid in get_mapped_equipment(working_id)]

        with st.expander(
            f"🏭 {working_id} — {working_name} | {len(mapped_ids)} Equipment for LOTOTO",
            expanded=False
        ):
            st.markdown(f"**Equipment for Working:** `{working_id}` — {working_name}")
            st.caption(
                f"Area: {item.get('area', '-')} · Jumlah titik Tag & Padlock: "
                f"{item.get('points') if item.get('points') is not None else 'Tidak tercantum di Excel'}"
            )

            if not mapped_ids:
                st.warning("Belum ada Equipment for LOTOTO yang dipetakan pada baris ini di Excel.")
                continue

            # Pastikan item status tersedia untuk record LOTOTO terakhir dari Working ini.
            latest_parent = read_sql_df(
                "SELECT id, work_status, start_time FROM public.lototo WHERE machine_id = %s ORDER BY id DESC LIMIT 1",
                params=(working_id,)
            )
            if not latest_parent.empty:
                ensure_lototo_equipment_items(
                    int(latest_parent.iloc[0]["id"]), working_id,
                    latest_parent.iloc[0]["start_time"]
                )

            # Tampilkan status terbaru untuk setiap Equipment for LOTOTO lintas kelompok Working.
            global_states = read_sql_df(
                """
                SELECT DISTINCT ON (ei.equipment_machine_id)
                    ei.equipment_machine_id, ei.status
                FROM public.lototo_equipment_items ei
                JOIN public.lototo l ON l.id = ei.lototo_id
                WHERE ei.equipment_machine_id = ANY(%s)
                ORDER BY ei.equipment_machine_id, ei.id DESC
                """,
                params=(mapped_ids,)
            )
            status_by_equipment = {
                str(row["equipment_machine_id"]): str(row["status"])
                for _, row in global_states.iterrows()
            }

            matrix_rows = []
            for equipment_id in mapped_ids:
                equipment = catalog_by_id.get(equipment_id, {})
                equipment_name = equipment.get("machine_name", "Nama equipment belum tersedia")
                raw_status = status_by_equipment.get(equipment_id, "BELUM DIMULAI")
                status_label = {
                    "ACTIVE": "🟢 ACTIVE / TERISOLASI",
                    "COMPLETED": "⚪ ENDED",
                    "BELUM DIMULAI": "— BELUM DIMULAI"
                }.get(raw_status, raw_status)
                matrix_rows.append({
                    "Equipment ID": equipment_id,
                    "Equipment for LOTOTO": equipment_name,
                    "Jumlah titik Tag & Padlock": equipment.get("points") if equipment else None,
                    "Status": status_label
                })

            matrix_df = pd.DataFrame(matrix_rows)
            def shade_ended_equipment(row):
                if row["Status"] == "⚪ ENDED":
                    return ["background-color: #d1d5db; color: #6b7280"] * len(row)
                return [""] * len(row)

            st.dataframe(
                matrix_df.style.apply(shade_ended_equipment, axis=1),
                use_container_width=True,
                hide_index=True
            )

            states = [status_by_equipment.get(eid, "BELUM DIMULAI") for eid in mapped_ids]
            if states and all(state == "ACTIVE" for state in states):
                st.success(
                    f"🟢 EQUIPMENT FOR WORKING ACTIVE — {working_id} — {working_name}. "
                    "Seluruh Equipment for LOTOTO pada baris ini sudah ACTIVE/terisolasi."
                )
            elif states and all(state == "COMPLETED" for state in states):
                st.info("Seluruh Equipment for LOTOTO pada Working ini sudah ENDED.")
            elif any(state == "COMPLETED" for state in states) and any(state == "ACTIVE" for state in states):
                st.warning("Sebagian Equipment for LOTOTO sudah ENDED (abu-abu), sementara equipment lainnya masih ACTIVE.")
            elif any(state == "ACTIVE" for state in states):
                st.info("Sebagian Equipment for LOTOTO sudah ACTIVE; equipment lainnya belum dimulai.")
            else:
                st.caption("Belum ada aktivitas LOTOTO untuk equipment dalam grup ini.")

    st.caption(
        "Sumber mapping: workbook lototo matrix packing house.xlsx. "
        "Periksa kembali mapping dan titik isolasi terhadap matriks resmi serta kondisi lapangan sebelum pekerjaan dilakukan."
    )

elif menu == "Start LOTOTO":

    st.title("▶️ Start LOTOTO")
    st.caption(
        "Penerapan LSR 6 - Isolasi Energi. Pilihan mesin Equipment for Working "
        "sudah dimuat otomatis dari gambar dan tidak perlu diinput manual."
    )

    machines = get_machines()

    if len(machines) == 0:

        st.warning(
            "Data Equipment for Working belum tersedia. Muat ulang aplikasi "
            "setelah proses pemuatan otomatis Supabase berhasil."
        )

    else:

        with st.form(
            "start_lototo",
            clear_on_submit=False
        ):

            st.subheader("Informasi Pekerjaan")

            work_order = st.text_input(
                "Work Order",
                placeholder="Contoh: WO-001"
            )

            # Keep the database machine_id as the selectbox value, but display
            # the Equipment for Working machine name to the operator.
            machine_options = machines["machine_id"].tolist()
            machine_name_by_id = dict(
                zip(machines["machine_id"].astype(str), machines["machine_name"].astype(str))
            )

            selected_machine = st.selectbox(
                "Pilih Equipment for Working",
                machine_options,
                format_func=lambda machine_id: (
                    f"{machine_id} — {machine_name_by_id.get(str(machine_id), str(machine_id))}"
                ),
            )

            technician = st.text_input(
                "Nama Teknisi / Petugas"
            )

            st.divider()

            selected_machine_data = machines[
                machines["machine_id"] == selected_machine
            ].iloc[0]

            st.info(
                f"**Sumber energi:** "
                f"{selected_machine_data['energy_source']}\n\n"
                f"**Isolation point:** "
                f"{selected_machine_data['isolation_point']}"
            )

            # ------------------------------------------------
            # LSR 6 STEP 1
            # ------------------------------------------------

            st.subheader(
                "LSR 6 - Step 1: Identifikasi Sumber Energi"
            )

            energy_identified = st.checkbox(
                "Saya telah mengidentifikasi seluruh sumber "
                "energi yang relevan pada mesin/peralatan."
            )

            # ------------------------------------------------
            # LSR 6 STEP 2
            # ------------------------------------------------

            st.subheader(
                "LSR 6 - Step 2: Beritahukan Pihak Terkait"
            )

            parties_notified = st.checkbox(
                "Pihak-pihak terkait telah diberitahukan "
                "mengenai penghentian/isolasi mesin."
            )

            st.write("**Bukti foto Step 2:**")

            jsa_photo = st.file_uploader(
                "📷 Upload Foto JSA",
                type=["jpg", "jpeg", "png"],
                key="jsa_photo"
            )

            dra_photo = st.file_uploader(
                "📷 Upload Foto DRA",
                type=["jpg", "jpeg", "png"],
                key="dra_photo"
            )

            ptw_type = st.selectbox(
                "Jenis PTW",
                PTW_TYPES,
                key="ptw_type"
            )

            ptw_number = st.text_input(
                "Nomor PTW",
                key="ptw_number"
            )

            safety_briefing_photo = st.file_uploader(
                "📷 Upload Foto Bukti Safety Briefing",
                type=["jpg", "jpeg", "png"],
                key="safety_briefing_photo"
            )

            ptw_photo = st.file_uploader(
                "📷 Upload Foto PTW",
                type=["jpg", "jpeg", "png"],
                key="ptw_photo"
            )

            e1, e2, e3, e4 = st.columns(4)

            with e1:
                if jsa_photo:
                    st.image(
                        jsa_photo,
                        caption="Preview - JSA",
                        width=300
                    )

            with e2:
                if dra_photo:
                    st.image(
                        dra_photo,
                        caption="Preview - DRA",
                        width=300
                    )

            with e3:
                if ptw_photo:
                    st.image(
                        ptw_photo,
                        caption="Preview - PTW",
                        width=300
                    )

            with e4:
                if safety_briefing_photo:
                    st.image(
                        safety_briefing_photo,
                        caption="Preview - Safety Briefing",
                        width=260
                    )

            # ------------------------------------------------
            # LSR 6 STEP 3
            # ------------------------------------------------

            st.subheader(
                "LSR 6 - Step 3: Matikan / Isolasi Energi"
            )

            shutdown_isolated = st.checkbox(
                "Mesin telah dimatikan dan/atau sumber energi "
                "telah diisolasi."
            )

            # ------------------------------------------------
            # LSR 6 STEP 4 - LOCK OUT
            # ------------------------------------------------

            st.subheader(
                "LSR 6 - Step 4: 🔒 Lock Out"
            )

            st.write(
                "Upload foto bukti penguncian sumber energi."
            )

            lock_photo = st.file_uploader(
                "📷 Foto Lock Out",
                type=["jpg", "jpeg", "png"],
                key="lock_photo"
            )

            if lock_photo:
                st.image(
                    lock_photo,
                    caption="Preview - Lock Out Evidence",
                    width=400
                )

            # ------------------------------------------------
            # LSR 6 STEP 5 - TAG OUT
            # ------------------------------------------------

            st.subheader(
                "LSR 6 - Step 5: 🏷️ Tag Out"
            )

            st.write(
                "Upload foto bukti penandaan/tag pada "
                "sumber energi."
            )

            tag_photo = st.file_uploader(
                "📷 Foto Tag Out",
                type=["jpg", "jpeg", "png"],
                key="tag_photo"
            )

            if tag_photo:
                st.image(
                    tag_photo,
                    caption="Preview - Tag Out Evidence",
                    width=400
                )

            # ------------------------------------------------
            # LSR 6 STEP 6 - TRY OUT
            # ------------------------------------------------

            st.subheader(
                "LSR 6 - Step 6: 🧪 Try Out"
            )

            try_out = st.checkbox(
                "Uji/coba (Try Out) telah dilakukan untuk "
                "memastikan isolasi energi efektif."
            )

            # ------------------------------------------------
            # LOTOTO MATRIX - AUTOMATIC SELECTION IN BACKGROUND
            # Based on selected Equipment for Working. The separate Matrix
            # page remains available for viewing; no duplicate checkboxes here.
            selected_working_id = str(selected_machine)
            selected_working_name = machine_name_by_id.get(
                selected_working_id, selected_working_id
            )
            mapped_equipment = {
                str(item) for item in get_mapped_equipment(selected_working_id)
            }

            # Yang dipilih hanya LOTOTO dengan ID dan nama yang identik
            # dengan Equipment for Working yang dipilih. Working lain yang
            # memetakan ID LOTOTO identik akan menampilkan status item yang
            # sama di LOTOTO Matrix, tetapi equipment LOTOTO lain milik
            # Working tersebut tidak ikut dibuat/diaktifkan.
            lototo_equipment_selected = []
            selected_lototo_name = machine_name_by_id.get(
                selected_working_id, selected_working_id
            )
            if (
                selected_working_id in mapped_equipment
                and selected_lototo_name.strip()
                == machine_name_by_id.get(selected_working_id, selected_working_id).strip()
            ):
                lototo_equipment_selected = [selected_working_id]

            # ------------------------------------------------
            # START
            # ------------------------------------------------

            start_button = st.form_submit_button(
                "▶️ START LOTOTO"
            )

            if start_button:

                errors = []

                if not work_order:
                    errors.append(
                        "Work Order wajib diisi."
                    )

                if not technician:
                    errors.append(
                        "Nama teknisi/petugas wajib diisi."
                    )

                if not energy_identified:
                    errors.append(
                        "LSR 6 Step 1 belum diverifikasi."
                    )

                if not parties_notified:
                    errors.append(
                        "LSR 6 Step 2 belum diverifikasi."
                    )

                if jsa_photo is None:
                    errors.append(
                        "Bukti foto JSA wajib diupload."
                    )

                if dra_photo is None:
                    errors.append(
                        "Bukti foto DRA wajib diupload."
                    )

                if not ptw_number.strip():
                    errors.append("Nomor PTW wajib diisi.")

                if ptw_photo is None:
                    errors.append("Bukti foto PTW wajib diupload.")

                if safety_briefing_photo is None:
                    errors.append("Bukti foto Safety Briefing wajib diupload.")

                if not shutdown_isolated:
                    errors.append(
                        "LSR 6 Step 3 belum diverifikasi."
                    )

                if lock_photo is None:
                    errors.append(
                        "Foto Lock Out wajib diupload."
                    )

                if tag_photo is None:
                    errors.append(
                        "Foto Tag Out wajib diupload."
                    )

                if not try_out:
                    errors.append(
                        "LSR 6 Step 6 Try Out belum diverifikasi."
                    )

                if not lototo_equipment_selected:
                    errors.append(
                        "Belum ada mapping Equipment for LOTOTO untuk mesin Working ini. LOTOTO Matrix perlu dilengkapi terlebih dahulu."
                    )

                # Check whether machine is already active
                cursor.execute(
                    """
                    SELECT id
                    FROM lototo
                    WHERE machine_id = %s
                    AND work_status = 'ACTIVE'
                    LIMIT 1
                    """,
                    (selected_machine,)
                )
                active_machine = cursor.fetchone()

                if active_machine:
                    errors.append(
                        "Mesin tersebut masih memiliki LOTOTO ACTIVE."
                    )

                # Cegah dua pekerjaan aktif mengunci equipment LOTOTO fisik yang sama.
                if lototo_equipment_selected:
                    cursor.execute(
                        """
                        SELECT ei.equipment_machine_id, l.machine_id
                        FROM public.lototo_equipment_items ei
                        JOIN public.lototo l ON l.id = ei.lototo_id
                        WHERE ei.equipment_machine_id = ANY(%s)
                          AND ei.status = 'ACTIVE'
                          AND l.work_status = 'ACTIVE'
                          AND l.machine_id <> %s
                        LIMIT 1
                        """,
                        (lototo_equipment_selected, selected_machine)
                    )
                    overlapping_active = cursor.fetchone()
                    if overlapping_active:
                        errors.append(
                            f"Equipment LOTOTO {overlapping_active[0]} sedang ACTIVE "
                            f"dalam pekerjaan Working {overlapping_active[1]}."
                        )

                # End the SELECT transaction even when the form has validation errors.
                conn.commit()

                if errors:

                    st.error(
                        "LOTOTO belum dapat dimulai:"
                    )

                    for error in errors:
                        st.write(f"❌ {error}")

                else:

                    start_time = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    # Upload independent evidence files concurrently. This is
                    # usually the main source of Start LOTOTO network delay.
                    evidence_paths = save_uploaded_files_parallel(
                        [
                            ("LOCK", lock_photo),
                            ("TAG", tag_photo),
                            ("JSA", jsa_photo),
                            ("DRA", dra_photo),
                            ("PTW", ptw_photo),
                            ("SAFETY_BRIEFING", safety_briefing_photo),
                        ],
                        work_order,
                        max_workers=4,
                    )
                    lock_path = evidence_paths["LOCK"]
                    tag_path = evidence_paths["TAG"]
                    jsa_path = evidence_paths["JSA"]
                    dra_path = evidence_paths["DRA"]
                    ptw_path = evidence_paths["PTW"]
                    safety_briefing_path = evidence_paths["SAFETY_BRIEFING"]

                    ptw_checklist_json = json.dumps(
                        {
                            "type": ptw_type,
                            "number": ptw_number,
                            "replaced_by": "safety_briefing_photo"
                        },
                        ensure_ascii=False
                    )

                    lototo_status = calculate_lototo_status(
                        {
                            "energy_identified": int(
                                energy_identified
                            ),
                            "parties_notified": int(
                                parties_notified
                            ),
                            "shutdown_isolated": int(
                                shutdown_isolated
                            ),
                            "lock_out": 1,
                            "tag_out": 1,
                            "try_out": int(
                                try_out
                            ),
                            "checked_restored": 0
                        }
                    )

                    cursor.execute(
                        """
                        INSERT INTO lototo
                        (
                            work_order,
                            machine_id,
                            technician,

                            start_time,
                            end_time,

                            energy_identified,
                            parties_notified,
                            shutdown_isolated,
                            lock_out,
                            tag_out,
                            try_out,
                            checked_restored,

                            lock_photo,
                            tag_photo,
                            lock_photo_time,
                            tag_photo_time,

                            jsa_photo,
                            dra_photo,
                            ptw_photo,
                            ptw_type,
                            ptw_number,
                            safety_briefing_photo,
                            safety_briefing_photo_time,
                            ptw_checklist_json,
                            jsa_photo_time,
                            dra_photo_time,
                            ptw_photo_time,

                            lototo_status,
                            work_status
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        RETURNING id
                        """,
                        (
                            work_order,
                            selected_machine,
                            technician,

                            start_time,
                            None,

                            int(energy_identified),
                            int(parties_notified),
                            int(shutdown_isolated),
                            1,
                            1,
                            int(try_out),
                            0,

                            lock_path,
                            tag_path,
                            start_time,
                            start_time,

                            jsa_path,
                            dra_path,
                            ptw_path,
                            ptw_type,
                            ptw_number,
                            safety_briefing_path,
                            start_time,
                            ptw_checklist_json,
                            start_time,
                            start_time,
                            start_time,

                            lototo_status,
                            "ACTIVE"
                        )
                    )
                    new_lototo_id = cursor.fetchone()[0]
                    for equipment_id in lototo_equipment_selected:
                        cursor.execute(
                            """
                            INSERT INTO public.lototo_equipment_items
                                (lototo_id, working_machine_id, equipment_machine_id, status, started_at)
                            VALUES (%s, %s, %s, 'ACTIVE', %s)
                            ON CONFLICT (lototo_id, equipment_machine_id) DO NOTHING
                            """,
                            (new_lototo_id, selected_machine, equipment_id, start_time)
                        )

                    conn.commit()

                    st.success(
                        "✅ LOTOTO berhasil dimulai."
                    )

                    st.info(
                        f"Start Time: {start_time}"
                    )

                    st.warning(
                        "Status pekerjaan: 🔴 ACTIVE"
                    )

                    st.caption(
                        "LSR 6 Step 7 akan diverifikasi "
                        "pada proses End LOTOTO."
                    )


# ============================================================
# ACTIVE LOTOTO
# ============================================================

elif menu == "Active LOTOTO":

    st.title("🔴 Active LOTOTO")
    st.caption("Buka detail melalui hyperlink untuk melihat detail dan melakukan End LOTOTO.")

    active = get_active_lototo()

    if len(active) == 0:
        st.success("Tidak ada pekerjaan LOTOTO yang sedang aktif.")
    else:
        machine_catalog = get_machines()
        machine_name_by_id = {
            str(row["machine_id"]): row["machine_name"]
            for _, row in machine_catalog.iterrows()
        }
        display = active[[
            "id", "work_order", "machine_id", "technician",
            "ptw_type", "ptw_number", "start_time",
            "lototo_status", "work_status"
        ]].copy()

        display["Work Order"] = display["id"].apply(
            lambda x: f"?page=detail&id={x}"
        )

        display["machine_id"] = display["machine_id"].astype(str).map(
            machine_name_by_id
        ).fillna(display["machine_id"].astype(str))

        display = display[[
            "id", "Work Order", "machine_id", "technician",
            "ptw_type", "ptw_number", "start_time",
            "lototo_status", "work_status"
        ]]

        display.columns = [
            "ID", "Work Order", "Machine", "Technician",
            "PTW Type", "PTW No.", "Start", "LSR 6 Status", "Work Status"
        ]

        st.dataframe(
            display.drop(columns=["Work Order"], errors="ignore"),
            hide_index=True,
            use_container_width=True
        )
        st.caption("Buka detail pada tab aplikasi yang sama:")
        render_open_detail_buttons(
            active,
            key_prefix="open_detail"
        )


# ============================================================
# END LOTOTO
# ============================================================

elif menu == "End LOTOTO":

    st.title("⏹️ End LOTOTO")
    st.caption("Pilih Open Detail untuk melakukan proses End LOTOTO.")

    active = get_active_lototo()

    if len(active) == 0:
        st.info("Tidak ada LOTOTO yang sedang aktif untuk diakhiri.")
    else:
        machine_catalog = get_machines()
        machine_name_by_id = {
            str(row["machine_id"]): row["machine_name"]
            for _, row in machine_catalog.iterrows()
        }
        display = active[[
            "id", "work_order", "machine_id", "technician",
            "ptw_type", "ptw_number", "start_time",
            "lototo_status", "work_status"
        ]].copy()

        display["Work Order"] = display["id"].apply(
            lambda x: f"?page=detail&id={x}"
        )

        display["machine_id"] = display["machine_id"].astype(str).map(
            machine_name_by_id
        ).fillna(display["machine_id"].astype(str))

        display = display[[
            "id", "Work Order", "machine_id", "technician",
            "ptw_type", "ptw_number", "start_time",
            "lototo_status", "work_status"
        ]]

        display.columns = [
            "ID", "Work Order", "Machine", "Technician",
            "PTW Type", "PTW No.", "Start", "LSR 6 Status", "Work Status"
        ]

        st.dataframe(
            display.drop(columns=["Work Order"], errors="ignore"),
            hide_index=True,
            use_container_width=True
        )
        st.caption("Buka detail pada tab aplikasi yang sama:")
        render_open_detail_buttons(
            active,
            key_prefix="open_detail"
        )


# ============================================================
# HISTORY
# ============================================================

elif menu == "History":

    st.title("📋 LOTOTO History")

    history = get_history()

    if len(history) == 0:

        st.info(
            "Belum ada history LOTOTO."
        )

    else:

        history_display = history.copy()

        history_display["duration"] = history_display.apply(
            lambda row: duration_between(
                row["start_time"],
                row["end_time"]
            ),
            axis=1
        )

        machine_catalog = get_machines()
        machine_name_by_id = {
            str(row["machine_id"]): row["machine_name"]
            for _, row in machine_catalog.iterrows()
        }

        display = history_display[
            [
                "id",
                "work_order",
                "machine_id",
                "technician",
                "ptw_type",
                "ptw_number",
                "start_time",
                "end_time",
                "duration",
                "lototo_status"
            ]
        ].copy()

        display["machine_id"] = display["machine_id"].astype(str).map(
            machine_name_by_id
        ).fillna(display["machine_id"].astype(str))

        display["Work Order"] = display["id"].apply(
            lambda x: f"?page=detail&id={x}"
        )

        display = display[
            [
                "id",
                "Work Order",
                "machine_id",
                "technician",
                "ptw_type",
                "ptw_number",
                "start_time",
                "end_time",
                "duration",
                "lototo_status"
            ]
        ]

        display.columns = [
            "ID",
            "Work Order",
            "Machine",
            "Technician",
            "PTW Type",
            "PTW No.",
            "Start",
            "End",
            "Duration",
            "LSR 6 Status"
        ]

        st.dataframe(
            display.drop(columns=["Work Order"], errors="ignore"),
            hide_index=True,
            use_container_width=True
        )
        st.caption("Buka detail pada tab aplikasi yang sama:")
        render_open_detail_buttons(
            history,
            key_prefix="history_detail"
        )

        csv = history_display.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download LOTOTO History CSV",
            csv,
            "lototo_history.csv",
            "text/csv"
        )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()
st.sidebar.caption(
    "LSR 6 - Isolasi Energi (LOTOTO)"
)
st.sidebar.caption(
    "Safety Management System - Prototype"
)



st.markdown("""
<style>
/* Sign In / Sign Up: remove the bright white inner strip and keep typed text clear.
   Style both the BaseWeb shell and the native input so browser defaults cannot
   paint a second white layer over the field. */
[data-testid="stTextInput"] div[data-baseweb="input"],
[data-testid="stTextInput"] div[data-baseweb="base-input"],
div[data-baseweb="input"],
div[data-baseweb="base-input"] {
    background: #eaf2f5 !important;
    border: 1px solid #c6d8df !important;
    border-radius: 11px !important;
    box-shadow: none !important;
}

/* Native editable area stays transparent inside the styled field shell */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] textarea,
div[data-baseweb="input"] input,
div[data-baseweb="base-input"] input {
    background: transparent !important;
    background-color: transparent !important;
    color: #183247 !important;
    -webkit-text-fill-color: #183247 !important;
    caret-color: #168b83 !important;
    opacity: 1 !important;
    text-shadow: none !important;
    font-weight: 600 !important;
    border: 0 !important;
    box-shadow: none !important;
}

/* Focus state: teal outline around the complete field, not an inner white bar */
[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
div[data-baseweb="input"]:focus-within,
div[data-baseweb="base-input"]:focus-within {
    background: #f0f8f8 !important;
    border-color: #168b83 !important;
    box-shadow: 0 0 0 2px rgba(22,139,131,.13) !important;
}

[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder,
[data-testid="stAppViewContainer"] input::placeholder,
[data-testid="stAppViewContainer"] textarea::placeholder {
    color: #718895 !important;
    -webkit-text-fill-color: #718895 !important;
    opacity: 1 !important;
    font-weight: 400 !important;
}

/* Keep password visibility control integrated with the same field surface */
[data-testid="stTextInput"] button,
div[data-baseweb="input"] button {
    background: transparent !important;
    color: #168b83 !important;
    border: 0 !important;
    box-shadow: none !important;
}

/* Prevent Chrome autofill from introducing a white overlay */
[data-testid="stAppViewContainer"] input:-webkit-autofill,
[data-testid="stAppViewContainer"] input:-webkit-autofill:hover,
[data-testid="stAppViewContainer"] input:-webkit-autofill:focus {
    -webkit-text-fill-color: #183247 !important;
    caret-color: #168b83 !important;
    -webkit-box-shadow: 0 0 0 1000px #eaf2f5 inset !important;
    box-shadow: 0 0 0 1000px #eaf2f5 inset !important;
}


/* FINAL OVERRIDE: make entered text black and remove inner white fill */
.stApp [data-testid="stTextInput"] input,
.stApp [data-testid="stTextArea"] textarea,
.stApp [data-testid="stNumberInput"] input,
.stApp [data-testid="stDateInput"] input,
.stApp div[data-baseweb="input"] input,
.stApp div[data-baseweb="base-input"] input,
.stApp input[type="text"],
.stApp input[type="password"],
.stApp input[type="email"],
.stApp textarea {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
    opacity: 1 !important;
    background: transparent !important;
    background-color: transparent !important;
    text-shadow: none !important;
    font-weight: 600 !important;
}

/* BaseWeb wrapper is the visible field; keep it light and remove inner overlays */
.stApp [data-testid="stTextInput"] [data-baseweb="input"],
.stApp [data-testid="stTextInput"] [data-baseweb="base-input"],
.stApp div[data-baseweb="input"],
.stApp div[data-baseweb="base-input"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid #b8cbd3 !important;
    box-shadow: none !important;
}

/* Focus border only; never add a white inset layer */
.stApp [data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
.stApp [data-testid="stTextInput"] [data-baseweb="base-input"]:focus-within,
.stApp div[data-baseweb="input"]:focus-within,
.stApp div[data-baseweb="base-input"]:focus-within {
    border-color: #168b83 !important;
    box-shadow: 0 0 0 2px rgba(22,139,131,.16) !important;
}

/* Placeholder remains gray; entered characters remain black */
.stApp input::placeholder,
.stApp textarea::placeholder {
    color: #758894 !important;
    -webkit-text-fill-color: #758894 !important;
    opacity: 1 !important;
    font-weight: 400 !important;
}

/* Chrome autofill: prevent browser's pale text/fill treatment */
.stApp input:-webkit-autofill,
.stApp input:-webkit-autofill:hover,
.stApp input:-webkit-autofill:focus {
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
    -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
    box-shadow: 0 0 0 1000px #ffffff inset !important;
}

</style>
""", unsafe_allow_html=True)





