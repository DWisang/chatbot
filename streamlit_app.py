import base64
import streamlit as st
import google.generativeai as genai

# ==============================
# CONFIG
# ==============================
st.set_page_config(
    page_title="SMAN 1 TUNJUNGAN - Chatbot AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================
# GEMINI API
# ==============================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel("models/gemini-1.5-pro")

# ==============================
# LOAD LOGO
# ==============================
def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo_base64 = get_base64_image("logo.png")

# ==============================
# UI STYLE
# ==============================
st.markdown(f"""
<style>
.stApp {{
    background: #f1f5f9;
    font-family: 'Segoe UI', sans-serif;
}}

.fixed-header {{
    position: fixed;
    top: 55px;
    left: 0;
    right: 0;
    height: 110px;
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

.school-logo {{
    width: 65px;
    height: 65px;
}}

.header-text h1 {{
    font-size: 26px;
    margin: 0;
    font-weight: 800;
    color: #1e293b;
}}

.header-text p {{
    font-size: 13px;
    margin-top: 4px;
    color: #64748b;
}}

.header-spacer {{
    height: 170px;
}}

.chat-bubble {{
    padding: 14px 18px;
    border-radius: 18px;
    margin-bottom: 12px;
    font-size: 15px;
    max-width: 75%;
    line-height: 1.6;
}}

.user {{
    background: #2563eb;
    color: white;
    margin-left: auto;
}}

.bot {{
    background: white;
    border: 1px solid #e2e8f0;
    color: #1e293b;
    margin-right: auto;
}}

[data-testid="stChatInput"] {{
    max-width: 800px;
    margin: auto;
}}

@media screen and (max-width: 768px) {{
    .chat-bubble {{
        max-width: 92%;
    }}
}}
</style>

<div class="fixed-header">
    <div class="header-content">
        <img src="data:image/png;base64,{logo_base64}" class="school-logo">
        <div class="header-text">
            <h1>SMAN 1 TUNJUNGAN</h1>
            <p>Chatbot AI Berbasis Artificial Intelligence</p>
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

# ==============================
# DISPLAY CHAT
# ==============================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble user'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble bot'>{msg['content']}</div>", unsafe_allow_html=True)

# ==============================
# INPUT
# ==============================
if prompt := st.chat_input("Tulis pertanyaan Anda..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<div class='chat-bubble user'>{prompt}</div>", unsafe_allow_html=True)

    with st.spinner("Chatbot sedang mengetik..."):

        chat_history = ""

        for m in st.session_state.messages:
            chat_history += f"{m['role']}: {m['content']}\n"

        full_prompt = (
            "Kamu adalah Chatbot AI resmi SMAN 1 TUNJUNGAN. "
            "Jawab dalam Bahasa Indonesia yang jelas dan profesional.\n\n"
            + chat_history
        )

        response = model.generate_content(full_prompt)
        reply = response.text

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.markdown(f"<div class='chat-bubble bot'>{reply}</div>", unsafe_allow_html=True)
