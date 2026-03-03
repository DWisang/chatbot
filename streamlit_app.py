import streamlit as st
from openai import OpenAI
import json
import re
import base64
from datetime import datetime

# ==============================
# CONFIG & INITIALIZATION
# ==============================
st.set_page_config(
    page_title="SMAN 1 TUNJUNGAN - Chatbot AI",
    page_icon="🎓",
    layout="wide",
)

# Inisialisasi API Client dengan Error Handling
try:
    client = OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )
except Exception as e:
    st.error("Konfigurasi API Key belum benar. Silakan cek st.secrets.")

MODEL_NAME = "llama-3.1-8b-instant"

# ==============================
# LOAD DATA (Caching untuk Performa)
# ==============================
@st.cache_data
def get_base64_image(path):
    try:
        with open(path, "rb") as img:
            return base64.b64encode(img.read()).decode()
    except:
        return ""

def load_json(file_path, default_val):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default_val

logo_base64 = get_base64_image("logo.png")
teachers_raw = load_json("teachers.json", {"guru": []})
teachers = teachers_raw.get("guru", [])
osis = load_json("osis.json", {"inti": {}, "seksi": []})
school_data = load_json("school_profile.json", {})

# ==============================
# STYLE
# ==============================
st.markdown(f"""
<style>
    header {{visibility:hidden;}}
    .fixed-header {{
        position: fixed; top: 0; left: 0; right: 0;
        background: white; padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        display: flex; align-items: center; justify-content: center;
        gap: 15px; z-index: 999;
    }}
    .header-logo {{ width: 50px; height: 50px; object-fit: contain; }}
    .header-title {{ font-size: 20px; font-weight: bold; color: #1e293b; }}
    .spacer {{ height: 100px; }}
    .chat-row {{ display: flex; margin-bottom: 15px; width: 100%; }}
    .user {{ justify-content: flex-end; }}
    .bot {{ justify-content: flex-start; }}
    .bubble {{
        padding: 12px 16px; border-radius: 15px;
        max-width: 75%; font-size: 14px; line-height: 1.5;
    }}
    .user-bubble {{ background: #2563eb; color: white; border-bottom-right-radius: 2px; }}
    .bot-bubble {{ background: #f1f5f9; color: #1e293b; border-bottom-left-radius: 2px; }}
    .bot-avatar {{ width: 35px; height: 35px; margin-right: 10px; border-radius: 50%; }}
</style>

<div class="fixed-header">
    <img src="data:image/png;base64,{logo_base64}" class="header-logo">
    <div style="display:flex; flex-direction:column;">
        <span class="header-title">SMAN 1 TUNJUNGAN</span>
        <span style="font-size:12px; color:gray;">Chatbot AI Resmi Sekolah</span>
    </div>
</div>
<div class="spacer"></div>
""", unsafe_allow_html=True)

# ==============================
# LOGIC FUNCTIONS
# ==============================
def normalize(text):
    if not isinstance(text, str):
        text = str(text)
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()

def handle_school_profile(prompt):
    p = normalize(prompt)
    identitas = school_data.get("identitas", {})
    alamat = school_data.get("alamat", {})
    
    if "alamat" in p or "lokasi" in p:
        return f"📍 **Alamat {identitas.get('nama_sekolah', 'Sekolah')}**: {alamat.get('jalan', '')}, Kec. {alamat.get('kecamatan', '')}, Kab. {alamat.get('kabupaten', '')}."
    if "npsn" in p:
        return f"🆔 **NPSN**: {identitas.get('npsn', '-')}"
    if "siswa" in p and "jumlah" in p:
        return f"📊 **Jumlah Siswa**: {school_data.get('statistik', {}).get('jumlah_siswa_total', '-')} orang."
    return None

