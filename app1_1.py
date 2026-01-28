import streamlit as st
import fitz  # PyMuPDF
from gtts import gTTS
import tempfile
import os
import re

# -------------------------------
def extract_text_from_pdf(pdf_file):
    pdf_bytes = pdf_file.read()  # read the uploaded file into memory
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

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

def split_into_sentences(text):
    return [s.strip() for s in text.split('. ') if s]

def summarize_text(text, max_sentences=5):
    sentences = split_into_sentences(text)
    return ". ".join(sentences[:max_sentences])

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp_file.name)
    return tmp_file.name

# -------------------------------
st.title("PDF to Speech Reader")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Extracting text from PDF..."):
        raw_text = extract_text_from_pdf(uploaded_file)

    st.success("Text extracted!")

    clean_text = normalize_text(raw_text)

    num_sentences = st.slider(
        "Select number of sentences for the summary:",
        min_value=1,
        max_value=20,
        value=5
    )

    st.subheader(f"Summary (first {num_sentences} sentences):")
    summary = summarize_text(clean_text, max_sentences=num_sentences)
    st.write(summary)

    if st.button("Read PDF Aloud"):
        st.info("Generating audio...")
        audio_file = text_to_speech(clean_text)
        audio_bytes = open(audio_file, "rb").read()
        st.audio(audio_bytes, format="audio/mp3")
        st.success("Done!")
        os.remove(audio_file)
