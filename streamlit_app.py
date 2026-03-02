import streamlit as st
from openai import OpenAI
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
def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo_base64 = get_base64_image("logo.png")

# ==============================
# CSS + FIXED HEADER
# ==============================
st.markdown(f"""
<style>

/* Background */
.stApp {{
    background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    font-family: 'Segoe UI', sans-serif;
}}

header {{visibility: hidden;}}
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

/* Fixed Header */
.fixed-header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
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

.logo {{
    width: 55px;
    height: 55px;
    border-radius: 12px;
}}

.header-text {{
    text-align: left;
}}

.header-text h1 {{
    font-size: 20px;
    margin: 0;
    font-weight: 800;
    color: #0f172a;
}}

.header-text p {{
    font-size: 13px;
    margin: 0;
    color: #64748b;
}}

/* Spacer */
.header-spacer {{
    height: 110px;
}}

/* Chat container */
.block-container {{
    max-width: 900px;
    margin: auto;
}}

/* Chat bubble */
.chat-bubble {{
    padding: 14px 18px;
    border-radius: 22px;
    margin-bottom: 14px;
    max-width: 75%;
    line-height: 1.6;
    font-size: 15px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
    word-wrap: break-word;
}}

.user {{
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 6px;
}}

.bot {{
    background: white;
    color: #0f172a;
    margin-right: auto;
    border-bottom-left-radius: 6px;
    border: 1px solid #e2e8f0;
}}

/* Input */
[data-testid="stChatInput"] {{
    max-width: 800px;
    margin: auto;
}}

/* Mobile */
@media screen and (max-width: 768px) {{

    .logo {{
        width: 45px;
        height: 45px;
    }}

    .header-text h1 {{
        font-size: 16px;
    }}

    .header-text p {{
        font-size: 11px;
    }}

    .chat-bubble {{
        max-width: 92%;
        font-size: 14px;
    }}
}}

</style>

<div class="fixed-header">
    <div class="header-content">
        <img src="data:image/png;base64,{logo_base64}" class="logo">
        <div class="header-text">
            <h1>SMAN 1 TUNJUNGAN</h1>
            <p>Chatbot AI Berbasis Groq Llama 3.1</p>
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
        st.markdown(
            f"<div class='chat-bubble user'>{msg['content']}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='chat-bubble bot'>{msg['content']}</div>",
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

    with st.spinner("AI sedang mengetik..."):

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "Kamu adalah Chatbot AI resmi SMAN 1 TUNJUNGAN. Jawab dalam Bahasa Indonesia yang jelas dan profesional."
                },
                *st.session_state.messages
            ],
            temperature=0.3,
            max_tokens=500,
        )

        reply = completion.choices[0].message.content

    st.session_state.messages.append(
        {"role": "assistant", "content": reply}
    )

    st.markdown(
        f"<div class='chat-bubble bot'>{reply}</div>",
        unsafe_allow_html=True
    )
