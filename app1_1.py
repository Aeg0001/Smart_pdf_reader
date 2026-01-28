import streamlit as st
import fitz  # PyMuPDF
import re
from gtts import gTTS
import io
import base64

# ----------------------------------
# PDF TEXT EXTRACTION
# ----------------------------------
def extract_text_from_pdf(pdf_file):
    # FIX: Use getvalue() to avoid the "0 characters" pointer issue
    pdf_bytes = pdf_file.getvalue()
    if not pdf_bytes:
        return ""
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# ----------------------------------
# TEXT NORMALIZATION
# ----------------------------------
def normalize_text(text):
    text = re.sub(r'\s+', ' ', text)
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

# ----------------------------------
# STABLE AUDIO GENERATION
# ----------------------------------
def generate_audio_player(text, label):
    """Generates a reliable audio player for a chunk of text."""
    try:
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang="en")
        tts.write_to_fp(mp3_fp)
        
        # Convert to Base64 for the HTML player
        b64 = base64.b64encode(mp3_fp.getvalue()).decode()
        md = f"""
            <div style="margin-bottom: 20px; padding: 10px; border: 1px solid #444; border-radius: 5px;">
                <p style="margin: 0 0 5px 0; font-weight: bold;">{label}</p>
                <audio controls style="width: 100%;">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
            </div>
            """
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Failed to generate {label}: {e}")

# ----------------------------------
# STREAMLIT UI
# ----------------------------------
st.set_page_config(page_title="PDF Audiobook", page_icon="🔊")
st.title("📄🔊 PDF Full Audiobook Reader")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    # Use session state to keep text loaded between clicks
    if "clean_text" not in st.session_state:
        with st.spinner("Extracting and cleaning text..."):
            raw = extract_text_from_pdf(uploaded_file)
            st.session_state.clean_text = normalize_text(raw)

    text = st.session_state.clean_text

    if not text:
        st.error("No text found in this PDF.")
    else:
        st.success(f"Loaded {len(text)} characters.")

        if st.button("🔊 Generate Full Audiobook"):
            # We split into 3000-character chunks (approx 5 mins of audio each)
            # This prevents gTTS timeouts and browser crashes.
            chunk_size = 3000
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            st.info(f"Generating {len(chunks)} audio parts...")
            
            for idx, chunk in enumerate(chunks):
                generate_audio_player(chunk, f"Part {idx + 1}")
            
            st.balloons()
