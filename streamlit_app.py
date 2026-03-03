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
with open("teachers.json", "r", encoding="utf-8") as f:
    teachers = json.load(f)["guru"]

with open("school_profile.json", "r", encoding="utf-8") as f:
    school_data = json.load(f)

with open("osis.json", "r", encoding="utf-8") as f:
    osis_data = json.load(f)["osis"]   # ROOT KEY FIXED

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

def find_teacher_by_subject(prompt):
    matches = []
    for teacher in teachers:
        for subject in teacher["mapel"]:
            pattern = r"\b" + re.escape(subject.lower()) + r"\b"
            if re.search(pattern, prompt):
                matches.append(teacher)
                break
    return matches

def find_all_waka():
    return [
        f"<li><b>{t['jabatan']}</b> - {t['nama']}</li>"
        for t in teachers
        if t["jabatan"] and "waka" in t["jabatan"].lower()
    ]

# ==============================
# STYLE
# ==============================
st.markdown("""
<style>
.chat-bubble {
    padding: 14px 18px;
    border-radius: 16px;
    margin-bottom: 10px;
}
.user { background: #2563eb; color: white; }
.bot { background: white; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ==============================
# SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================
# DISPLAY CHAT
# ==============================
for msg in st.session_state.messages:

    if msg["role"] == "user":
        st.markdown(
            f"<div class='chat-bubble user'>{msg['content']}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='chat-bubble bot'>{msg['content']}</div>",
            unsafe_allow_html=True
        )
        st.code(msg["content"], language="markdown")

# ==============================
# INPUT
# ==============================
if prompt := st.chat_input("Tulis pertanyaan Anda..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    clean_prompt = normalize(prompt)
    reply = None

    # ==============================
    # DATA SEKOLAH
    # ==============================
    if "alamat" in clean_prompt:
        a = school_data["alamat"]
        reply = f"""
<b>Alamat Sekolah:</b>
<ul>
<li>{a['jalan']}</li>
<li>Kecamatan: {a['kecamatan']}</li>
<li>Kabupaten: {a['kabupaten']}</li>
<li>Provinsi: {a['provinsi']}</li>
</ul>
"""

    elif "npsn" in clean_prompt:
        reply = f"NPSN: <b>{school_data['identitas']['npsn']}</b>"

    elif "jumlah siswa" in clean_prompt and "per tingkat" not in clean_prompt:
        reply = f"Jumlah total siswa: <b>{school_data['statistik']['jumlah_siswa_total']}</b> siswa"

    elif "per tingkat" in clean_prompt:
        t = school_data["statistik"]["per_tingkat"]
        reply = f"""
<b>Jumlah Siswa per Tingkat:</b>
<ul>
<li>Kelas 10: {t['kelas_10']} siswa</li>
<li>Kelas 11: {t['kelas_11']} siswa</li>
<li>Kelas 12: {t['kelas_12']} siswa</li>
</ul>
"""

    elif "umur" in clean_prompt:
        tahun_berdiri = datetime.strptime(
            school_data["legalitas"]["sk_pendirian"]["tanggal"],
            "%Y-%m-%d"
        ).year
        umur = datetime.now().year - tahun_berdiri
        reply = f"SMAN 1 TUNJUNGAN berdiri sejak {tahun_berdiri} dan saat ini berusia <b>{umur}</b> tahun."

    # ==============================
    # WAKA
    # ==============================
    elif "waka" in clean_prompt:
        waka_list = find_all_waka()
        reply = f"<b>Daftar Wakil Kepala Sekolah:</b><ul>{''.join(waka_list)}</ul>"

    # ==============================
    # GURU PER MAPEL
    # ==============================
    elif find_teacher_by_subject(clean_prompt):
        matches = find_teacher_by_subject(clean_prompt)
        list_html = "".join([f"<li>{t['nama']}</li>" for t in matches])
        reply = f"<b>Guru yang mengampu:</b><ul>{list_html}</ul>"

    # ==============================
    # DETAIL GURU
    # ==============================
    elif find_teacher_by_name(clean_prompt):
        teacher = find_teacher_by_name(clean_prompt)
        mapel_list = "".join([f"<li>{m}</li>" for m in teacher["mapel"]])
        jabatan = f" ({teacher['jabatan']})" if teacher["jabatan"] else ""
        reply = f"""
<b>{teacher['nama']}{jabatan}</b>
<br><br>
<b>Mata Pelajaran:</b>
<ul>{mapel_list}</ul>
"""

    # ==============================
    # OSIS INTI
    # ==============================
    elif "inti osis" in clean_prompt:
        list_html = "".join([
            f"<li><b>{i['jabatan']}</b> - {i['nama']}</li>"
            for i in osis_data["inti"]
        ])
        reply = f"<b>Pengurus Inti OSIS {osis_data['periode']}:</b><ul>{list_html}</ul>"

    # ==============================
    # LIST SEKSI
    # ==============================
    elif "list seksi" in clean_prompt:
        list_html = "".join([
            f"<li>{s['nama_seksi']}</li>"
            for s in osis_data["seksi"]
        ])
        reply = f"<b>Daftar Seksi OSIS:</b><ul>{list_html}</ul>"

    # ==============================
    # DETAIL SEKSI
    # ==============================
    elif "seksi" in clean_prompt:
        for seksi in osis_data["seksi"]:
            if seksi["nama_seksi"].lower() in clean_prompt:
                anggota_list = "".join([f"<li>{a}</li>" for a in seksi["anggota"]])
                reply = f"""
<b>{seksi['nama_seksi']}</b><br>
Ketua: {seksi['ketua']}
<br><br>
<b>Anggota:</b>
<ul>{anggota_list}</ul>
"""
                st.image(seksi["foto"], width=200)
                break

    # ==============================
    # PEMBINA OSIS
    # ==============================
    elif "pembina osis" in clean_prompt:
        p = osis_data["pembina"]
        reply = f"<b>Pembina OSIS</b><br>{p['nama']}"
        st.image(p["foto"], width=200)

    # ==============================
    # FALLBACK AI
    # ==============================
    if reply is None:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Anda adalah Chatbot Resmi SMAN 1 TUNJUNGAN."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=400,
        )
        reply = completion.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
