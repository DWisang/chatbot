import streamlit as st
from huggingface_hub import InferenceClient

st.title("💬 Chatbot (Hugging Face)")

st.write(
    "This chatbot uses a Hugging Face model via Inference API."
)

hf_token = st.text_input("Hugging Face API Key", type="password")

if not hf_token:
    st.info("Please add your Hugging Face API key to continue.", icon="🔑")
else:
    client = InferenceClient(
        model="Qwen/Qwen2.5-3B-Instruct",
        token=hf_token,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):

        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

       prompt_text = ""
for m in st.session_state.messages:
    prompt_text += f"{m['role']}: {m['content']}\n"

response = client.text_generation(
    prompt_text,
    max_new_tokens=300,
)

reply = response

        with st.chat_message("assistant"):
            st.markdown(reply)

        st.session_state.messages.append(
            {"role": "assistant", "content": reply}
        )
