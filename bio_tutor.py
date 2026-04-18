import os
from datetime import datetime

import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

# 1. Load the API key securely
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="BioTutor AI", page_icon="🔬")
if not api_key:
    st.error("Missing GEMINI_API_KEY. Add it to your .env file and restart the app.")
    st.stop()

# 2. Configure the Gemini API
genai.configure(api_key=api_key)

# Page styling
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stChatMessage { border-radius: 15px; }
    .stChatMessage div[data-testid="stMarkdownContainer"] p { margin: 0.35rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔬 Modern Biology Tutor")
st.write(
    "Welcome! Let's break down complex biology concepts into easy-to-understand lessons with quizzes, flashcards, and quick summaries."
)

# 3. Define the Tutor's Personality (System Instruction)
system_instruction = (
    "You are a dedicated Secondary School Biology Tutor. "
    "Your goal is to explain concepts clearly using bullet points, bold text for key terms, and helpful analogies. "
    "Always wrap up your explanation with a quick quiz question to test the user's understanding. "
    "If the user asks about a process, explain it step-by-step."
)

# Initialize the model
model = genai.GenerativeModel(
    model_name="models/gemini-3-flash-preview",
    system_instruction=system_instruction,
)

# 4. Manage Session State for Chat History
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = []

if "lesson_summary" not in st.session_state:
    st.session_state.lesson_summary = ""

if "practice_questions" not in st.session_state:
    st.session_state.practice_questions = ""

if "last_export" not in st.session_state:
    st.session_state.last_export = ""

biology_topics = [
    "Photosynthesis",
    "Cell structure",
    "Genetics and DNA",
    "Evolution",
    "Human anatomy",
    "Ecosystems",
]



def send_gemini_message(chat_session, prompt):
    try:
        return chat_session.send_message(prompt)
    except ResourceExhausted as err:
        st.error("Gemini quota exceeded.")
        st.warning(
            "Your tier quota for Gemini has been reached. "
            "Please wait a few minutes before retrying, or upgrade your API plan to continue using the model."
        )
        st.markdown(
            "[Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) | "
            "[Monitor usage](https://ai.dev/rate-limit)"
        )
        return None
    except Exception as err:
        st.error(f"Gemini API error: {err}")
        return None

with st.sidebar:
    st.header("BioTutor Controls")
    st.write("Use the controls to adjust difficulty, generate practice questions, and export your lesson.")

    difficulty = st.selectbox(
        "Choose difficulty",
        ["Beginner", "Intermediate", "Advanced"],
        index=0,
    )

    tutoring_style = st.radio(
        "Tutoring style",
        ["Clear explanation", "Analogy-driven", "Step-by-step process"],
        index=0,
    )

    include_glossary = st.checkbox("Include a short glossary of key terms", value=True)
    include_flashcards = st.checkbox("Generate 3 flashcards after the answer", value=False)

    st.markdown("**Try a topic**")
    for topic in biology_topics:
        if st.button(topic, icon="🔬"):
            query = f"Please explain {topic} in a {difficulty.lower()} level, {tutoring_style.lower()}, and include a quick quiz."
            with st.spinner("Thinking..."):
                assistant_response = send_gemini_message(st.session_state.chat_session, query)
            if assistant_response is not None:
                st.session_state.prompt_history.append(topic)
                st.session_state.messages.append({"role": "user", "content": query})
                st.session_state.messages.append({"role": "assistant", "content": assistant_response.text})
                st.rerun()

    st.write("---")
    st.markdown("**Try asking:**\n- What is photosynthesis?\n- How does DNA replication work?\n- Explain the structure of a cell.")
    st.write("---")

    if st.button("Generate lesson summary", icon="📝"):
        if not st.session_state.messages:
            st.warning("Ask at least one question before generating a summary.")
        else:
            summary_prompt = (
                "Review the following biology tutoring conversation and provide a brief lesson summary in three bullet points, "
                "followed by one key takeaway."
                "\n\nConversation:\n"
            )
            for message in st.session_state.messages:
                role = message["role"].title()
                summary_prompt += f"{role}: {message['content']}\n"

            with st.spinner("Generating lesson summary..."):
                summary_chat = model.start_chat(history=[])
                summary_response = send_gemini_message(summary_chat, summary_prompt)
                if summary_response is not None:
                    st.session_state.lesson_summary = summary_response.text

    if st.button("Generate practice questions", icon="❓"):
        if not st.session_state.messages:
            st.warning("Ask a question first to generate context-aware practice questions.")
        else:
            practice_prompt = (
                "Based on the biology tutoring conversation below, create 5 multiple-choice review questions. "
                "Provide 4 answer options for each question and clearly indicate the correct answer.\n\nConversation:\n"
            )
            for message in st.session_state.messages:
                role = message["role"].title()
                practice_prompt += f"{role}: {message['content']}\n"

            with st.spinner("Generating practice questions..."):
                practice_chat = model.start_chat(history=[])
                practice_response = send_gemini_message(practice_chat, practice_prompt)
                if practice_response is not None:
                    st.session_state.practice_questions = practice_response.text

    if st.session_state.lesson_summary:
        st.write("---")
        st.subheader("Lesson summary")
        st.text_area("Copy or edit the summary", st.session_state.lesson_summary, height=180)
        st.download_button(
            "Download summary",
            st.session_state.lesson_summary,
            "lesson_summary.txt",
            mime="text/plain",
        )

    if st.session_state.practice_questions:
        st.write("---")
        st.subheader("Practice questions")
        st.text_area("Review questions", st.session_state.practice_questions, height=220)
        st.download_button(
            "Download practice questions",
            st.session_state.practice_questions,
            "practice_questions.txt",
            mime="text/plain",
        )

    if st.button("Download conversation", icon="💾"):
        if not st.session_state.messages:
            st.warning("There is no conversation to download yet.")
        else:
            transcript = "\n".join(
                f"{message['role'].title()}: {message['content']}" for message in st.session_state.messages
            )
            st.session_state.last_export = transcript

    if st.session_state.last_export:
        st.download_button(
            "Download transcript",
            st.session_state.last_export,
            f"bio_tutor_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
        )

    if st.button("Clear Conversation", icon="🗑️"):
        st.session_state.messages = []
        st.session_state.prompt_history = []
        st.session_state.lesson_summary = ""
        st.session_state.practice_questions = ""
        st.session_state.last_export = ""
        st.session_state.chat_session = model.start_chat(history=[])
        st.rerun()

    st.write("---")
    st.markdown("<small>Powered by Gemini AI Models and can make mistakes</small>", unsafe_allow_html=True)

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Chat Input and Logic
if prompt := st.chat_input("Ask me about any biology concept"):
    st.session_state.prompt_history.append(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    user_prompt = (
        f"[Difficulty: {difficulty}] [Style: {tutoring_style}] {prompt}"
    )
    if include_glossary:
        user_prompt += " Please include a short glossary of key biology terms at the end."
    if include_flashcards:
        user_prompt += " Also generate 3 short flashcards after your explanation."

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = send_gemini_message(st.session_state.chat_session, user_prompt)
        if response is not None:
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
