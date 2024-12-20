import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
from typing import Dict, List
import json
from dataclasses import dataclass
import io
from pathlib import Path
import requests

@dataclass
class Personality:
    name: str
    description: str
    system_prompt: str
    avatar: str
    model: str  
PERSONALITIES = {
    "harlow": Personality(
        name="Harlow",
        description="A chill, laid-back character who maintains composure in any situation",
        system_prompt="You are Harlow, a very relaxed and composed individual. You respond to situations calmly and diplomatically. You rarely show extreme emotions and prefer to take things as they come.",
        avatar="🧑‍🦰",
        model="mistral" 
    ),
    "harvey": Personality(
        name="Harvey",
        description="A confident and intelligent advisor who provides accurate suggestions",
        system_prompt="You are Harvey, a knowledgeable and self-assured individual. You provide well-thought-out advice and accurate suggestions based on your expertise. You speak with authority but remain approachable.",
        avatar="👨‍💼",
        model="llama2"
    )
}

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def record_audio(self) -> str:
        with sr.Microphone() as source:
            st.write("Listening...")
            audio = self.recognizer.listen(source)
            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except Exception as e:
                st.error(f"Error: {str(e)}")
                return ""

class ChatHandler:
    def __init__(self):
        self.messages = []
        self.base_url = "http://localhost:11434/api/chat"

    def get_response(self, personality: Personality, user_input: str) -> str:
        if not self.messages:
            self.messages = [{"role": "system", "content": personality.system_prompt}]
        
        self.messages.append({"role": "user", "content": user_input})
        
        try:
            response = requests.post(
                self.base_url,
                json={
                    "model": personality.model,
                    "messages": self.messages,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                ai_response = response.json()["message"]["content"]
                self.messages.append({"role": "assistant", "content": ai_response})
                return ai_response
            else:
                error_msg = f"Error: API returned status code {response.status_code}"
                st.error(error_msg)
                return error_msg
                
        except requests.exceptions.ConnectionError:
            error_msg = "Error: Could not connect to Ollama. Make sure Ollama is running on localhost:11434"
            st.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            st.error(error_msg)
            return error_msg

def text_to_speech(text: str, output_file: str = "response.mp3"):
    tts = gTTS(text=text, lang='en')
    tts.save(output_file)
    return output_file

def main():
    st.set_page_config(page_title="AI Personality Chat", layout="wide")
    
    if "selected_personality" not in st.session_state:
        st.session_state.selected_personality = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    chat_handler = ChatHandler()

    st.sidebar.title("Choose a Personality")
    
    cols = st.sidebar.columns(len(PERSONALITIES))
    for idx, (key, personality) in enumerate(PERSONALITIES.items()):
        with cols[idx]:
            if st.button(
                f"{personality.avatar}\n{personality.name}\n({personality.model})",
                key=f"btn_{personality.name}",
                use_container_width=True
            ):
                st.session_state.selected_personality = personality

    st.title("AI Personality Chat")
    
    if st.session_state.selected_personality:
        st.subheader(f"Chatting with {st.session_state.selected_personality.name}")
        st.write(st.session_state.selected_personality.description)

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if st.button("🎤 Start Recording"):
            user_input = voice_handler.record_audio()
            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                ai_response = chat_handler.get_response(st.session_state.selected_personality, user_input)
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                
                audio_file = text_to_speech(ai_response)
                st.audio(audio_file)

        user_input = st.chat_input("Type your message here...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            ai_response = chat_handler.get_response(st.session_state.selected_personality, user_input)
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            
            audio_file = text_to_speech(ai_response)
            st.audio(audio_file)

    else:
        st.info("Please select a personality from the sidebar to start chatting.")

if __name__ == "__main__":
    main()