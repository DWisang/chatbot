import streamlit as st
from openai import OpenAI
import json
import re
import base64

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
        teachers_data = json.load(f)
        teachers = teachers_data.get("guru", teachers_data)
except:
    teachers = []

try:
    with open("school_profile.json", "r", encoding="utf-8") as f:
        school_data = json.load(f)
except:
    school_data = {}

osis = school_data.get("osis", {})

# ==============================
# STYLE + FIXED HEADER
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

.header-logo {{
    width: 55px;
}}

.header-text {{
    display: flex;
    flex-direction: column;
}}

.header-title {{
    font-size: 20px;
    font-weight: 600;
}}

.header-sub {{
    font-size: 13px;
    color: gray;
}}

.spacer {{
    height: 110px;
}}

.chat-row {{
    display: flex;
    margin-bottom: 15px;
}}

.user {{
    justify-content: flex-end;
}}

.bot {{
    justify-content: flex-start;
}}

.bubble {{
    padding: 12px 16px;
    border-radius: 18px;
    max-width: 70%;
    font-size: 14px;
}}

.user-bubble {{
    background: #2563eb;
    color: white;
}}

.bot-bubble {{
    background: #f1f5f9;
    color: black;
}}

.logo {{
    width: 38px;
    margin-right: 10px;
}}
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

    clean_prompt = normalize(prompt)
    reply = None

    # ==========================
    # LIST GURU
    # ==========================
    if any(k in clean_prompt for k in ["daftar guru", "list guru", "semua guru"]):
        if teachers:
            text = "<b>Daftar Guru:</b><br><br>"
            for t in teachers:
                nama = t.get("nama", "-")
                jabatan = t.get("jabatan", "")
                if jabatan:
                    text += f"• {nama} ({jabatan})<br>"
                else:
                    text += f"• {nama}<br>"
            reply = text
        else:
            reply = "Data guru tidak ditemukan."

    # ==========================
    # LIST WAKA
    # ==========================
    elif any(k in clean_prompt for k in ["waka", "wakil kepala"]):
        waka_list = [
            f"{t.get('jabatan')} - {t.get('nama')}"
            for t in teachers
            if "waka" in t.get("jabatan","").lower()
            or "wakil kepala" in t.get("jabatan","").lower()
        ]
        if waka_list:
            reply = "<b>Daftar Wakil Kepala Sekolah:</b><br><br>"
            for w in waka_list:
                reply += f"• {w}<br>"
        else:
            reply = "Data Wakil Kepala Sekolah tidak ditemukan."

    # ==========================
    # OSIS
    # ==========================
    elif "osis" in clean_prompt and osis:

        periode = osis.get("periode", "-")
        inti = osis.get("inti", {})
        seksi = osis.get("seksi", [])

        text = f"<b>Struktur OSIS Periode {periode}</b><br><br>"
        text += "<b>Pengurus Inti:</b><br>"

        for jab, data in inti.items():
            text += f"• {jab.replace('_',' ').title()}: {data.get('nama')} ({data.get('kelas')})<br>"

        text += "<br><b>Seksi Bidang:</b><br>"

        for s in seksi:
            text += f"<br><b>{s.get('nama_seksi')}</b><br>"
            text += f"• Ketua: {s.get('ketua',{}).get('nama')} ({s.get('ketua',{}).get('kelas')})<br>"

            for a in s.get("anggota", []):
                text += f"&nbsp;&nbsp;&nbsp;• {a.get('nama')} ({a.get('kelas')})<br>"

        reply = text

    # ==========================
    # STREAMING AI (NO ANIMATION)
    # ==========================
    if reply is None:
        full_reply = ""
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Anda adalah Chatbot Resmi SMAN 1 TUNJUNGAN."},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=0.2,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_reply += chunk.choices[0].delta.content

        reply = full_reply

    render_bot(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
