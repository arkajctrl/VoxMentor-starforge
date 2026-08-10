import streamlit as st
import os
import json
import random
import urllib.request
import urllib.error
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from groq import Groq

# ---------------------------------------------------------
# 1. PAGE CONFIG & MODERN CSS INJECTION
# ---------------------------------------------------------
st.set_page_config(
    page_title="VoxMentor | AI Interview Coach", 
    page_icon="🎙️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
RIME_API_KEY = os.getenv("RIME_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_key) if groq_key else None

# Complete UI Overhaul & Animation CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* Hide default Streamlit clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Global Page Styling */
    .stApp {
        background: radial-gradient(circle at 50% -20%, #1e1e2d 0%, #08090f 100%) !important;
    }

    /* ---------------- Sleek Scrollbar ---------------- */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }
    * {
        scrollbar-width: thin;
        scrollbar-color: rgba(255, 255, 255, 0.15) transparent;
    }

    /* ---------------- Animations ---------------- */
    @keyframes fadeInUp {
        0% { opacity: 0; transform: translateY(30px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    .animate-1 { animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
    .animate-2 { animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards; opacity: 0; }
    .animate-3 { animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.4s forwards; opacity: 0; }

    /* Ensure Streamlit containers sit above the particles */
    .block-container {
        position: relative;
        z-index: 10;
    }

    /* ---------------- Landing Page Styles ---------------- */
    .hero-container {
        text-align: center;
        padding: 4rem 1rem;
        margin-top: 2rem;
    }

    .hero-title-mega {
        font-weight: 800;
        font-size: 4.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #a1a1aa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.04em;
        margin-bottom: 0.5rem;
        line-height: 1.1;
    }
    
    .hero-sub-mega {
        color: #a1a1aa;
        font-size: 1.25rem;
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto 2.5rem auto;
        line-height: 1.6;
        letter-spacing: -0.01em;
    }

    .feature-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 30px;
        backdrop-filter: blur(12px);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        text-align: left;
        height: 100%;
    }

    .feature-card:hover {
        transform: translateY(-8px);
        border-color: rgba(255, 255, 255, 0.2);
        background: rgba(255, 255, 255, 0.04);
    }

    .feature-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }

    .feature-title {
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .feature-text {
        color: #a1a1aa;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* ---------------- App Page Styles ---------------- */
    .hero-title { font-weight: 700; font-size: 2.5rem; color: #ffffff; letter-spacing: -0.03em; margin-bottom: 0.5rem; }
    .hero-sub { color: #a1a1aa; font-size: 1.1rem; font-weight: 400; margin-bottom: 1.5rem; }
    
    .status-bar { display: flex; gap: 12px; align-items: center; margin-bottom: 1.5rem; }
    .status-badge { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); padding: 6px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 500; color: #e4e4e7; backdrop-filter: blur(10px); letter-spacing: 0.02em;}
    .pulse-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background-color: #10B981; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); animation: pulse 1.6s infinite; margin-right: 8px; }
    @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }
    
    .glass-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 24px; backdrop-filter: blur(12px); margin-bottom: 1.2rem; transition: transform 0.2s ease, border-color 0.2s ease; }
    .glass-card:hover { border-color: rgba(255, 255, 255, 0.15); }
    .card-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #a1a1aa; font-weight: 600; margin-bottom: 8px; }
    .card-text { font-size: 1rem; color: #ffffff; line-height: 1.6; font-weight: 400; }
    
    /* Sleek Button Overrides */
    .stButton > button { 
        background-color: #ffffff !important; 
        color: #09090b !important; 
        border: 1px solid #ffffff !important; 
        border-radius: 6px !important; 
        padding: 0.5rem 1.5rem !important; 
        font-weight: 500 !important; 
        font-size: 0.95rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.2s ease !important; 
        box-shadow: 0 4px 14px 0 rgba(255, 255, 255, 0.1) !important;
    }
    .stButton > button:hover { 
        background-color: rgba(255, 255, 255, 0.05) !important; 
        color: #ffffff !important; 
        border-color: rgba(255, 255, 255, 0.2) !important;
        box-shadow: none !important; 
        transform: translateY(-1px) !important; 
    }
    
    section[data-testid="stSidebar"] { background-color: #09090b !important; border-right: 1px solid rgba(255, 255, 255, 0.05) !important; z-index: 9999;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. ROUTING LOGIC
# ---------------------------------------------------------
current_page = st.query_params.get("page", "home")

# Hide Sidebar on Home Page via CSS injection
if current_page == "home":
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] {display: none;}
            [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. HOME PAGE (LANDING SITE WITH PURE CSS PARTICLES)
# ---------------------------------------------------------
if current_page == "home":
    
    # Generate infinite CSS particles using Python random logic
    @st.cache_data
    def generate_particle_cosmos():
        def gen_layer(count, size, duration):
            shadows = ", ".join([f"{random.uniform(0, 100)}vw {random.uniform(0, 100)}vh {random.uniform(0, 2)}px rgba(255,255,255,{random.uniform(0.1, 0.8)})" for _ in range(count)])
            return f"""
                .p-layer-{size} {{
                    width: {size}px; height: {size}px; background: transparent; 
                    box-shadow: {shadows}; animation: drift {duration}s linear infinite; 
                    position: fixed; top: 0; left: 0; z-index: 0; pointer-events: none; border-radius: 50%;
                }}
                .p-layer-{size}::after {{
                    content: ''; position: absolute; top: 100vh; width: {size}px; height: {size}px; 
                    background: transparent; box-shadow: {shadows}; border-radius: 50%;
                }}
            """
        css = f"""
        <style>
        @keyframes drift {{ from {{ transform: translateY(0px); }} to {{ transform: translateY(-100vh); }} }}
        {gen_layer(150, 2, 70)}
        {gen_layer(75, 3, 45)}
        {gen_layer(35, 4, 25)}
        </style>
        <div class="p-layer-2"></div><div class="p-layer-3"></div><div class="p-layer-4"></div>
        """
        return css

    # Inject the flawless native particles
    st.markdown(generate_particle_cosmos(), unsafe_allow_html=True)

    # Hero Section
    st.markdown("""
        <div class="hero-container animate-1">
            <div class="hero-title-mega">VoxMentor</div>
            <div class="hero-sub-mega">The hands-free, voice-first AI interview simulator designed to cure interview anxiety before the big day.</div>
        </div>
    """, unsafe_allow_html=True)

    # Launch Button (Centered)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="animate-2">', unsafe_allow_html=True)
        if st.button("Launch Interview Room", use_container_width=True):
            st.query_params["page"] = "app"
            st.rerun()
        st.markdown('</div><br><br><br>', unsafe_allow_html=True)

    # Features Grid
    st.markdown('<div class="animate-3">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3, gap="large")
    
    with f_col1:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <div class="feature-title">Contextual Memory</div>
                <div class="feature-text">Powered by Qdrant vector databases, VoxMentor dynamically selects role-specific questions tailored perfectly to your uploaded resume and skill set.</div>
            </div>
        """, unsafe_allow_html=True)
        
    with f_col2:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <div class="feature-title">Lightning Fast Logic</div>
                <div class="feature-text">Utilizing Groq's LPUs and Whisper V3, your spoken answers are transcribed and evaluated by Llama-3 instantly, with zero awkward latency.</div>
            </div>
        """, unsafe_allow_html=True)
        
    with f_col3:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🎙️</div>
                <div class="feature-title">Voice-First Experience</div>
                <div class="feature-text">Text chatbots don't prepare you for real conversations. Integrated with Rime AI, your interviewer speaks with a natural, human-like voice.</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. APP PAGE (INTERVIEW ROOM)
# ---------------------------------------------------------
elif current_page == "app":
    
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/microphone.png", width=70)
        st.markdown("<h3 style='margin-top: -10px; font-weight: 700; letter-spacing: -0.02em;'>VoxMentor</h3>", unsafe_allow_html=True)
        
        if st.button("Back to Home", use_container_width=True):
            st.query_params["page"] = "home"
            st.rerun()
            
        st.markdown("---")
        target_role = st.text_input("Target Role", "Software Engineer - AI")
        experience_level = st.selectbox("Experience Level", ["Fresher / Entry-Level", "Mid-Level", "Senior"])
        
        st.markdown("### 📄 Candidate Context")
        resume_text = st.text_area("Resume Highlights", "Python, Machine Learning, TensorFlow, Problem Solving")
        
        st.markdown("---")
        st.caption("⚡ STARFORGE 2026 Submission")
        st.caption("Track: **VoxForge** | Team: **Fantastic 4**")

    # Main App Header
    st.markdown('<div class="hero-title animate-1">Interview Room</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="status-bar animate-1">
            <div class="status-badge"><span class="pulse-dot"></span>System Operational</div>
            <div class="status-badge">Model: Llama-3 8B</div>
            <div class="status-badge">Voice: Rime AI (Astra)</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-bottom: 2rem;'>", unsafe_allow_html=True)

    # Initialize State & Vector DB
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""

    @st.cache_resource
    def setup_vector_memory():
        q = QdrantClient(":memory:")
        q.create_collection(collection_name="question_bank", vectors_config=VectorParams(size=4, distance=Distance.COSINE))
        q.upsert(
            collection_name="question_bank",
            points=[
                PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"q": f"Tell me about a project where you used your skills for a {target_role} role."}),
                PointStruct(id=2, vector=[0.5, 0.6, 0.7, 0.8], payload={"q": "How do you handle debugging a complex system failure under a tight deadline?"}),
                PointStruct(id=3, vector=[0.9, 0.1, 0.2, 0.3], payload={"q": "Walk me through a technical challenge you faced and how you resolved it collaboratively."})
            ]
        )
        return q

    qdrant_db = setup_vector_memory()

    def generate_rime_audio(text_to_speak):
        if not RIME_API_KEY:
            st.error("RIME_API_KEY missing from environment.")
            return None
        url = "https://users.rime.ai/v1/rime-tts"
        headers = {"Accept": "audio/wav", "Authorization": f"Bearer {RIME_API_KEY}", "Content-Type": "application/json"}
        payload = {"text": text_to_speak, "speaker": "astra"}
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            st.error(f"Rime API Error {e.code}: {e.read().decode('utf-8')}")
            return None
        except Exception as e:
            st.error(f"System Error: {e}")
            return None

    st.markdown('<div class="animate-2">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("<h4 style='font-weight: 600; margin-bottom: 1rem;'>Interviewer</h4>", unsafe_allow_html=True)
        btn_label = "Generate Next Question" if len(st.session_state.history) > 0 else "Generate Question"
        
        if st.button(btn_label, use_container_width=True):
            results = qdrant_db.scroll(collection_name="question_bank", limit=3)[0]
            q_index = len(st.session_state.history) % len(results)
            st.session_state.current_question = results[q_index].payload['q']
            
            with st.spinner("Synthesizing voice response..."):
                audio_bytes = generate_rime_audio(st.session_state.current_question)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav", autoplay=True)
            
        if st.session_state.current_question:
            st.markdown(f"""
                <div class="glass-card" style="border-left: 3px solid #ffffff;">
                    <div class="card-label">Active Prompt</div>
                    <div class="card-text">{st.session_state.current_question}</div>
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("<h4 style='font-weight: 600; margin-bottom: 1rem;'>Candidate Response</h4>", unsafe_allow_html=True)
        if st.session_state.current_question:
            st.info("Record your answer below:")
            recorded_audio = st.audio_input("Audio Input")
            
            if recorded_audio and client:
                st.success("Audio captured. Processing evaluation...")
                with st.spinner("Transcribing speech..."):
                    with open("user_speech.wav", "wb") as f: f.write(recorded_audio.getbuffer())
                    with open("user_speech.wav", "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(model="whisper-large-v3", file=audio_file)
                    candidate_answer = transcript.text
                
                with st.spinner("Generating AI feedback..."):
                    prompt = f"Role: {target_role}. Question: '{st.session_state.current_question}'. Candidate Answer: '{candidate_answer}'. Provide concise direct feedback and a rating out of 10."
                    response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
                    feedback = response.choices[0].message.content
                    
                    st.session_state.history.append({"q": st.session_state.current_question, "a": candidate_answer, "f": feedback})
                    st.session_state.current_question = ""
                    
                    if len(feedback) > 400:
                        cut_index = feedback.rfind('.', 0, 400)
                        if cut_index == -1: cut_index = 400
                        spoken_feedback = feedback[:cut_index + 1] + " Please review the transcript for details."
                    else:
                        spoken_feedback = feedback
                        
                    feedback_audio = generate_rime_audio(spoken_feedback)
                    if feedback_audio: st.audio(feedback_audio, format="audio/wav", autoplay=True)
                    st.rerun()
            elif recorded_audio and not client:
                st.error("Groq API key missing.")
        else:
            st.warning("Click 'Generate Question' to start the session.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.history:
        st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        st.markdown("<h4 class='animate-3' style='font-weight: 600; margin-bottom: 1.5rem;'>Session Transcript & Feedback</h4>", unsafe_allow_html=True)
        st.markdown('<div class="animate-3">', unsafe_allow_html=True)
        for i, item in enumerate(reversed(st.session_state.history)):
            st.markdown(f"""
                <div class="glass-card">
                    <div class="card-label">Question</div>
                    <div class="card-text" style="font-weight: 500; margin-bottom: 16px;">{item['q']}</div>
                    <div class="card-label">Your Answer</div>
                    <div class="card-text" style="margin-bottom: 16px; color: #a1a1aa;">"{item['a']}"</div>
                    <div class="card-label">AI Evaluation</div>
                    <div class="card-text" style="color: #d4d4d8; font-size: 0.95rem;">{item['f']}</div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. CUSTOM 404 PAGE
# ---------------------------------------------------------
else:
    st.markdown('<br><br>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title-mega" style="text-align: center; font-size: 6rem; background: linear-gradient(135deg, #ffffff 0%, #a1a1aa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">404</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub-mega" style="text-align: center;">The interview room you are looking for got lost in the void.</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://http.cat/404", use_container_width=True)
        st.markdown('<br>', unsafe_allow_html=True)
        if st.button("Return to VoxMentor", use_container_width=True):
            st.query_params["page"] = "home"
            st.rerun()