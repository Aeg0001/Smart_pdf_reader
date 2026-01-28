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
# Audio Helper (with chunking)
# -------------------------------
def play_audio_full(text, chunk_size=3000):
    """Converts full text to audio safely by splitting into chunks."""
    try:
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            mp3_fp = io.BytesIO()
            tts = gTTS(text=chunk, lang='en')
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            # Base64 to play in Streamlit
            b64 = base64.b64encode(mp3_fp.read()).decode()
            st.markdown(f"""
                <audio controls autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Audio Error: {e}")

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="PDF Audio Reader", page_icon="🔊")
st.title("📄 PDF to Speech Reader")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    # 1. Extract text
    with st.spinner("Extracting text from PDF..."):
        raw_text = extract_text_from_pdf(uploaded_file)
    st.success("Text extracted!")

    clean_text = normalize_text(raw_text)

    st.subheader("Preview:")
    st.write(clean_text[:1000] + "...")  # Show first 1000 chars as preview

    # 2. Read full PDF button
    if st.button("🔊 Read Full PDF"):
        st.info("Generating audio...")
        play_audio_full(clean_text)
        st.success("Done!")