def find_osis_query(prompt):
    prompt_norm = normalize(prompt)

    # 1. Cek Pengurus Inti
    for jab, data in osis.get("inti", {}).items():
        jab_text = str(jab).replace("_", " ")
        
        if isinstance(data, dict):
            nama_raw = data.get("nama", "")
            kelas = data.get("kelas", "-")
        else:
            nama_raw = str(data)
            kelas = "-"

        nama_norm = normalize(nama_raw)

        if nama_norm and re.search(r"\b" + re.escape(nama_norm) + r"\b", prompt_norm):
            return f"<b>{nama_raw}</b><br>Jabatan: {jab_text.title()}<br>Kelas: {kelas}"

        if jab_text in prompt_norm:
            return f"{jab_text.title()} adalah {nama_raw} ({kelas})"

    # 2. Cek Seksi-Seksi
    for seksi in osis.get("seksi", []):
        for anggota in seksi.get("anggota", []):
            if isinstance(anggota, dict):
                nama_anggota = anggota.get("nama", "")
                kelas_anggota = anggota.get("kelas", "")
            else:
                nama_anggota = str(anggota)
                kelas_anggota = ""
            
            nama_norm = normalize(nama_anggota)
            if nama_norm and re.search(r"\b" + re.escape(nama_norm) + r"\b", prompt_norm):
                resp = f"<b>{nama_anggota}</b>"
                if kelas_anggota:
                    resp += f" ({kelas_anggota})"
                resp += f"<br>Anggota {seksi.get('nama_seksi', 'Seksi')}"
                return resp

    return None

def find_teacher(prompt):
    p = normalize(prompt)
    
    # Cek Waka terlebih dahulu
    if "waka" in p or "wakil" in p:
        wakas = [f"• {t.get('jabatan', 'Wakil Kepala Sekolah')}: {t.get('nama', '-')}" for t in teachers if "waka" in str(t.get("jabatan", "")).lower()]
        if wakas: return "<b>Daftar Wakil Kepala Sekolah:</b><br>" + "<br>".join(wakas)

    # Cek Nama Guru
    for t in teachers:
        names_to_check = [normalize(t.get('nama', ''))]
        if 'alias' in t and isinstance(t['alias'], list):
            names_to_check.extend([normalize(a) for a in t['alias']])
            
        if any(name in p for name in names_to_check if len(name) > 2):
            res = f"<b>{t.get('nama', '-')}</b><br>"
            if t.get('jabatan'): res += f"📌 Jabatan: {t['jabatan']}<br>"
            if t.get('mapel'): 
                mapels = t['mapel'] if isinstance(t['mapel'], list) else [t['mapel']]
                res += f"📚 Mapel: {', '.join(mapels)}"
            return res
    return None

# ==============================
# CHAT INTERFACE
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan chat yang tersimpan
for m in st.session_state.messages:
    if m["role"] == "user":
        st.markdown(f'<div class="chat-row user"><div class="bubble user-bubble">{m["content"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''
            <div class="chat-row bot">
                <img src="data:image/png;base64,{logo_base64}" class="bot-avatar">
                <div class="bubble bot-bubble">{m["content"]}</div>
            </div>
        ''', unsafe_allow_html=True)

# Input User
if prompt := st.chat_input("Tanya tentang sekolah, guru, atau OSIS..."):
    # Render user message
    st.markdown(f'<div class="chat-row user"><div class="bubble user-bubble">{prompt}</div></div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Logic Pencarian (Waterfall)
    response = handle_school_profile(prompt)
    
    if not response: 
        response = find_osis_query(prompt)
        
    if not response: 
        response = find_teacher(prompt)
    
    # Jika tidak ada di data lokal, gunakan AI
    if not response:
        with st.spinner("Berpikir..."):
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "Anda adalah asisten AI resmi SMAN 1 Tunjungan. Jawab dengan sopan dan informatif. Jika tidak tahu, arahkan untuk menghubungi pihak sekolah."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                response = completion.choices[0].message.content
            except Exception as e:
                response = "Maaf, layanan AI sedang sibuk. Silakan coba lagi nanti."

    # Render bot response
    st.markdown(f'''
        <div class="chat-row bot">
            <img src="data:image/png;base64,{logo_base64}" class="bot-avatar">
            <div class="bubble bot-bubble">{response}</div>
        </div>
    ''', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": response})
