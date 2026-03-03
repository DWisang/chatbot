import streamlit as st
from openai import OpenAI
import base64
import json
import re
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
with open("teachers.json", "r", encoding="utf-8") as f:
    teachers = json.load(f)["guru"]

with open("school_profile.json", "r", encoding="utf-8") as f:
    school_data = json.load(f)

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
        if teacher["jabatan"] and teacher["jabatan"].lower() in prompt:
            return teacher
    return None

def find_all_waka():
    waka_list = []
    for teacher in teachers:
        if teacher["jabatan"] and "waka" in teacher["jabatan"].lower():
            waka_list.append(f"<b>{teacher['jabatan']}</b> - {teacher['nama']}")
    return waka_list

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
# HEADER + STYLE
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

.copy-btn {{
    margin-top:8px;
    padding:4px 10px;
    border-radius:8px;
    border:none;
    background:#2563eb;
    color:white;
    cursor:pointer;
}}
</style>

<script>
function copyText(id) {{
    var text = document.getElementById(id).innerText;
    navigator.clipboard.writeText(text);
}}
</script>

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
# SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = []

for i, msg in enumerate(st.session_state.messages):
    role_class = "user" if msg["role"] == "user" else "bot"

    if msg["role"] == "assistant":
        st.markdown(
            f"""
            <div class='chat-bubble {role_class}'>
                <div id='msg_{i}'>{msg['content']}</div>
                <button class='copy-btn' onclick="copyText('msg_{i}')">📋 Copy</button>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='chat-bubble {role_class}'>{msg['content']}</div>",
            unsafe_allow_html=True
        )

# ==============================
# INPUT
# ==============================
if prompt := st.chat_input("Tulis pertanyaan Anda..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    clean_prompt = normalize(prompt)
    reply = None

    # FUN
    if "guru" in clean_prompt and "ganteng" in clean_prompt:
        reply = "Guru paling ganteng adalah Pak Dhimas 😎"

    # DATA SEKOLAH
    if reply is None:
        if "alamat" in clean_prompt:
            alamat = school_data["alamat"]
            reply = (
                f"Alamat {school_data['identitas']['nama_sekolah']} adalah "
                f"{alamat['jalan']}, Kec. {alamat['kecamatan']}, "
                f"Kab. {alamat['kabupaten']}, Prov. {alamat['provinsi']}."
            )

        elif "npsn" in clean_prompt:
            reply = f"NPSN {school_data['identitas']['nama_sekolah']} adalah {school_data['identitas']['npsn']}."

        elif "jumlah siswa" in clean_prompt or "total siswa" in clean_prompt:
            reply = f"Jumlah total siswa adalah {school_data['statistik']['jumlah_siswa_total']} siswa."

        elif "kelas 10" in clean_prompt:
            reply = f"Jumlah siswa kelas 10 adalah {school_data['statistik']['per_tingkat']['kelas_10']} siswa."

        elif "kelas 11" in clean_prompt:
            reply = f"Jumlah siswa kelas 11 adalah {school_data['statistik']['per_tingkat']['kelas_11']} siswa."

        elif "kelas 12" in clean_prompt:
            reply = f"Jumlah siswa kelas 12 adalah {school_data['statistik']['per_tingkat']['kelas_12']} siswa."

        elif "umur" in clean_prompt or "berdiri sejak" in clean_prompt:
            tanggal_str = school_data["legalitas"]["sk_pendirian"]["tanggal"]
            tahun_berdiri = datetime.strptime(tanggal_str, "%Y-%m-%d").year
            tahun_sekarang = datetime.now().year
            umur = tahun_sekarang - tahun_berdiri
            reply = f"SMAN 1 TUNJUNGAN berdiri sejak {tahun_berdiri} dan pada tahun {tahun_sekarang} berusia {umur} tahun."

    # WAKA LIST
    if reply is None and "waka" in clean_prompt:
        waka_list = find_all_waka()
        if waka_list:
            list_html = "".join([f"<li>{w}</li>" for w in waka_list])
            reply = f"<b>Daftar Wakil Kepala Sekolah:</b><ul>{list_html}</ul>"

    # JABATAN
    if reply is None:
        jabatan_match = find_by_jabatan(clean_prompt)
        if jabatan_match:
            reply = f"{jabatan_match['jabatan']} adalah {jabatan_match['nama']}."

    # NAMA GURU
    if reply is None:
        teacher_match = find_teacher_by_name(clean_prompt)
        if teacher_match:
            jabatan = f" ({teacher_match['jabatan']})" if teacher_match["jabatan"] else ""
            reply = f"{teacher_match['nama']}{jabatan} mengampu: {', '.join(teacher_match['mapel'])}."

    # MAPEL
    if reply is None:
        subject_matches = find_teacher_by_subject(clean_prompt)
        if subject_matches:
            names = [t["nama"] for t in subject_matches]
            reply = f"Guru yang mengampu mata pelajaran tersebut adalah: {', '.join(names)}."

    # FALLBACK AI
    if reply is None:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "Anda adalah Chatbot Resmi SMAN 1 TUNJUNGAN. Jawab sopan dan profesional."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=400,
        )
        reply = completion.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
