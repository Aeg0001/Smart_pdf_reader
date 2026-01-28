# -------------------------------
# Streamlit PDF Audiobook with Coqui TTS
# -------------------------------

import streamlit as st
import fitz  # PyMuPDF
import re
import io
import os
from TTS.api import TTS
import tempfile

# -------------------------------
# 1️⃣ PDF TEXT EXTRACTION
# -------------------------------
def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF"""
    try:
        pdf_bytes = pdf_file.getvalue()
        if not pdf_bytes:
            return ""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# -------------------------------
# 2️⃣ TEXT NORMALIZATION
# -------------------------------
def normalize_text(text):
    """Clean up PDF artifacts, replace symbols for speech"""
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)

    # Replace common symbols / acronyms
    replacements = {
        "HEC-RAS": "H E C R A S",
        "SWMM": "S W M M",
        "β": "beta",
        "α": "alpha",
        "μ": "mu",
        "°C": "degrees Celsius",
        "m³/s": "cubic meters per second",
        "km²": "square kilometers"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    return text.strip()

# -------------------------------
# 3️⃣ SMART FILTERS
# -------------------------------
def remove_references(text):
    """Remove references section"""
    ref_patterns = [
        r"\bReferences\b",
        r"\bBibliography\b",
        r"\bWorks Cited\b"
    ]
    for pattern in ref_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            text = text[:match.start()]
    return text

def remove_inline_citations(text):
    """Remove (Author, Year) and [Number] citations"""
    # (Author, 2023)
    text = re.sub(r"\([A-Za-z\s]+,?\s?\d{4}[a-z]?\)", "", text)
    # [1], [12], etc.
    text = re.sub(r"\[\d+\]", "", text)
    return text

def extract_main_text(text):
    text = remove_references(text)
    text = remove_inline_citations(text)
    return text

# -------------------------------
# 4️⃣ AUDIO GENERATION WITH COQUI TTS
# -------------------------------
# Load a pre-trained TTS model (English)
tts = TTS(model_name="tts_models/en/vctk/vits")

def generate_audio_player(text, label):
    """Generate audio from text and embed in Streamlit"""
    try:
        # Use temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tts.tts_to_file(text=text, file_path=tmp.name)
            st.audio(tmp.name, format="audio/wav")
            st.markdown(f"**{label}**")
    except Exception as e:
        st.error(f"Audio generation failed: {e}")

# -------------------------------
# 5️⃣ STREAMLIT UI
# -------------------------------
st.set_page_config(page_title="Coqui PDF Audiobook", page_icon="🎧")
st.title("📄 Coqui PDF Audiobook Reader")

uploaded_file = st.file_uploader("Upload a scientific or technical PDF", type=["pdf"])

if uploaded_file:
    if "processed_text" not in st.session_state:
        with st.spinner("Extracting and processing text..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            raw_text = normalize_text(raw_text)
            st.session_state.processed_text = extract_main_text(raw_text)
    
    full_text = st.session_state.processed_text

    if not full_text:
        st.error("PDF appears empty or unreadable")
    else:
        st.success(f"Loaded {len(full_text)} characters!")

        # Preview
        with st.expander("🔍 Preview Text"):
            st.write(full_text[:1500] + "...")
        
        # Generate audio
        if st.button("🔊 Generate Audiobook"):
            chunk_size = 2000  # characters per chunk
            chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
            st.info(f"Creating {len(chunks)} audio segments...")
            for idx, chunk in enumerate(chunks):
                generate_audio_player(chunk, f"Part {idx+1}")
            st.balloons()
