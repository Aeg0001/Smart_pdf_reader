import streamlit as st
import fitz  # PyMuPDF
import re
from gtts import gTTS
import io
import base64

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
# Summarization
# -------------------------------
def summarize_text(text, max_sentences=5):
    # Improved splitting for better summary
    sentences = re.split(r'(?<=[.!?]) +', text)
    return " ".join(sentences[:max_sentences])

# -------------------------------
# Audio Helper (The Fix)
# -------------------------------
def play_audio(text):
    """Converts text to speech and plays it using Base64 to avoid path errors."""
    try:
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang='en')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # Convert to Base64
        b64 = base64.b64encode(mp3_fp.read()).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Audio Error: {e}")

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="PDF Audio Reader", page_icon="🔊")
st.title("📄 PDF to Speech Reader")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    # 1. Extraction
    if "raw_text" not in st.session_state:
        with st.spinner("Extracting text..."):
            st.session_state.raw_text = extract_text_from_pdf(uploaded_file)
    
    clean_text = normalize_text(st.session_state.raw_text)

    # 2. Summary Slider
    num_sentences = st.slider("Summary length (sentences):", 1, 50, 5)
    summary = summarize_text(clean_text, max_sentences=num_sentences)

    st.subheader("Summary Content:")
    st.info(summary)

    # 3. Audio Buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔊 Read Full PDF"):
            # Note: gTTS has a limit on text length per request. 
            # For very long PDFs, we read the first 3000 chars or chunk it.
            play_audio(clean_text[:3000]) 

    with col2:
        if st.button("🔊 Read Summary"):
            play_audio(summary)
