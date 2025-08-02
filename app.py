import streamlit as st
import speech_recognition as sr
import spacy
import os
from textblob import TextBlob
from googletrans import Translator

# Load spaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
    st.write("spaCy model 'en_core_web_sm' loaded successfully.")
except OSError:
    nlp = None
    st.error("Run: python -m spacy download en_core_web_sm")

# Initialize tools
recognizer = sr.Recognizer()
translator = Translator()

# Recognize speech
def recognize_speech_from_mic(language_code="en-US"):
    mic = sr.Microphone()
    with mic as source:
        st.write("🎙️ Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio, language=language_code)
        st.success(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        st.error("Could not understand audio.")
        return ""
    except sr.RequestError:
        st.error("Request to Google Speech failed.")
        return ""

# Process command
def process_command(command):
    command = command.lower().strip()
    if "add" in command:
        return command.replace("add", "").strip()
    elif "delete" in command:
        return ""
    elif "html" in command:
        return f"<p>{command.replace('html', '').strip()}</p>"
    elif "php" in command:
        return f"<?php echo '{command.replace('php', '').strip()}'; ?>"
    elif "bold" in command:
        return f"**{command.replace('bold', '').strip()}**"
    elif "italic" in command:
        return f"*{command.replace('italic', '').strip()}*"
    else:
        return command

# POS tagging
def pos_tagging(text):
    if not nlp:
        return ["spaCy model not loaded."]
    doc = nlp(text)
    return [f"{token.text} -> {token.pos_}" for token in doc]

# Sentiment analysis
def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    if polarity > 0.1:
        tone = "Positive 😊"
    elif polarity < -0.1:
        tone = "Negative 😠"
    else:
        tone = "Neutral 😐"

    return polarity, subjectivity, tone

# Translate text
def translate_text(text, dest_lang_code):
    try:
        translated = translator.translate(text, dest=dest_lang_code)
        return translated.text
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return text

# File I/O
def save_text_to_file(text, filename):
    with open(filename, 'w') as f:
        f.write(text)

def load_text_from_file(filename):
    with open(filename, 'r') as f:
        return f.read()

# --- Streamlit UI ---
st.title("📝 Voice-Controlled AI Text Editor")
st.caption("Dictate, edit, enhance, and translate text using voice and NLP")

# Language selection
language = st.selectbox("Choose Recognition Language", ["en-US", "es-ES", "fr-FR", "de-DE", "zh-CN"])

# Session state
if 'text' not in st.session_state:
    st.session_state.text = ""
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = -1

def save_to_history():
    st.session_state.history = st.session_state.history[:st.session_state.current_index + 1]
    st.session_state.history.append(st.session_state.text)
    st.session_state.current_index += 1

# Sidebar
with st.sidebar:
    st.header("🎛️ Actions")
    
    if st.button("🎤 Start Dictation"):
        with st.spinner("Listening..."):
            result = recognize_speech_from_mic(language)
            if result:
                processed = process_command(result)
                st.session_state.text += processed
                save_to_history()

    if st.button("🧹 Clear Text"):
        st.session_state.text = ""
        st.session_state.history = []
        st.session_state.current_index = -1
        st.success("Cleared!")

    st.subheader("↩️ Undo / Redo")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Undo"):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1
                st.session_state.text = st.session_state.history[st.session_state.current_index]
    with col2:
        if st.button("Redo"):
            if st.session_state.current_index < len(st.session_state.history) - 1:
                st.session_state.current_index += 1
                st.session_state.text = st.session_state.history[st.session_state.current_index]

    st.subheader("📂 File")
    filename = "text_editor_output.txt"
    if st.button("💾 Save to File"):
        save_text_to_file(st.session_state.text, filename)
        st.success(f"Saved to {filename}")
    if st.button("📁 Load from File"):
        if os.path.exists(filename):
            st.session_state.text = load_text_from_file(filename)
            st.success(f"Loaded from {filename}")
        else:
            st.warning("File not found.")

    st.subheader("📚 NLP Tools")

    if st.button("Analyze Sentiment"):
        if st.session_state.text.strip():
            polarity, subjectivity, tone = analyze_sentiment(st.session_state.text)
            st.write(f"**Tone:** `{tone}`")
            st.write(f"**Polarity:** `{polarity}` (-1 = negative, 1 = positive)")
            st.write(f"**Subjectivity:** `{subjectivity}` (0 = objective, 1 = subjective)")
        else:
            st.warning("Text is empty.")

    if st.button("Show POS Tags"):
        tags = pos_tagging(st.session_state.text)
        st.markdown("### POS Tags:")
        for tag in tags:
            st.markdown(f"- {tag}")

# Text Area
st.subheader("📝 Editor")
text_area = st.text_area("Edit below:", value=st.session_state.text, height=300)

if st.session_state.text != text_area:
    st.session_state.text = text_area
    save_to_history()

# Stats & Preview
st.markdown(f"**Character Count:** `{len(st.session_state.text)}`")

if st.button("🔍 Show Preview"):
    if st.session_state.text.strip():
        st.markdown("### Preview:")
        st.markdown(st.session_state.text)
    else:
        st.warning("Nothing to preview.")

# Translation Section
st.subheader("🌍 Translate Text")
target_language = st.selectbox("Translate to:", ["en", "es", "fr", "de", "zh-cn"], index=0, help="Choose target language")

if st.button("🌐 Translate"):
    if st.session_state.text.strip():
        translated_text = translate_text(st.session_state.text, target_language)
        st.text_area("🔄 Translated Text", value=translated_text, height=200)
    else:
        st.warning("Text is empty.")
