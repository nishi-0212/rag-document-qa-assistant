import streamlit as st
import requests
import os

API_BASE_URL = st.secrets.get(
    "API_BASE_URL",
    os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
)
UPLOAD_URL = f"{API_BASE_URL}/upload"
QUERY_URL = f"{API_BASE_URL}/query"

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Document Q&A Assistant",
    page_icon="📄",
    layout="centered"
)

# =========================
# SESSION
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =========================
# CSS
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Manrope', sans-serif;
}

.stApp {
    background-color: #f8fafc;
}

header, footer, #MainMenu {
    visibility: hidden;
}

.block-container {
    max-width: 900px;
    padding-top: 3rem;
}

/* Title */
.main-title {
    text-align: center;
    font-size: 3.2rem;
    font-weight: 800;
    color: #111827;
    margin-bottom: 3rem;
}

/* Buttons */
.stButton > button {
    border-radius: 14px;
    border: none;
    background: #2563eb;
    color: white;
    font-weight: 600;
    padding: 0.8rem 1rem;
    transition: 0.2s;
}

.stButton > button:hover {
    background: #1d4ed8;
}

/* Ask button smaller */
.ask-btn button {
    height: 52px;
}

/* Text input */
.stTextInput input {
    border-radius: 14px !important;
    border: 1px solid #d1d5db !important;
    padding: 0.9rem !important;
    background: white !important;
    color: #111827 !important;
    font-size: 1rem !important;
}

/* Placeholder */
.stTextInput input::placeholder {
    color: #6b7280 !important;
    opacity: 1 !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 1.5px dashed #cbd5e1;
    border-radius: 16px;
    padding: 1rem;
    background: white;
}

/* Response box */
.answer-box {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
    line-height: 1.6;
    color: #111827;
}

/* Source chips */
.source-chip {
    display: inline-block;
    background: #eff6ff;
    color: #2563eb;
    padding: 0.4rem 0.75rem;
    border-radius: 999px;
    margin: 0.2rem;
    font-size: 0.8rem;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# =========================
# TITLE
# =========================
st.markdown(
    "<div class='main-title'>Document Q&A Assistant</div>",
    unsafe_allow_html=True
)

# =========================
# UPLOAD
# =========================
uploaded_files = st.file_uploader(
    "Upload PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if st.button("Create Knowledge Base", use_container_width=True):
    if uploaded_files:
        files = [
            ("files", (file.name, file, "application/pdf"))
            for file in uploaded_files
        ]

        with st.spinner("Creating knowledge base..."):
            try:
                response = requests.post(UPLOAD_URL, files=files)

                if response.status_code == 200:
                    st.success("Knowledge base created successfully.")
                else:
                    st.error("Upload failed.")
            except Exception as e:
                st.error(f"Connection error: {e}")

st.write("")
st.write("")

# =========================
# QUESTION INPUT
# =========================
input_col1, input_col2, input_col3 = st.columns([0.2, 5, 1])

with input_col2:
    question = st.text_input(
        "Question",
        placeholder="Ask anything about your uploaded documents...",
        label_visibility="collapsed"
    )

with input_col3:
    ask_clicked = st.button("Ask", use_container_width=True)

# =========================
# QUERY
# =========================
if ask_clicked:
    if question.strip():
        with st.spinner("Searching documents..."):
            try:
                response = requests.post(
                    QUERY_URL,
                    json={"question": question}
                )

                if response.status_code == 200:
                    result = response.json()

                    st.session_state.chat_history.append({
                        "question": question,
                        "answer": result["answer"],
                        "sources": result["sources"]
                    })

                else:
                    st.error("Query failed.")

            except Exception as e:
                st.error(f"Connection error: {e}")

# =========================
# RESPONSES
# =========================
if st.session_state.chat_history:
    st.write("")
    st.subheader("Responses")

    for chat in reversed(st.session_state.chat_history):
        st.markdown(f"**Question:** {chat['question']}")

        st.markdown(
            f"<div class='answer-box'>{chat['answer']}</div>",
            unsafe_allow_html=True
        )

        source_html = ""
        for src in chat["sources"]:
            source_html += f"<span class='source-chip'>{src}</span>"

        st.markdown(source_html, unsafe_allow_html=True)