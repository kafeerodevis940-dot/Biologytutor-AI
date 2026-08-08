import os
import urllib.parse
from datetime import datetime
import streamlit as st
import google.generativeai as genai
from openai import OpenAI  
from dotenv import load_dotenv

load_dotenv()

# These lines securely extract the keys from system memory without revealing them in the code
gemini_key = os.getenv("GEMINI_API_KEY")
openrouter_key = os.getenv("OPENROUTER_API_KEY")

st.set_page_config(
    page_title="BioTutor AI · Derlish",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Soft validation: Warn instead of hard stopping so the UI still loads
if not gemini_key:
    st.sidebar.warning("⚠️ GEMINI_API_KEY missing in .env (Image upload will fail).")
else:
    genai.configure(api_key=gemini_key)

if not openrouter_key:
    st.sidebar.error("❌ OPENROUTER_API_KEY missing in .env. Text chat will not work.")
    st.stop()

# Initialize OpenRouter client via OpenAI's SDK infrastructure
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_key,
)

# ── 2. Global CSS with Coral Reef Background ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght=700&family=DM+Sans:wght=300;400;500&display=swap');

:root {
    --green-deep:   #0d3320;
    --green-mid:    #1a5e3a;
    --green-bright: #2ecc71;
    --green-pale:   #d4edda;
    --gold:         #c9a84c;
    --text-dark:    #0d2016;
    --text-muted:   #4a7060;
    --radius:       16px;
    --shadow:       0 8px 32px rgba(0, 0, 0, 0.2);
}

