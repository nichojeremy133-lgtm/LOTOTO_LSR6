
import streamlit as st
import sqlite3
import json
import pandas as pd
import os
import uuid
from datetime import datetime

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

DB_FILE = "lototo.db"
EVIDENCE_FOLDER = "evidence"

os.makedirs(EVIDENCE_FOLDER, exist_ok=True)

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()



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
# DATABASE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT UNIQUE,
    machine_name TEXT NOT NULL,
    area TEXT,
    energy_source TEXT,
    isolation_point TEXT,
    status TEXT DEFAULT 'AVAILABLE'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS lototo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

conn.commit()


# ============================================================
# DATABASE MIGRATION
# Makes the application safer to update if an older DB exists.
# ============================================================

def ensure_column(table, column, definition):
    columns = [
        row[1]
        for row in cursor.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    ]

    if column not in columns:
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )
        conn.commit()


migration_columns = {
    "energy_identified": "INTEGER DEFAULT 0",
    "parties_notified": "INTEGER DEFAULT 0",
    "shutdown_isolated": "INTEGER DEFAULT 0",
    "lock_out": "INTEGER DEFAULT 0",
    "tag_out": "INTEGER DEFAULT 0",
    "try_out": "INTEGER DEFAULT 0",
    "checked_restored": "INTEGER DEFAULT 0",
    "lock_photo": "TEXT",
    "tag_photo": "TEXT",
    "lock_photo_time": "TEXT",
    "tag_photo_time": "TEXT",

    "jsa_photo": "TEXT",
    "dra_photo": "TEXT",
    "ptw_photo": "TEXT",
    "ptw_type": "TEXT",
    "ptw_number": "TEXT",
    "safety_briefing_photo": "TEXT",
    "safety_briefing_photo_time": "TEXT",
    "ptw_checklist_json": "TEXT",
    "jsa_photo_time": "TEXT",
    "dra_photo_time": "TEXT",
    "ptw_photo_time": "TEXT",

    "end_lock_photo": "TEXT",
    "end_tag_photo": "TEXT",
    "end_lock_photo_time": "TEXT",
    "end_tag_photo_time": "TEXT",

    "lototo_status": "TEXT DEFAULT 'NOT STARTED'",
    "work_status": "TEXT DEFAULT 'ACTIVE'",
    "end_confirmation": "INTEGER DEFAULT 0",
}

for column, definition in migration_columns.items():
    ensure_column("lototo", column, definition)


# ============================================================
# FUNCTIONS
# ============================================================

def get_machines():
    return pd.read_sql_query(
        """
        SELECT *
        FROM machines
        ORDER BY machine_id
        """,
        conn
    )


def get_lototo():
    return pd.read_sql_query(
        """
        SELECT *
        FROM lototo
        ORDER BY id DESC
        """,
        conn
    )


def get_active_lototo():
    return pd.read_sql_query(
        """
        SELECT *
        FROM lototo
        WHERE work_status = 'ACTIVE'
        ORDER BY start_time DESC
        """,
        conn
    )


