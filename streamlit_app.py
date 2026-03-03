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
# LOAD DATA
# ==============================
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
        school = json.load(f)
except:
    school = {}

# ==============================
# STYLE
# ==============================
st.markdown(f"""
<style>
header {{visibility:hidden;}}
.fixed-header {{
    position: fixed;
    top: 0; left: 0; right: 0;
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

def remove_duplicates(results):
    unique = []
    seen = set()
    for r in results:
        if r["nama"] not in seen:
            unique.append(r)
            seen.add(r["nama"])
    return unique

# ==============================
# MAPEL SMART MATCH
# ==============================
def find_teacher_by_subject(prompt):
    prompt = normalize(prompt)
    results = []

    specific_keywords = ["islam", "kristen", "katolik", "buddha", "tl"]

    for keyword in specific_keywords:
        if keyword in prompt:
            for t in teachers:
                for m in t.get("mapel", []):
                    if keyword in normalize(m):
                        results.append(t)
                        break
            return remove_duplicates(results)

    for t in teachers:
        for m in t.get("mapel", []):
            subject = normalize(m)
            base_subject = subject.replace(" tl", "")
            if base_subject in prompt:
                results.append(t)
                break

    return remove_duplicates(results)

# ==============================
# OSIS
# ==============================
def find_osis_query(prompt):
    prompt = normalize(prompt)
    inti = osis.get("inti", {})

    for jab, data in inti.items():
        jab_text = jab.replace("_", " ")
        jab_words = jab_text.split()

        if any(word in prompt for word in jab_words):
            return f"{jab_text.title()} adalah {data.get('nama')} ({data.get('kelas')})."

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

    clean = normalize(prompt)
    reply = None

    identitas = school.get("identitas", {})
    alamat = school.get("alamat", {})
    statistik = school.get("statistik", {})
    legalitas = school.get("legalitas", {})

    # SCHOOL INFO
    if "alamat" in clean:
        reply = f"Alamat sekolah berada di {alamat.get('jalan')}, Kecamatan {alamat.get('kecamatan')}, Kabupaten {alamat.get('kabupaten')}, Provinsi {alamat.get('provinsi')}."

    elif "npsn" in clean:
        reply = f"NPSN {identitas.get('nama_sekolah')} adalah {identitas.get('npsn')}."

    elif "status" in clean:
        reply = f"Status sekolah adalah {identitas.get('status')}."

    elif "jumlah siswa" in clean:
        reply = f"Jumlah total siswa adalah {statistik.get('jumlah_siswa_total')} siswa."

    elif "kelas 10" in clean:
        reply = f"Jumlah siswa kelas 10 adalah {statistik.get('per_tingkat', {}).get('kelas_10')} siswa."

    elif "kelas 11" in clean:
        reply = f"Jumlah siswa kelas 11 adalah {statistik.get('per_tingkat', {}).get('kelas_11')} siswa."

    elif "kelas 12" in clean:
        reply = f"Jumlah siswa kelas 12 adalah {statistik.get('per_tingkat', {}).get('kelas_12')} siswa."

    elif "berdiri" in clean or "tahun berdiri" in clean:
        tanggal = legalitas.get("sk_pendirian", {}).get("tanggal")
        if tanggal:
            tahun = datetime.strptime(tanggal, "%Y-%m-%d").year
            umur = datetime.now().year - tahun
            reply = f"Sekolah berdiri pada tahun {tahun} dan saat ini berusia {umur} tahun."

    # GURU
    if reply is None:
        subject_matches = find_teacher_by_subject(prompt)
        if subject_matches:
            text = "<b>Guru Pengampu:</b><br><br>"
            for t in subject_matches:
                text += f"• {t.get('nama')}<br>"
            reply = text

    # OSIS
    if reply is None:
        reply = find_osis_query(prompt)

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

    render_bot(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
