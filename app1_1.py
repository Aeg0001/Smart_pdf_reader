import streamlit as st
import fitz  # PyMuPDF
import re
from gtts import gTTS
import io

# -------------------------------
# 1️⃣ PDF Extraction
# -------------------------------
def extract_text_from_pdf(pdf_file):
    pdf_bytes = pdf_file.read()  # read uploaded file into memory
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

# -------------------------------
# 2️⃣ Text normalization
# -------------------------------
def normalize_text(text):
    text = re.sub(r'\s+', ' ', text)  # remove extra spaces/newlines
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
# 3️⃣ Sentence splitting
# -------------------------------
def split_into_sentences(text):
    return [s.strip() for s in text.split('. ') if s]

# -------------------------------
# 4️⃣ Summarization
# -------------------------------
def summarize_text(text, max_sentences=5):
    sentences = split_into_sentences(text)
    return ". ".join(sentences[:max_sentences])

# -------------------------------
# 5️⃣ Text-to-speech using gTTS + BytesIO
# -------------------------------
def text_to_speech_chunks(text):
    chunk_size = 2000  # max chars per gTTS call
    audio_bytes = io.BytesIO()

    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        tts = gTTS(text=chunk, lang='en')
        tts_fp = io.BytesIO()
        tts.write_to_fp(tts_fp)
        tts_fp.seek(0)
        audio_bytes.write(tts_fp.read())

    audio_bytes.seek(0)
    return audio_bytes

# -------------------------------
# 6️⃣ Streamlit UI
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

    # Show summary
    st.subheader(f"Summary (first {num_sentences} sentences):")
    summary = summarize_text(clean_text, max_sentences=num_sentences)
    st.write(summary)

    # Buttons to read full text or summary
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔊 Read Full PDF"):
            st.info("Generating audio for full PDF...")
            audio_bytes = text_to_speech_chunks(clean_text)
            st.audio(audio_bytes, format="audio/mp3")
            st.success("Done!")

    with col2:
        if st.button("🔊 Read Summary"):
            st.info("Generating audio for summary...")
            audio_bytes = text_to_speech_chunks(summary)
            st.audio(audio_bytes, format="audio/mp3")
            st.success("Done!")

