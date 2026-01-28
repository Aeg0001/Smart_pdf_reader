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
# Convert text to multiple audio files (chunking)
# -------------------------------
def text_to_audio_chunks(text, chunk_size=500):
    """
    Splits text into chunks (chunk_size in words)
    and generates gTTS MP3 for each chunk.
    Returns list of temp file paths.
    """
    words = text.split()
    audio_files = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts = gTTS(text=chunk, lang='en')
        tts.save(tmp_file.name)
        audio_files.append(tmp_file.name)

    return audio_files

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("📄 PDF to Speech Reader")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

# Keep track of temp audio files so we can avoid deleting too early
if "audio_files" not in st.session_state:
    st.session_state.audio_files = []

if uploaded_file is not None:
    with st.spinner("Extracting text from PDF..."):
        raw_text = extract_text_from_pdf(uploaded_file)
    st.success("Text extracted!")

    clean_text = normalize_text(raw_text)

    # Slider to adjust summary length
    num_sentences = st.slider(
        "Select number of sentences for the summary:",
        min_value=1,
        max_value=50,
        value=5
    )

    summary = summarize_text(clean_text, max_sentences=num_sentences)

    st.subheader(f"Summary ({num_sentences} sentences):")
    st.write(summary)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔊 Read Full PDF"):
            st.info("Generating audio for full PDF...")
            audio_files = text_to_audio_chunks(clean_text, chunk_size=500)
            st.session_state.audio_files.extend(audio_files)
            for idx, f in enumerate(audio_files):
                st.audio(f, format="audio/mp3")
            st.success("Done!")

    with col2:
        if st.button("🔊 Read Summary"):
            st.info("Generating audio for summary...")
            audio_files = text_to_audio_chunks(summary, chunk_size=100)
            st.session_state.audio_files.extend(audio_files)
            for idx, f in enumerate(audio_files):
                st.audio(f, format="audio/mp3")
            st.success("Done!")

# -------------------------------
# Optional: clean up temp files when app stops
# -------------------------------
def cleanup_temp_files():
    for f in st.session_state.get("audio_files", []):
        if os.path.exists(f):
            os.remove(f)
    st.session_state.audio_files = []

# Uncomment this if you want to add a cleanup button
if st.button("🗑️ Cleanup Temp Files"):
     cleanup_temp_files()
     st.success("Temp files deleted.")

