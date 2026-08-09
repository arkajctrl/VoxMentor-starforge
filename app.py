import streamlit as st
import os
import json
import urllib.request
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from groq import Groq

# ---------------------------------------------------------
# 1. PAGE CONFIG & STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="VoxMentor | AI Interview Coach", page_icon="🎙️", layout="wide")

load_dotenv()
RIME_API_KEY = os.getenv("RIME_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_key) if groq_key else None

# Custom CSS styling for a modern look
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; color: #FF4B4B; font-weight: 700; }
    .sub-text { color: #555; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SIDEBAR - CONFIGURATION & RESUME UPLOAD
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/microphone.png", width=100)
    st.title("VoxMentor Setup")
    st.markdown("---")
    
    target_role = st.text_input("Target Job Role", "Software Engineer - AI")
    experience_level = st.selectbox("Experience Level", ["Fresher / Entry-Level", "Mid-Level", "Senior"])
    
    st.markdown("### 📄 Candidate Context")
    resume_text = st.text_area("Paste your Resume / Skills summary here:", "Python, Machine Learning, TensorFlow, Problem Solving")
    
    st.markdown("---")
    st.info("STARFORGE 2026 Submission\nTrack: VoxForge")

# ---------------------------------------------------------
# 3. MAIN APP HEADER
# ---------------------------------------------------------
st.markdown('<p class="main-title">VoxMentor 🎙️</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Your hands-free, voice-first AI interview simulator powered by Qdrant, Groq, and Rime AI.</p>', unsafe_allow_html=True)
st.divider()

# ---------------------------------------------------------
# 4. INITIALIZE SESSION STATE & QDRANT
# ---------------------------------------------------------
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""

@st.cache_resource
def setup_vector_memory():
    q = QdrantClient(":memory:")
    q.create_collection(
        collection_name="question_bank",
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    # Adding dynamic contextual questions
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

# ---------------------------------------------------------
# 5. RIME AI VOICE GENERATOR
# ---------------------------------------------------------
def generate_rime_audio(text_to_speak):
    if not RIME_API_KEY:
        return None
    url = "https://users.rime.ai/v1/rime-tts"
    headers = {
        "Accept": "audio/wav",
        "Authorization": f"Bearer {RIME_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": text_to_speak, "speaker": "celeste", "modelId": "coda"}
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.read()
    except Exception as e:
        st.error(f"Rime API Error: {e}")
        return None

# ---------------------------------------------------------
# 6. INTERVIEW WORKFLOW UI
# ---------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🤖 Interviewer Panel")
    if st.button("🎤 Ask Next Question", type="primary"):
        # Fetch question from Qdrant memory based on role context
        results = qdrant_db.scroll(collection_name="question_bank", limit=3)[0]
        # Pick based on session history length to cycle through questions
        q_index = len(st.session_state.history) % len(results)
        st.session_state.current_question = results[q_index].payload['q']
        
        st.markdown(f"> **Interviewer:** {st.session_state.current_question}")
        
        with st.spinner("Generating natural voice response..."):
            audio_bytes = generate_rime_audio(st.session_state.current_question)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav", autoplay=True)

with col2:
    st.subheader("🗣️ Your Response Panel")
    if st.session_state.current_question:
        st.info("Click the microphone below to record your spoken answer:")
        recorded_audio = st.audio_input("Record audio answer:")
        
        if recorded_audio and client:
            st.success("Audio successfully recorded!")
            with st.spinner("Transcribing via Whisper..."):
                with open("user_speech.wav", "wb") as f:
                    f.write(recorded_audio.getbuffer())
                
                with open("user_speech.wav", "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=audio_file
                    )
                candidate_answer = transcript.text
                st.write(f"**You said:** *{candidate_answer}*")
            
            with st.spinner("Evaluating performance with Llama 3..."):
                prompt = f"Role: {target_role}. Question: '{st.session_state.current_question}'. Candidate Answer: '{candidate_answer}'. Provide concise, direct constructive evaluation and scoring out of 10."
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}]
                )
                feedback = response.choices[0].message.content
                st.markdown(f"**Feedback:** {feedback}")
                
                # Speak feedback back
                feedback_audio = generate_rime_audio(feedback)
                if feedback_audio:
                    st.audio(feedback_audio, format="audio/wav")
        elif recorded_audio and not client:
            st.error("Groq API key is missing from your .env file!")
    else:
        st.warning("Click 'Ask Next Question' on the left to begin the interview.")

# Display Conversation History Log at the bottom
if st.session_state.history:
    st.divider()
    st.subheader("📜 Session Transcript Archive")
    for item in st.session_state.history:
        st.text(item)