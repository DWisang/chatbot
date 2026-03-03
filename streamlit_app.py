import streamlit as st
from openai import OpenAI
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

# ==============================
# HELPER FUNCTIONS
# ==============================
def normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text.strip()

def find_teacher_by_name(prompt):
    for teacher in teachers:
        if normalize(teacher.get("nama", "")) in prompt:
            return teacher
        for alias in teacher.get("alias", []):
            if alias.lower() in prompt:
                return teacher
    return None

def find_all_waka():
    waka_list = []
    for teacher in teachers:
        jabatan = teacher.get("jabatan", "")
        if jabatan and "waka" in jabatan.lower():
            waka_list.append(f"{jabatan} - {teacher.get('nama','')}")
    return waka_list

def find_teacher_by_subject(prompt):
    matches = []
    for teacher in teachers:
        for subject in teacher.get("mapel", []):
            pattern = r"\b" + re.escape(subject.lower()) + r"\b"
            if re.search(pattern, prompt):
                matches.append(teacher)
                break
    return matches

# ==============================
# HEADER
# ==============================
st.title("🎓 SMAN 1 TUNJUNGAN")
st.caption("Chatbot AI Resmi Sekolah")

# ==============================
# SESSION STATE
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = []

# tampilkan chat lama
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==============================
# INPUT
# ==============================
if prompt := st.chat_input("Tulis pertanyaan Anda..."):

    # tampilkan user langsung
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    clean_prompt = normalize(prompt)
    reply = None

    # ==========================
    # LOGIKA LOKAL
    # ==========================
    if "guru" in clean_prompt and "ganteng" in clean_prompt:
        reply = "Guru paling ganteng adalah Pak Dhimas 😎"

    if reply is None:
        identitas = school_data.get("identitas", {})
        alamat = school_data.get("alamat", {})
        statistik = school_data.get("statistik", {})
        legalitas = school_data.get("legalitas", {})

        if "alamat" in clean_prompt:
            reply = (
                f"Alamat {identitas.get('nama_sekolah','SMAN 1 TUNJUNGAN')} adalah "
                f"{alamat.get('jalan','-')}, Kec. {alamat.get('kecamatan','-')}, "
                f"Kab. {alamat.get('kabupaten','-')}, Prov. {alamat.get('provinsi','-')}."
            )

        elif "npsn" in clean_prompt:
            reply = f"NPSN adalah {identitas.get('npsn','Tidak tersedia')}."

        elif "jumlah siswa" in clean_prompt:
            reply = f"Jumlah total siswa adalah {statistik.get('jumlah_siswa_total','-')} siswa."

        elif "waka" in clean_prompt:
            waka_list = find_all_waka()
            if waka_list:
                reply = "Daftar Wakil Kepala Sekolah:\n" + "\n".join(waka_list)

    if reply is None:
        teacher_match = find_teacher_by_name(clean_prompt)
        if teacher_match:
            jabatan = teacher_match.get("jabatan")
            jabatan_text = f" ({jabatan})" if jabatan else ""
            mapel = ", ".join(teacher_match.get("mapel", []))
            reply = f"{teacher_match.get('nama')}{jabatan_text} mengampu: {mapel}."

    if reply is None:
        subject_matches = find_teacher_by_subject(clean_prompt)
        if subject_matches:
            names = [t.get("nama") for t in subject_matches]
            reply = f"Guru yang mengampu mata pelajaran tersebut adalah: {', '.join(names)}."

    # ==========================
    # STREAMING AI (ANTI DELAY)
    # ==========================
    if reply is None:

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_reply = ""

            stream = client.chat.completions.create(
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
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_reply += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_reply + "▌")

            message_placeholder.markdown(full_reply)

        reply = full_reply

    else:
        with st.chat_message("assistant"):
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
