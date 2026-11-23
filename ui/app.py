import sys
from pathlib import Path

# Thêm thư mục gốc project vào Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import streamlit as st
import uuid
import json

from src.llm import chat, SYSTEM
from src.config import PROVIDER, GEMINI_MODEL, OLLAMA_MODEL

st.set_page_config(
    page_title="My AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

# CSS
st.markdown("""
<style>
.stApp {
    background: #10121a;
    color: white;
}
[data-testid="stSidebar"] {
    background: #191c27;
}
[data-testid="stChatMessage"] {
    background: #1c2030;
    border-radius: 15px;
    padding: 12px;
}
h1 {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# File lưu lịch sử
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "conversations.json"


def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(
                HISTORY_FILE.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_history():
    HISTORY_FILE.write_text(
        json.dumps(
            st.session_state.chats,
            ensure_ascii=False,
            indent=4
        ),
        encoding="utf-8"
    )


if "chats" not in st.session_state:
    st.session_state.chats = load_history()

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None


def new_chat():
    chat_item = {
        "id": str(uuid.uuid4()),
        "title": "Cuộc trò chuyện mới",
        "messages": []
    }
    st.session_state.chats.insert(0, chat_item)
    st.session_state.active_chat = chat_item["id"]
    save_history()


def get_chat():
    for item in st.session_state.chats:
        if item["id"] == st.session_state.active_chat:
            return item

    new_chat()
    return st.session_state.chats[0]


# SIDEBAR
with st.sidebar:
    st.title("🤖 My AI")

    if st.button("＋ Cuộc trò chuyện mới", use_container_width=True):
        new_chat()
        st.rerun()

    st.divider()
    st.subheader("Lịch sử")

    for item in st.session_state.chats:
        if st.button(
            "💬 " + item["title"][:30],
            key=item["id"],
            use_container_width=True
        ):
            st.session_state.active_chat = item["id"]
            st.rerun()

    st.divider()

    st.caption(f"Provider: {PROVIDER.upper()}")

    if PROVIDER == "ollama":
        st.caption(f"Model: {OLLAMA_MODEL}")
    else:
        st.caption(f"Model: {GEMINI_MODEL}")

    if st.button("🗑 Xóa tất cả lịch sử"):
        st.session_state.chats = []
        st.session_state.active_chat = None
        save_history()
        st.rerun()


# MAIN
st.title("My AI Assistant")
st.caption("Trợ lý AI cá nhân của bạn")

conversation = get_chat()

# Hiển thị tin nhắn cũ
for msg in conversation["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Nhập câu hỏi
prompt = st.chat_input("Nhập tin nhắn của bạn...")

if prompt:
    conversation["messages"].append({
        "role": "user",
        "content": prompt
    })

    if conversation["title"] == "Cuộc trò chuyện mới":
        conversation["title"] = prompt[:30]

    with st.chat_message("user"):
        st.markdown(prompt)

    save_history()

    with st.chat_message("assistant"):
        with st.spinner("AI đang trả lời..."):
            try:
                answer = chat(
                    conversation["messages"],
                    system=SYSTEM
                )
                st.markdown(answer)

                conversation["messages"].append({
                    "role": "assistant",
                    "content": answer
                })

                save_history()

            except Exception as e:
                st.error(f"Lỗi: {e}")