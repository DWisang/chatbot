import streamlit as st
from openai import OpenAI
import base64
import json
import re

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
# LOAD JSON DATABASE
# ==============================
with open("teachers.json", "r", encoding="utf-8") as f:
    data = json.load(f)

teachers = data["guru"]

# ==============================
# HELPER FUNCTIONS
# ==============================
def normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text.strip()

def find_teacher_by_name(prompt):
    for teacher in teachers:
        if normalize(teacher["nama"]) in prompt:
            return teacher
        for alias in teacher["alias"]:
            if alias in prompt:
                return teacher
    return None

def find_by_jabatan(prompt):
    for teacher in teachers:
        if teacher["jabatan"]:
            if teacher["jabatan"].lower() in prompt:
                return teacher
    return None

def find_all_waka():
    waka_list = []
    for teacher in teachers:
        if teacher["jabatan"] and "waka" in teacher["jabatan"].lower():
            waka_list.append(f"{teacher['jabatan']} - {teacher['nama']}")
    return waka_list

# 🔥 FIXED SUBJECT MATCHING (NO DOUBLE)
def find_teacher_by_subject(prompt):
    matches = []
    for teacher in teachers:
        for subject in teacher["mapel"]:
            pattern = r"\b" + re.escape(subject.lower()) + r"\b"
            if re.search(pattern, prompt):
                matches.append(teacher)
                break
    return matches

# ==============================
# LOAD LOGO
# ==============================
def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo_base64 = get_base64_image("logo.png")

# ==============================
# UI HEADER
# ==============================
st.markdown(f"""
<style>
.stApp {{ background: #f8fafc; font-family: 'Segoe UI'; }}
header, #MainMenu, footer {{ visibility: hidden; }}

.fixed-header {{
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 90px;
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
    z-index: 999;
}}

.header-content {{
    display: flex;
    align-items: center;
    gap: 15px;
}}

.logo {{ width: 55px; }}
.header-spacer {{ height: 110px; }}

.chat-bubble {{
    padding: 14px 18px;
    border-radius: 20px;
    margin-bottom: 14px;
    max-width: 75%;
}}

.user {{
    background: #2563eb;
    color: white;
    margin-left: auto;
}}

.bot {{
    background: white;
    border: 1px solid #e2e8f0;
    margin-right: auto;
}}
</style>

<div class="fixed-header">
    <div class="header-content">
        <img src="data:image/png;base64,{logo_base64}" class="logo">
        <div>
            <b>SMAN 1 TUNJUNGAN</b><br>
            <small>Chatbot AI Sekolah</small>
        </div>
    </div>
</div>

<div class="header-spacer"></div>
""", unsafe_allow_html=True)

# ==============================
# SESSION STATE
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    role_class = "user" if msg["role"] == "user" else "bot"
    st.markdown(
        f"<div class='chat-bubble {role_class}'>{msg['content']}</div>",
        unsafe_allow_html=True
    )

# ==============================
# INPUT
# ==============================
if prompt := st.chat_input("Tulis pertanyaan Anda..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(
        f"<div class='chat-bubble user'>{prompt}</div>",
        unsafe_allow_html=True
    )

    clean_prompt = normalize(prompt)
    reply = None

    # ==============================
    # FUN RULE
    # ==============================
    if "guru" in clean_prompt and "ganteng" in clean_prompt:
        reply = "Guru paling ganteng adalah Pak Dhimas 😎"

    # ==============================
    # CEK SEMUA WAKA
    # ==============================
    if reply is None:
        if "waka" in clean_prompt and (
            "siapa" in clean_prompt or 
            "daftar" in clean_prompt or 
            "semua" in clean_prompt
        ):
            waka_list = find_all_waka()
            if waka_list:
                reply = "Berikut daftar Wakil Kepala Sekolah:\n\n" + "\n".join(waka_list)

    # ==============================
    # CEK JABATAN SPESIFIK
    # ==============================
    if reply is None:
        jabatan_match = find_by_jabatan(clean_prompt)
        if jabatan_match:
            reply = f"{jabatan_match['jabatan']} adalah {jabatan_match['nama']}."

    # ==============================
    # CEK NAMA GURU
    # ==============================
    if reply is None:
        teacher_match = find_teacher_by_name(clean_prompt)
        if teacher_match:
            jabatan = f" ({teacher_match['jabatan']})" if teacher_match["jabatan"] else ""
            reply = f"{teacher_match['nama']}{jabatan} mengampu: {', '.join(teacher_match['mapel'])}."

    # ==============================
    # CEK MAPEL
    # ==============================
    if reply is None:
        subject_matches = find_teacher_by_subject(clean_prompt)
        if subject_matches:
            names = [t["nama"] for t in subject_matches]
            reply = f"Guru yang mengampu mata pelajaran tersebut adalah: {', '.join(names)}."

    # ==============================
    # FALLBACK AI
    # ==============================
    if reply is None:
        with st.spinner("AI sedang mengetik..."):
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": """
Anda adalah Chatbot Resmi SMAN 1 TUNJUNGAN.
Nama sekolah WAJIB ditulis: SMAN 1 TUNJUNGAN.
JANGAN PERNAH menulis Tunjunggan.
Jawab dalam Bahasa Indonesia yang sopan dan profesional.
"""
                    },
                    *st.session_state.messages
                ],
                temperature=0.2,
                max_tokens=400,
            )

            reply = completion.choices[0].message.content
            reply = reply.replace("Tunjunggan", "TUNJUNGAN")

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.markdown(
        f"<div class='chat-bubble bot'>{reply}</div>",
        unsafe_allow_html=True
    )
