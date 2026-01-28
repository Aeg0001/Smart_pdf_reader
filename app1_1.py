import streamlit as st
import fitz  # PyMuPDF
import re
from gtts import gTTS
import io
import base64
import time

# ----------------------------------
# PDF TEXT EXTRACTION
# ----------------------------------
def extract_text_from_pdf(pdf_file):
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

# ----------------------------------
# TEXT NORMALIZATION
# ----------------------------------
def normalize_text(text):
    text = re.sub(r'\s+', ' ', text)
    replacements = {
        "HEC-RAS": "H E C R A S", "SWMM": "S W M M",
        "β": "beta", "α": "alpha", "μ": "mu",
        "°C": "degrees Celsius", "m³/s": "cubic meters per second"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.strip()

# ----------------------------------
# CACHED AUDIO GENERATION
# ----------------------------------
@st.cache_data(show_spinner=False)
def get_tts_b64(text_chunk):
    """
    This caches the result so if the app re-runs, 
    we don't ask Google for the same audio twice!
    """
    try:
        # Artificial delay to be polite to Google's servers
        time.sleep(1.5) 
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text_chunk, lang="en", tld="com.au")
        tts.write_to_fp(mp3_fp)
        return base64.b64encode(mp3_fp.getvalue()).decode()
    except Exception as e:
        return f"ERROR: {e}"

# ----------------------------------
# STREAMLIT UI
# ----------------------------------
st.set_page_config(page_title="Aussie PDF Reader", page_icon="🇦🇺")
st.title("📄🇦🇺 PDF Audiobook Reader")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file:
    if "processed_text" not in st.session_state:
        with st.spinner("Extracting text..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            st.session_state.processed_text = normalize_text(raw_text)

    full_text = st.session_state.processed_text
    
    if full_text:
        st.success(f"Loaded {len(full_text)} characters.")
        
        # Split into 2500-char chunks
        chunk_size = 2500
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        st.write(f"### 🎧 Audiobook Parts ({len(chunks)})")
        st.info("Click 'Generate' on a part to listen. Generating one-by-one prevents Google from blocking you.")

        for idx, chunk in enumerate(chunks):
            with st.container():
                col1, col2 = st.columns([1, 4])
                col1.write(f"**Part {idx+1}**")
                
                # We use a unique key for every button
                if col2.button(f"Generate & Play Part {idx+1}", key=f"btn_{idx}"):
                    with st.spinner("Talking to Google..."):
                        b64_result = get_tts_b64(chunk)
                        
                        if b64_result.startswith("ERROR"):
                            st.error("Google is temporarily busy. Wait 10 seconds and try again.")
                        else:
                            md = f"""
                                <audio controls autoplay style="width: 100%;">
                                    <source src="data:audio/mp3;base64,{b64_result}" type="audio/mp3">
                                </audio>
                                """
                            st.markdown(md, unsafe_allow_html=True)
