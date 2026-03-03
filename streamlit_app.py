import streamlit as st
from openai import OpenAI
import json
import re
import base64
import os

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
# LOAD LOGO
# ==============================
def get_base64_image(path):
    try:
        with open(path, "rb") as img:
            return base64.b64encode(img.read()).decode()
    except:
        return ""

logo_base64 = get_base64_image("logo.png")

# ==============================
# LOAD TEACHERS
# ==============================
try:
    with open("teachers.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
        teachers = raw["guru"] if "guru" in raw else raw
except:
    teachers = []

# ==============================
# LOAD OSIS
# ==============================
try:
    with open("osis.json", "r", encoding="utf-8") as f:
        raw_osis = json.load(f)
        osis = raw_osis["osis"] if "osis" in raw_osis else raw_osis
except:
    osis = {}

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

.header-text {{
    display: flex;
    flex-direction: column;
}}

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
# HELPER FUNCTIONS
# ==============================
def normalize(text):
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()

def render_user(msg):
    st.markdown(f"""
    <div class="chat-row user">
        <div class="bubble user-bubble">{msg}</div>
    </div>
    """, unsafe_allow_html=True)

def render_bot(msg, image_path=None):
    st.markdown(f"""
    <div class="chat-row bot">
        <img src="data:image/png;base64,{logo_base64}" class="logo">
        <div class="bubble bot-bubble">{msg}</div>
    </div>
    """, unsafe_allow_html=True)

    if image_path and os.path.exists(image_path):
        st.image(image_path, width=200)

def get_osis_photo(nama):
    filename = normalize(nama) + ".jpg"
    path = os.path.join("osis", filename)
    return path if os.path.exists(path) else None

def find_teacher_by_subject(prompt):
    prompt = normalize(prompt)
    results = []

    for t in teachers:
        for m in t.get("mapel", []):
            subject = normalize(m)
            if subject in prompt or any(word in prompt for word in subject.split()):
                results.append(t)
                break

    # remove duplicates
    unique = []
    seen = set()
    for r in results:
        if r["nama"] not in seen:
            unique.append(r)
            seen.add(r["nama"])

    return unique

def find_osis_query(prompt):
    prompt = normalize(prompt)
    inti = osis.get("inti", {})

    jabatan_mapping = {
        "ketua osis": "ketua_umum",
        "ketua umum": "ketua_umum",
        "wakil ketua": "wakil_ketua",
        "ketua harian": "ketua_harian",
        "sekretaris umum": "sekretaris_umum",
        "sekretaris": "sekretaris_umum",
        "wakil sekretaris": "wakil_sekretaris",
        "bendahara osis": "bendahara_umum",
        "bendahara umum": "bendahara_umum",
        "bendahara": "bendahara_umum",
        "wakil bendahara": "wakil_bendahara",
    }

    for key, value in jabatan_mapping.items():
        if key in prompt:
            data = inti.get(value)
            if data:
                nama = data.get("nama")
                kelas = data.get("kelas")
                photo = get_osis_photo(nama)
                return f"{key.title()} adalah {nama} ({kelas}).", photo

    for s in osis.get("seksi", []):
        nama_seksi = normalize(s.get("nama_seksi", ""))

        if "anggota" in prompt and any(word in prompt for word in nama_seksi.split()):
            text = f"Anggota Seksi {s.get('nama_seksi')}:<br>"
            for a in s.get("anggota", []):
                text += f"• {a.get('nama')} ({a.get('kelas')})<br>"
            return text, None

        if any(word in prompt for word in nama_seksi.split()):
            ketua = s.get("ketua", {})
            nama = ketua.get("nama")
            kelas = ketua.get("kelas")
            photo = get_osis_photo(nama)
            return f"Ketua Seksi {s.get('nama_seksi')} adalah {nama} ({kelas}).", photo

    return None, None

# ==============================
# SESSION STATE
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

    clean_prompt = normalize(prompt)
    reply = None
    photo = None

    # LIST GURU
    if "daftar guru" in clean_prompt:
        text = "<b>Daftar Guru:</b><br><br>"
        for t in teachers:
            text += f"• {t.get('nama')}<br>"
        reply = text

    # MAPEL
    if reply is None:
        subject_matches = find_teacher_by_subject(prompt)
        if subject_matches:
            text = "<b>Guru Pengampu:</b><br><br>"
            for t in subject_matches:
                text += f"• {t.get('nama')}<br>"
            reply = text

    # WAKA
    if reply is None and "waka" in clean_prompt:
        text = "<b>Daftar Wakil Kepala Sekolah:</b><br><br>"
        for t in teachers:
            if t.get("jabatan") and "waka" in t.get("jabatan","").lower():
                text += f"• {t.get('jabatan')} - {t.get('nama')}<br>"
        reply = text

    # OSIS SPECIFIC
    if reply is None and osis:
        reply, photo = find_osis_query(prompt)

    # OSIS FULL
    if reply is None and "osis" in clean_prompt:
        text = f"<b>Struktur OSIS Periode {osis.get('periode')}</b><br><br>"
        for jab, data in osis.get("inti", {}).items():
            text += f"• {jab.replace('_',' ').title()}: {data.get('nama')} ({data.get('kelas')})<br>"
        reply = text

    # AI FALLBACK
    if reply is None:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Anda adalah Chatbot Resmi SMAN 1 TUNJUNGAN."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        reply = completion.choices[0].message.content

    render_bot(reply, photo)
    st.session_state.messages.append({"role": "assistant", "content": reply})
