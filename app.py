import streamlit as st
import os
import json
import urllib.request
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from groq import Groq

# ---------------------------------------------------------
# 1. INITIALIZATION & API KEYS
# ---------------------------------------------------------
load_dotenv()
RIME_API_KEY = os.getenv("RIME_API_KEY")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="VoxMentor", page_icon="🎙️")
st.title("VoxMentor: AI Interview Coach")

# ---------------------------------------------------------
# 2. QDRANT DATABASE (MEMORY & CONTEXT)
# ---------------------------------------------------------
@st.cache_resource
def setup_qdrant():
    q = QdrantClient(":memory:")
    q.create_collection(
        collection_name="questions",
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    q.upsert(
        collection_name="questions",
        points=[
            PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"q": "Tell me about a time you failed and how you handled it."}),
            PointStruct(id=2, vector=[0.5, 0.6, 0.7, 0.8], payload={"q": "Why should we hire you over other candidates?"})
        ]
    )
    return q

qdrant = setup_qdrant()

# ---------------------------------------------------------
# 3. RIME AI VOICE GENERATOR (TEXT-TO-SPEECH)
# ---------------------------------------------------------
def generate_rime_audio(text_to_speak):
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
# 4. THE INTERVIEW WORKFLOW
# ---------------------------------------------------------
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""

st.subheader("Step 1: The Interviewer Asks a Question")
if st.button("Fetch Next Question from Database"):
    results = qdrant.scroll(collection_name="questions", limit=1)[0]
    st.session_state.current_question = results[0].payload['q']
    
    st.write(f"**Interviewer:** {st.session_state.current_question}")
    
    with st.spinner("Interviewer is speaking..."):
        audio = generate_rime_audio(st.session_state.current_question)
        if audio:
            st.audio(audio, format="audio/wav", autoplay=True)

st.divider()

if st.session_state.current_question:
    st.subheader("Step 2: Answer Out Loud")
    st.info("Click the microphone to record your answer.")
    
    recorded_audio = st.audio_input("Record your answer:")
    
    if recorded_audio:
        st.success("Audio captured!")
        
        with st.spinner("Transcribing your answer..."):
            with open("temp_answer.wav", "wb") as f:
                f.write(recorded_audio.getbuffer())
            
            with open("temp_answer.wav", "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file
                )
            candidate_text = transcription.text
            st.write(f"**You said:** {candidate_text}")
        
        with st.spinner("AI is evaluating your answer..."):
            prompt = f"The interview question was: '{st.session_state.current_question}'. The candidate answered verbally: '{candidate_text}'. Give them one short sentence of praise, and one short sentence of constructive feedback on their answer."
            
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )
            
            feedback = completion.choices[0].message.content
            st.write(f"**Interviewer Feedback:** {feedback}")
            
            feedback_audio = generate_rime_audio(feedback)
            if feedback_audio:
                st.audio(feedback_audio, format="audio/wav", autoplay=True)