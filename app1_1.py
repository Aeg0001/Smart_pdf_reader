import streamlit as st
import fitz  # PyMuPDF
import re
from gtts import gTTS
import io

# -------------------------------
# PDF Extraction
# -------------------------------
def extract_text_from_pdf(pdf_file):
    # Use .getvalue() to ensure we get the data even on reruns
    pdf_bytes = pdf_file.getvalue()
    if not pdf_bytes:
        return ""
    
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
    # Simple cleanup of common PDF artifacts
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
    return text.strip()

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="PDF Audio Reader", page_icon="📖")
st.title("📖 PDF Full Text Reader")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file is not None:
    # Extract text every time the file changes
    with st.spinner("Extracting text from PDF..."):
        raw_text = extract_text_from_pdf(uploaded_file)
        clean_text = normalize_text(raw_text)

    if not clean_text:
        st.error("No text could be extracted. The PDF might be a scanned image (OCR required) or encrypted.")
    else:
        st.success(f"Successfully loaded document ({len(clean_text)} characters)")

        # 1. Preview the text to make sure it's actually there
        with st.expander("👀 Preview Extracted Text"):
            st.write(clean_text[:2000] + "..." if len(clean_text) > 2000 else clean_text)

        # 2. Reading logic
        st.subheader("🔊 Listen to Document")
        
        # We split the text into chunks because gTTS and browsers 
        # struggle with massive single audio files.
        chunk_size = 2000 
        chunks = [clean_text[i:i+chunk_size] for i in range(0, len(clean_text), chunk_size)]
        
        st.info(f"The document has been split into {len(chunks)} parts for smooth playback.")

        # Create a player for each chunk
        for idx, chunk in enumerate(chunks):
            with st.container():
                col1, col2 = st.columns([1, 4])
                col1.write(f"**Part {idx + 1}**")
                
                # Button to generate audio for this specific part
                # (This prevents the app from crashing by trying to load everything at once)
                if col2.button(f"Generate Audio for Part {idx + 1}", key=f"btn_{idx}"):
                    with st.spinner(f"Preparing Part {idx + 1}..."):
                        mp3_fp = io.BytesIO()
                        tts = gTTS(text=chunk, lang='en')
                        tts.write_to_fp(mp3_fp)
                        # Passing bytes directly to st.audio is the most stable method
                        st.audio(mp3_fp.getvalue(), format="audio/mp3")
