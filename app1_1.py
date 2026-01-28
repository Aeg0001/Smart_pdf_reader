import streamlit as st
import fitz  # PyMuPDF
import re
from gtts import gTTS
import tempfile
import os

# -------------------------------
# PDF Extraction
# -------------------------------
def extract_text_from_pdf(pdf_file):
    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

# -------------------------------
# Text normalization
# -------------------------------
def normalize_text(text):
    text = re.sub(r'\s+', ' ', text)
    replacements = {
        "HEC-RAS": "H E C R A S",
        "SWMM": "S W M M",
        "β": "beta",
        "α": "alpha",
        "μ": "mu",
        "°C": "degrees Celsius",
        "m³/s": "cubic meters per second"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

# -------------------------------
# Sentence splitting
# -------------------------------
def split_into_sentences(text):
    return [s.strip() for s in text.split('. ') if s]

# -------------------------------
# Summarization
# -------------------------------
def summarize_text(text, max_sentences=5):
    sentences = split_into_sentences(text)
    return ". ".join(sentences[:max_sentences])

# -------------------------------
# Text-to-speech (saved to temp file)
# -------------------------------
def text_to_speech_file(text):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts = gTTS(text=text, lang='en')
        tts.save(tmp.name)
        tmp_path = tmp.name
    return tmp_path

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("📄 PDF to Speech Reader")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Extracting text from PDF..."):
        raw_text = extract_text_from_pdf(uploaded_file)
    st.success("Text extracted!")

    clean_text = normalize_text(raw_text)

    # Slider to adjust summary length
    num_sentences = st.slider(
        "Select number of sentences for the summary:",
        min_value=1,
        max_value=20,
        value=5
    )

    summary = summarize_text(clean_text, max_sentences=num_sentences)

    st.subheader(f"Summary (first {num_sentences} sentences):")
    st.write(summary)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔊 Read Full PDF"):
            st.info("Generating audio for full PDF...")
            audio_file = text_to_speech_file(clean_text)
            st.audio(audio_file, format="audio/mp3")
            st.success("Done!")
            os.remove(audio_file)  # clean up temp file

    with col2:
        if st.button("🔊 Read Summary"):
            st.info("Generating audio for summary...")
            audio_file = text_to_speech_file(summary)
            st.audio(audio_file, format="audio/mp3")
            st.success("Done!")
            os.remove(audio_file)  # clean up temp file
