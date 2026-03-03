import streamlit as st
from openai import OpenAI
import json
import re
import base64
from datetime import datetime

# ==============================
# CONFIG
# ==============================
st.set_page_config(
    page_title="SMAN 1 TUNJUNGAN - Chatbot AI",
    page_icon="🎓",
    layout="wide",
)

client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

MODEL_NAME = "llama-3.1-8b-instant"

# ==============================
# LOAD DATA
# ==============================
def get_base64_image(path):
    try:
        with open(path, "rb") as img:
            return base64.b64encode(img.read()).decode()
    except:
        return ""

logo_base64 = get_base64_image("logo.png")

try:
    with open("teachers.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
        teachers = raw["guru"] if "guru" in raw else raw
except:
    teachers = []

try:
    with open("osis.json", "r", encoding="utf-8") as f:
        raw_osis = json.load(f)
        osis = raw_osis["osis"] if "osis" in raw_osis else raw_osis
except:
    osis = {}

try:
    with open("school_profile.json", "r", encoding="utf-8") as f:
        school_data = json.load(f)
except:
    school_data = {}

# ==============================
# STYLE
# ==============================
st.markdown(f"""
<style>
header {{visibility:hidden;}}
.fixed-header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: white;
    padding: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    z-index: 999;
}}
.header-logo {{ width: 55px; }}
.header-text {{ display: flex; flex-direction: column; }}
.header-title {{ font-size: 20px; font-weight: 600; }}
.header-sub {{ font-size: 13px; color: gray; }}
.spacer {{ height: 110px; }}
.chat-row {{ display: flex; margin-bottom: 15px; }}
.user {{ justify-content: flex-end; }}
.bot {{ justify-content: flex-start; }}
.bubble {{
    padding: 12px 16px;
    border-radius: 18px;
    max-width: 70%;
    font-size: 14px;
}}
.user-bubble {{ background: #2563eb; color: white; }}
.bot-bubble {{ background: #f1f5f9; color: black; }}
.logo {{ width: 38px; margin-right: 10px; }}
</style>

<div class="fixed-header">
    <img src="data:image/png;base64,{logo_base64}" class="header-logo">
    <div class="header-text">
        <div class="header-title">SMAN 1 TUNJUNGAN</div>
        <div class="header-sub">Chatbot AI Resmi Sekolah</div>
    </div>
</div>
<div class="spacer"></div>
""", unsafe_allow_html=True)

# ==============================
# HELPER
# ==============================
def normalize(text):
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()

def render_user(msg):
    st.markdown(f"""
    <div class="chat-row user">
        <div class="bubble user-bubble">{msg}</div>
    </div>
    """, unsafe_allow_html=True)

def render_bot(msg):
    st.markdown(f"""
    <div class="chat-row bot">
        <img src="data:image/png;base64,{logo_base64}" class="logo">
        <div class="bubble bot-bubble">{msg}</div>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# SCHOOL PROFILE
# ==============================
def handle_school_profile(prompt):
    prompt = normalize(prompt)
    identitas = school_data.get("identitas", {})
    alamat = school_data.get("alamat", {})
    statistik = school_data.get("statistik", {})
    legalitas = school_data.get("legalitas", {})

    if "alamat" in prompt:
        return f"Alamat {identitas.get('nama_sekolah')} adalah {alamat.get('jalan')}, Kec. {alamat.get('kecamatan')}, Kab. {alamat.get('kabupaten')}, Prov. {alamat.get('provinsi')}."

    if "npsn" in prompt:
        return f"NPSN {identitas.get('nama_sekolah')} adalah {identitas.get('npsn')}."

    if "jumlah siswa" in prompt:
        return f"Jumlah total siswa adalah {statistik.get('jumlah_siswa_total')} siswa."

    if "umur" in prompt or "berdiri" in prompt:
        tanggal = legalitas.get("sk_pendirian", {}).get("tanggal")
        if tanggal:
            tahun = datetime.strptime(tanggal, "%Y-%m-%d").year
            umur = datetime.now().year - tahun
            return f"{identitas.get('nama_sekolah')} berdiri sejak {tahun} dan saat ini berusia {umur} tahun."

    return None

# ==============================
# OSIS SMART
# ==============================
def find_osis_query(prompt):
    prompt = normalize(prompt)

    for jab, data in osis.get("inti", {}).items():
        jab_text = jab.replace("_", " ")
        nama = normalize(data.get("nama",""))

        if re.search(r"\b" + re.escape(nama) + r"\b", prompt):
            return f"<b>{data.get('nama')}</b><br>Jabatan: {jab_text.title()}<br>Kelas: {data.get('kelas')}"

        if jab_text in prompt:
            return f"{jab_text.title()} adalah {data.get('nama')} ({data.get('kelas')})"

    for seksi in osis.get("seksi", []):
        for anggota in seksi.get("anggota", []):
            if re.search(r"\b" + re.escape(normalize(anggota)) + r"\b", prompt):
                return f"<b>{anggota}</b><br>Anggota {seksi.get('nama_seksi')}"

    return None

# ==============================
# FORMAT GURU
# ==============================
def format_teacher_detail(t):
    text = f"<b>{t.get('nama')}</b><br><br>"
    if t.get("jabatan"):
        text += f"Jabatan: {t.get('jabatan')}<br>"
    if t.get("mapel"):
        text += f"Mengampu: {', '.join(t.get('mapel'))}"
    return text

# ==============================
# SAFE GURU MATCH (FILTERED)
# ==============================
def find_teacher_by_name(prompt):
    prompt_clean = normalize(prompt)

    trigger_keywords = ["siapa", "pak", "bu", "guru", "wali", "mengampu"]
    if not any(word in prompt_clean for word in trigger_keywords):
        return None

    for t in teachers:
        nama = normalize(t.get("nama",""))

        for alias in t.get("alias", []):
            pattern = r"\b" + re.escape(normalize(alias)) + r"\b"
            if re.search(pattern, prompt_clean):
                return format_teacher_detail(t)

        full_pattern = r"\b" + re.escape(nama) + r"\b"
        if re.search(full_pattern, prompt_clean):
            return format_teacher_detail(t)

    return None

# ==============================
# WAKA
# ==============================
def find_waka(prompt):
    prompt = normalize(prompt)

    if "waka" not in prompt:
        return None

    waka_list = []
    for t in teachers:
        jabatan = t.get("jabatan")
        if jabatan and "waka" in jabatan.lower():
            if normalize(jabatan) in prompt:
                return f"{jabatan} adalah {t.get('nama')}."
            waka_list.append(f"• {jabatan} - {t.get('nama')}")

    if waka_list:
        text = "<b>Daftar Wakil Kepala Sekolah:</b><br><br>"
        for w in waka_list:
            text += w + "<br>"
        return text

    return None

# ==============================
# SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    if m["role"] == "user":
        render_user(m["content"])
    else:
        render_bot(m["content"])

# ==============================
# INPUT
# ==============================
if prompt := st.chat_input("Tulis pertanyaan Anda..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    render_user(prompt)

    reply = None

    reply = handle_school_profile(prompt)

    if reply is None:
        reply = find_osis_query(prompt)

    if reply is None:
        reply = find_teacher_by_name(prompt)

    if reply is None:
        reply = find_waka(prompt)

    if reply is None:
        with st.spinner("AI sedang mengetik..."):
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Anda adalah Chatbot Resmi SMAN 1 TUNJUNGAN."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            reply = completion.choices[0].message.content

    render_bot(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
