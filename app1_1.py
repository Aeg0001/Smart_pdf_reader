import streamlit as st
import fitz  # PyMuPDF
import re
from gtts import gTTS
import tempfile
import io

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
# Convert text to audio (Bytes approach)
# -------------------------------
def text_to_audio_chunks(text, chunk_size=500):
    """
    Splits text into chunks and generates gTTS audio bytes.
    Returns a list of bytes-objects (MP3 data).
    """
    words = text.split()
    audio_chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        
        # We use a BytesIO buffer to store the audio in memory
        mp3_fp = io.BytesIO()
        tts = gTTS(text=chunk, lang='en')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio_chunks.append(mp3_fp.read())

    return audio_chunks

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="PDF Audio Reader", page_icon="🔊")
st.title("📄 PDF to Speech Reader")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    # 1. Extraction
    with st.spinner("Extracting text from PDF..."):
        raw_text = extract_text_from_pdf(uploaded_file)
    st.success("Text extracted!")

    clean_text = normalize_text(raw_text)

    # 2. Summarization Settings
    num_sentences = st.slider(
        "Select number of sentences for the summary:",
        min_value=1,
        max_value=50,
        value=5
    )

    summary = summarize_text(clean_text, max_sentences=num_sentences)

    st.subheader(f"Summary ({num_sentences} sentences):")
    st.info(summary)

    # 3. Audio Controls
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔊 Read Full PDF"):
            with st.spinner("Generating audio for full PDF..."):
                # Larger chunk size for full text
                audio_data_list = text_to_audio_chunks(clean_text, chunk_size=400)
                for audio_bytes in audio_data_list:
                    st.audio(audio_bytes, format="audio/mp3")
            st.success("Full audio ready!")

    with col2:
        if st.button("🔊 Read Summary"):
            with st.spinner("Generating audio for summary..."):
                # Smaller chunk size for summary
                audio_data_list = text_to_audio_chunks(summary, chunk_size=100)
                for audio_bytes in audio_data_list:
                    st.audio(audio_bytes, format="audio/mp3")
            st.success("Summary audio ready!")
