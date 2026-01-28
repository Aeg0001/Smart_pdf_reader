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
# Audio Helper (The Base64 Fix)
# -------------------------------
def play_audio(text, label):
    """Converts text to speech and plays it using Base64 to avoid path errors."""
    try:
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang='en')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        b64 = base64.b64encode(mp3_fp.read()).decode()
        md = f"""
            <p style='margin-bottom: 5px;'>{label}</p>
            <audio controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error generating audio: {e}")

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="PDF Full Reader", page_icon="📖")
st.title("📖 PDF Full Text Reader")
st.write("Upload a PDF to convert the entire document into audio segments.")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file is not None:
    # 1. Extraction (Cached in session state)
    if "full_text" not in st.session_state:
        with st.spinner("Reading document..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            st.session_state.full_text = normalize_text(raw_text)
    
    full_text = st.session_state.full_text
    
    st.success(f"Successfully loaded document ({len(full_text)} characters)")

    # 2. Reading Options
    if st.button("🔊 Generate Audio for Entire PDF"):
        # We chunk by character count (approx 2500 chars is safe for gTTS)
        chunk_size = 2500 
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        st.write(f"Created {len(chunks)} audio segments. Please play them in order:")
        
        with st.spinner("Processing audio chunks..."):
            for idx, chunk in enumerate(chunks):
                # We add a small label so the user knows which part they are on
                play_audio(chunk, label=f"Part {idx + 1}")
                
    # 3. Text Preview (Optional)
    with st.expander("Show Document Text"):
        st.write(full_text)