def get_history():
    return pd.read_sql_query(
        """
        SELECT *
        FROM lototo
        WHERE work_status = 'COMPLETED'
        ORDER BY end_time DESC
        """,
        conn
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
    if uploaded_file is None:
        return None

    extension = os.path.splitext(uploaded_file.name)[1].lower()

    unique_id = uuid.uuid4().hex[:8]

    safe_work_order = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in work_order
    )

    filename = (
        f"{safe_work_order}_"
        f"{evidence_type}_"
        f"{unique_id}"
        f"{extension}"
    )

    filepath = os.path.join(
        EVIDENCE_FOLDER,
        filename
    )

    with open(filepath, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return filepath


def evidence_exists(path):
    return bool(path) and os.path.exists(path)


def duration_between(start_time, end_time):
    if not start_time or not end_time:
        return ""

    start = pd.to_datetime(start_time)
    end = pd.to_datetime(end_time)

    return str(end - start)


# ============================================================
# HEADER
# ============================================================

st.sidebar.title("🔒 LSR 6")
st.sidebar.caption("Energy Isolation - LOTOTO")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Data Mesin",
        "Start LOTOTO",
        "Active LOTOTO",
        "End LOTOTO",
        "History"
    ]
)


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

        detail = pd.read_sql_query(
            """
            SELECT *
            FROM lototo
            WHERE id = ?
            """,
            conn,
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
                    st.image(selected["lock_photo"], width=400)
                    st.caption(
                        f"Evidence time: {selected['lock_photo_time']}"
                    )
                else:
                    st.info("Tidak tersedia.")

            with c2:
                st.write("🏷️ Tag Out")
                if evidence_exists(selected["tag_photo"]):
                    st.image(selected["tag_photo"], width=400)
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
                        st.image(selected[field], width=260)
                        st.caption(f"Evidence time: {selected[time_field]}")
                    else:
                        st.info("Tidak tersedia.")

            st.divider()

            st.subheader("📄 PTW & Safety Briefing")
            st.write(f"**Jenis PTW:** {selected['ptw_type'] or '-'}")
            st.write(f"**Nomor PTW:** {selected['ptw_number'] or '-'}")

            if evidence_exists(selected["safety_briefing_photo"]):
                st.write("**📷 Bukti Safety Briefing**")
                st.image(selected["safety_briefing_photo"], width=450)
                st.caption(f"Evidence time: {selected['safety_briefing_photo_time']}")
            else:
                st.info("Bukti Safety Briefing tidak tersedia.")

            st.divider()

            st.subheader("📷 End Evidence - Lock Out / Tag Out")

            c1, c2 = st.columns(2)

            with c1:
                st.write("🔒 End Lock Out")
                if evidence_exists(selected["end_lock_photo"]):
                    st.image(selected["end_lock_photo"], width=400)
                    st.caption(
                        f"Evidence time: {selected['end_lock_photo_time']}"
                    )
                else:
                    st.info("Belum ada evidence End Lock Out.")

            with c2:
                st.write("🏷️ End Tag Out")
                if evidence_exists(selected["end_tag_photo"]):
                    st.image(selected["end_tag_photo"], width=400)
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
                st.subheader("⏹️ End LOTOTO")
                st.caption(
                    "Lengkapi evidence End Lock Out, End Tag Out, Step 7, "
                    "dan konfirmasi untuk menyelesaikan LOTOTO."
                )

                with st.form(f"end_lototo_detail_{detail_id}"):

                    end_lock_photo = st.file_uploader(
                        "📷 Upload Foto End Lock Out",
                        type=["jpg", "jpeg", "png"],
                        key=f"detail_end_lock_{detail_id}"
                    )

                    end_tag_photo = st.file_uploader(
                        "📷 Upload Foto End Tag Out",
                        type=["jpg", "jpeg", "png"],
                        key=f"detail_end_tag_{detail_id}"
                    )

                    checked_restored = st.checkbox(
                        "LSR 6 Step 7 telah diperiksa dan proses pengembalian "
                        "dilakukan sesuai prosedur.",
                        key=f"detail_checked_restored_{detail_id}"
                    )

                    confirmation = st.checkbox(
                        "Saya memastikan pekerjaan LOTOTO telah selesai dan "
                        "aman untuk END.",
                        key=f"detail_end_confirmation_{detail_id}"
                    )

                    end_button = st.form_submit_button("⏹️ END WORK")

                if end_button:
                    if end_lock_photo is None:
                        st.error("❌ Foto End Lock Out wajib diupload.")
                    elif end_tag_photo is None:
                        st.error("❌ Foto End Tag Out wajib diupload.")
                    elif not checked_restored:
                        st.error("❌ LSR 6 Step 7 belum diverifikasi.")
                    elif not confirmation:
                        st.error("❌ Konfirmasi END WORK belum dilakukan.")
                    else:
                        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        end_lock_path = save_uploaded_file(
                            end_lock_photo,
                            selected["work_order"],
                            "END_LOCK"
                        )

                        end_tag_path = save_uploaded_file(
                            end_tag_photo,
                            selected["work_order"],
                            "END_TAG"
                        )

                        cursor.execute(
                            """
                            UPDATE lototo
                            SET
                                end_time = ?,
                                checked_restored = 1,
                                end_confirmation = 1,
                                end_lock_photo = ?,
                                end_tag_photo = ?,
                                end_lock_photo_time = ?,
                                end_tag_photo_time = ?,
                                lototo_status = 'LSR 6 COMPLETE',
                                work_status = 'COMPLETED'
                            WHERE id = ?
                            """,
                            (
                                end_time,
                                end_lock_path,
                                end_tag_path,
                                end_time,
                                end_time,
                                detail_id
                            )
                        )

                        conn.commit()

                        st.success("✅ LOTOTO selesai.")
                        st.info(f"End Time: {end_time}")
                        st.rerun()

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
            display,
            column_config={
                "Work Order": st.column_config.LinkColumn(
                    "🔗 Work Order",
                    display_text="Open Detail"
                )
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("Tidak ada pekerjaan LOTOTO yang sedang aktif.")


# ============================================================
# DATA MESIN
# ============================================================

elif menu == "Data Mesin":

    st.title("🏭 Data Mesin")

    with st.form("machine_form"):

        machine_id = st.text_input(
            "ID Mesin",
            placeholder="Contoh: CV-001"
        )

        machine_name = st.text_input(
            "Nama Mesin",
            placeholder="Contoh: Conveyor 1"
        )

        area = st.text_input(
            "Area / Departemen"
        )

        energy = st.multiselect(
            "Sumber Energi",
            [
                "Electrical",
                "Mechanical",
                "Hydraulic",
                "Pneumatic",
                "Thermal",
                "Chemical",
                "Gravity"
            ]
        )

        isolation = st.text_input(
            "Isolation Point",
            placeholder="Contoh: MCC Panel 01 / Valve HV-01"
        )

        submitted = st.form_submit_button(
            "➕ Tambah Mesin"
        )

        if submitted:

            if not machine_id or not machine_name:
                st.error(
                    "ID Mesin dan Nama Mesin wajib diisi."
                )
            else:
                try:
                    cursor.execute(
                        """
                        INSERT INTO machines
                        (
                            machine_id,
                            machine_name,
                            area,
                            energy_source,
                            isolation_point,
                            status
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            machine_id,
                            machine_name,
                            area,
                            ", ".join(energy),
                            isolation,
                            "AVAILABLE"
                        )
                    )

                    conn.commit()

                    st.success(
                        "Data mesin berhasil ditambahkan."
                    )

                except sqlite3.IntegrityError:
                    st.error(
                        "ID mesin sudah terdaftar."
                    )

    st.divider()

    st.subheader("📋 Daftar Mesin")

    machines = get_machines()

    if len(machines):
        st.dataframe(
            machines,
            use_container_width=True
        )
    else:
        st.info("Belum ada data mesin.")


# ============================================================
# START LOTOTO
# ============================================================

elif menu == "Start LOTOTO":

    st.title("▶️ Start LOTOTO")
    st.caption(
        "Penerapan LSR 6 - Isolasi Energi"
    )

    machines = get_machines()

    if len(machines) == 0:

        st.warning(
            "Tambahkan data mesin terlebih dahulu."
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

            machine_options = machines[
                "machine_id"
            ].tolist()

            selected_machine = st.selectbox(
                "Pilih Mesin",
                machine_options
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

                # Check whether machine is already active
                active_machine = cursor.execute(
                    """
                    SELECT id
                    FROM lototo
                    WHERE machine_id = ?
                    AND work_status = 'ACTIVE'
                    """,
                    (selected_machine,)
                ).fetchone()

                if active_machine:
                    errors.append(
                        "Mesin tersebut masih memiliki "
                        "LOTOTO ACTIVE."
                    )

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

                    # Save evidence
                    lock_path = save_uploaded_file(
                        lock_photo,
                        work_order,
                        "LOCK"
                    )

                    tag_path = save_uploaded_file(
                        tag_photo,
                        work_order,
                        "TAG"
                    )

                    jsa_path = save_uploaded_file(
                        jsa_photo,
                        work_order,
                        "JSA"
                    )

                    dra_path = save_uploaded_file(
                        dra_photo,
                        work_order,
                        "DRA"
                    )

                    ptw_path = save_uploaded_file(
                        ptw_photo,
                        work_order,
                        "PTW"
                    )

                    safety_briefing_path = save_uploaded_file(
                        safety_briefing_photo,
                        work_order,
                        "SAFETY_BRIEFING"
                    )

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
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
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
        display = active[[
            "id", "work_order", "machine_id", "technician",
            "ptw_type", "ptw_number", "start_time",
            "lototo_status", "work_status"
        ]].copy()

        display["Work Order"] = display["id"].apply(
            lambda x: f"?page=detail&id={x}"
        )

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
            display,
            column_config={
                "Work Order": st.column_config.LinkColumn(
                    "🔗 Work Order",
                    display_text="Open Detail"
                )
            },
            hide_index=True,
            use_container_width=True
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
        display = active[[
            "id", "work_order", "machine_id", "technician",
            "ptw_type", "ptw_number", "start_time",
            "lototo_status", "work_status"
        ]].copy()

        display["Work Order"] = display["id"].apply(
            lambda x: f"?page=detail&id={x}"
        )

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
            display,
            column_config={
                "Work Order": st.column_config.LinkColumn(
                    "🔗 Work Order",
                    display_text="Open Detail"
                )
            },
            hide_index=True,
            use_container_width=True
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
            display,
            column_config={
                "Work Order": st.column_config.LinkColumn(
                    "🔗 Work Order",
                    display_text="Open Detail"
                )
            },
            hide_index=True,
            use_container_width=True
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