.stApp {
    background-image: linear-gradient(rgba(13, 51, 32, 0.85), rgba(13, 51, 32, 0.85)), 
                      url('https://images.unsplash.com/photo-1546026423-cc4642628d2b?q=80&w=2574&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #ffffff;
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Hero banner (Frosted Glass Glassmorphism) ── */
.hero {
    background: rgba(13, 51, 32, 0.75);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    padding: 2.4rem 2.8rem 2rem;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow);
}
.hero::before {
    content: "🐠";
    position: absolute;
    right: 2rem; top: 50%;
    transform: translateY(-50%);
    font-size: 6rem;
    opacity: .15;
}
.hero h1 {
    font-family: 'Playfair Display', serif;
    color: #fff;
    font-size: 2.4rem;
    margin: 0 0 .4rem;
    letter-spacing: -.5px;
}
.hero .sub {
    color: #a8d5b8;
    font-size: .95rem;
    font-weight: 300;
    margin: 0;
}
.hero .badge {
    display: inline-block;
    background: var(--gold);
    color: var(--green-deep);
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: .25rem .7rem;
    border-radius: 50px;
    margin-bottom: .8rem;
}

[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: .5rem 0 !important;
}

[data-testid="stChatMessage"][data-testid*="user"],
div[class*="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div:last-child {
    background: var(--green-deep) !important;
    color: #fff !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: .9rem 1.2rem !important;
    margin-left: auto;
    max-width: 80%;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

div[class*="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) > div:last-child {
    background: rgba(13, 51, 32, 0.92) !important; /* Changed to dark green */
    color: #ffffff !important;
    border: 1.5px solid var(--green-pale) !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: .9rem 1.2rem !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    max-width: 85%;
}
}

[data-testid="stChatInputContainer"] {
    background: rgba(255, 255, 255, 0.95) !important;
    border: 2px solid var(--green-pale) !important;
    border-radius: 50px !important;
    box-shadow: var(--shadow) !important;
    padding: .2rem .6rem !important;
}

[data-testid="stSidebar"] {
    background: rgba(13, 51, 32, 0.85) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}
[data-testid="stSidebar"] * { color: #c8e6d2 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #fff !important;
    font-family: 'Playfair Display', serif !important;
}
[data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stRadio label, [data-testid="stSidebar"] .stCheckbox label {
    color: #a8d5b8 !important;
    font-size: .88rem !important;
}

[data-testid="stSidebar"] button {
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: #fff !important;
    border-radius: 10px !important;
    width: 100%;
    transition: all .2s !important;
    font-size: .85rem !important;
}
[data-testid="stSidebar"] button:hover {
    background: var(--green-bright) !important;
    color: var(--green-deep) !important;
    border-color: var(--green-bright) !important;
    box-shadow: 0 0 12px rgba(46,204,113,0.4);
}

.stat-row { display: flex; gap: 1rem; margin-bottom: 1.4rem; }
.stat-card {
    background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(5px);
    border: 1.5px solid var(--green-pale); border-radius: var(--radius); padding: 1rem 1.4rem; flex: 1;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}
.stat-card .label { font-size: .78rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: .25rem; }
.stat-card .value { font-family: 'Playfair Display', serif; font-size: 1.6rem; color: var(--green-mid); }

.info-box {
    background: rgba(232, 245, 238, 0.9);
    border-left: 4px solid var(--green-bright); padding: .9rem 1.2rem; margin-bottom: 1rem;
    font-size: .88rem; color: var(--text-muted); border-radius: 0 var(--radius) var(--radius) 0;
}
.divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); margin: 1.2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── 3. System Instructions ────────────────────────────────────────────────────
SYSTEM_INSTRUCTION = (
    "You are a dedicated Secondary School Biology Tutor for the Uganda curriculum (UCE/UACE). "
    "Explain concepts clearly using bullet points, bold text for key terms, and helpful analogies. "
    "Always wrap up your explanation with a quick quiz question to test the user's understanding. "
    "If the user asks about a process or diagram, explain it step-by-step. "
    "Always include examples relevant to the Uganda secondary school curriculum."
    "You re powered by open ai and gemini but created by derek."
)

# ── 4. Session State ──────────────────────────────────────────────────────────
for key, default in {
    "messages": [],
    "prompt_history": [],
    "lesson_summary": "",
    "practice_questions": "",
    "last_export": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

biology_topics = [
    "Photosynthesis", "Cell Structure", "Genetics & DNA",
    "Evolution", "Human Anatomy", "Ecosystems",
]

# ── 5. LLM Call Handlers ──────────────────────────────────────────────────────
def ask_openrouter(current_prompt):
    """Handles text chat queries completely for free using OpenRouter."""
    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    
    for msg in st.session_state.messages:
        role = "assistant" if msg["role"] == "assistant" else "user"
        messages.append({"role": role, "content": msg["content"]})
        
    messages.append({"role": "user", "content": current_prompt})
    
    try:
        # Utilizing 'openrouter/free' to automatically switch between available free system instances
        completion = openrouter_client.chat.completions.create(
            model="openrouter/free",
            messages=messages,
            extra_headers={
                "HTTP-Referer": "http://localhost:8501", 
                "X-OpenRouter-Title": "BioTutor Derlish",
            }
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"OpenRouter Free-tier API Error: {e}")
        return None

def ask_gemini_vision(image_file, prompt):
    """Handles multi-modal image analysis using Gemini 2.5."""
    if not gemini_key:
        st.error("Cannot process image. Gemini API key is missing or invalid.")
        return None
        
    try:
        import PIL.Image
        img = PIL.Image.open(image_file)
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nUser Question about this image: {prompt}"
        
        vision_model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = vision_model.generate_content([full_prompt, img])
        return response.text
    except Exception as e:
        st.error(f"Gemini Vision Error: {e}")
        return None

# ── 6. Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔬 BioTutor AI")
    st.markdown("<small style='color:#6aaa84'>Created by Derek Powered by OpenRouter Free & Gemini Vision</small>", unsafe_allow_html=True)
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    st.markdown("#### 🖼️ Upload Biological Diagram")
    uploaded_image = st.file_uploader("Upload cell diagrams, UNEB papers, etc.", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded Diagram", use_container_width=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("#### ⚙️ Settings")
    difficulty = st.selectbox("Difficulty level", ["Beginner", "Intermediate", "Advanced"])
    tutoring_style = st.radio("Tutoring style", ["Clear explanation", "Analogy-driven", "Step-by-step process"])
    include_glossary = st.checkbox("Include key terms glossary", value=True)
    include_flashcards = st.checkbox("Generate 3 flashcards", value=False)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("#### 📚 Quick Topics")

    for topic in biology_topics:
        if st.button(f"🔬 {topic}", key=f"topic_{topic}"):
            query = f"Please explain {topic} at a {difficulty.lower()} level using a {tutoring_style.lower()} approach. Include a quick quiz at the end."
            with st.spinner("OpenRouter is routing to a free model..."):
                resp_text = ask_openrouter(query)
            if resp_text:
                st.session_state.prompt_history.append(topic)
                st.session_state.messages.append({"role": "user", "content": f"Quick Topic: {topic}"})
                st.session_state.messages.append({"role": "assistant", "content": resp_text})
                st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("#### 🛠️ Tools")

    if st.button("📝 Generate Lesson Summary"):
        if not st.session_state.messages:
            st.warning("Ask at least one question first.")
        else:
            prompt = "Summarise this biology tutoring conversation in 3 bullet points plus one key takeaway.\n\n"
            for m in st.session_state.messages:
                prompt += f"{m['role'].title()}: {m['content']}\n"
            with st.spinner("Summarising..."):
                try:
                    res = openrouter_client.chat.completions.create(model="openrouter/free", messages=[{"role": "user", "content": prompt}])
                    st.session_state.lesson_summary = res.choices[0].message.content
                except Exception as e: st.error(f"{e}")

    if st.button("❓ Generate Practice Questions"):
        if not st.session_state.messages: st.warning("Ask a question first.")
        else:
            prompt = "Based on this conversation, create 5 multiple-choice questions with 4 options each. Mark the correct answer.\n\n"
            for m in st.session_state.messages: prompt += f"{m['role'].title()}: {m['content']}\n"
            with st.spinner("Creating questions..."):
                try:
                    res = openrouter_client.chat.completions.create(model="openrouter/free", messages=[{"role": "user", "content": prompt}])
                    st.session_state.practice_questions = res.choices[0].message.content
                except Exception as e: st.error(f"{e}")

    if st.session_state.lesson_summary:
        st.markdown("**Lesson Summary**")
        st.text_area("", st.session_state.lesson_summary, height=160, key="sum_area")

    if st.session_state.practice_questions:
        st.markdown("**Practice Questions**")
        st.text_area("", st.session_state.practice_questions, height=200, key="pq_area")

    if st.button("🗑️ Clear Conversation"):
        for k in ["messages", "prompt_history", "lesson_summary", "practice_questions", "last_export"]:
            st.session_state[k] = [] if k in ["messages", "prompt_history"] else ""
        st.rerun()

    # ── New Section: Image Generation ──
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("#### 🎨 Draw a Biology Diagram")
    
    image_prompt = st.text_input("What should I draw? (e.g., A plant cell)")
    
    if st.button("Generate Image"):
        if not image_prompt:
            st.warning("Please type what you want me to draw first.")
        else:
            with st.spinner(f"Drawing {image_prompt}..."):
                # Safely encode the text for a URL
                safe_prompt = urllib.parse.quote(image_prompt)
                # Use a free, no-API-key image generator
                image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true"
                
                # Display the image in the sidebar
                st.image(image_url, caption=image_prompt, use_container_width=True)

# ── 7. Main Area ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="badge"> Secondary Curriculum </div>
   <h1>🔬 Derlish Biology Tutor</h1>
    <p class="sub">Explore the wonders of biology with completely free text answers and diagram recognition.</p>
</div>
""", unsafe_allow_html=True)

# Stat cards
msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
topic_count = len(set(st.session_state.prompt_history))
st.markdown(f"""
<div class="stat-row">
    <div class="stat-card"><div class="label">Questions Asked</div><div class="value">{msg_count}</div></div>
    <div class="stat-card"><div class="label">Topics Explored</div><div class="value">{topic_count}</div></div>
    <div class="stat-card"><div class="label">Difficulty</div><div class="value" style="font-size:1.1rem;margin-top:.3rem">{difficulty}</div></div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class="info-box">
        💡 <strong> Text generation is run completely free! Try uploading a diagram or type your question below.
    </div>
    """, unsafe_allow_html=True)

# Render Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── 8. Chat Input & Processing ────────────────────────────────────────────────
if prompt := st.chat_input("Ask about any biology concept or uploaded image…"):
    st.session_state.prompt_history.append(prompt)
    
    user_prompt = f"[Difficulty: {difficulty}] [Style: {tutoring_style}] {prompt}"
    if include_glossary:
        user_prompt += " Include a short glossary of key biology terms at the end."
    if include_flashcards:
        user_prompt += " Also generate 3 short flashcards after your explanation."

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing framework..."):
            if uploaded_image is not None:
                st.caption("🔄 Analyzing image with Gemini Vision...")
                response_text = ask_gemini_vision(uploaded_image, user_prompt)
            else:
                st.caption("🌐 Routing text request to OpenRouter (Free)...")
                response_text = ask_openrouter(user_prompt)
        
        if response_text:
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})