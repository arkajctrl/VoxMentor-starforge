import streamlit as st
import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
RIME_API_KEY = os.getenv("RIME_API_KEY")

st.set_page_config(page_title="VoxMentor", page_icon="🎙️")
st.title("VoxMentor: AI Interview Coach")
st.write("Type a question below, and the AI interviewer will ask it out loud.")

def generate_rime_audio(text_to_speak):
    url = "https://users.rime.ai/v1/rime-tts"
    headers = {
        "Accept": "audio/wav",
        "Authorization": f"Bearer {RIME_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text_to_speak,
        "speaker": "celeste",
        "modelId": "coda"
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.read()
    except Exception as e:
        st.error(f"Error connecting to Rime AI: {e}")
        return None

question = st.text_area("What should the interviewer ask you?", "Tell me about a time you faced a difficult challenge at work.")

if st.button("Ask Question"):
    if not RIME_API_KEY:
        st.error("Please add your RIME_API_KEY to the .env file.")
    else:
        with st.spinner("Generating voice..."):
            audio_data = generate_rime_audio(question)
            if audio_data:
                st.success("Audio generated successfully!")
                st.audio(audio_data, format="audio/wav")