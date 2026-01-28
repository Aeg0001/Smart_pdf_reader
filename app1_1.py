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
    """Extracts text reliably using getvalue() to avoid stream errors."""
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
    """Cleans up PDF artifacts and prepares scientific notation for speech."""
    # Replace multiple whitespaces/newlines with a single space
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
# AUDIO PLAYER GENERATOR
# ----------------------------------
def generate_audio_player(text, label):
    """Generates an HTML audio player with an Australian accent."""
    try:
        mp3_fp = io.BytesIO()
        # lang="en" and tld="com.au" provides the Australian Female voice
        tts = gTTS(text=text, lang="en", tld="com.au")
        tts.write_to_fp(mp3_fp)
        
        # Encode to Base64 to bypass local file path issues
        b64 = base64.b64encode(mp3_fp.getvalue()).decode()
        
        # Modern CSS-styled audio player
        md = f"""
            <div style="margin-bottom: 25px; padding: 15px; background-color: #262730; border-radius: 10px; border-left: 5px solid #FF4B4B;">
                <p style="margin: 0 0 10px 0; color: white; font-weight: bold; font-family: sans-serif;">{label}</p>
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
st.set_page_config(page_title="Aussie PDF Audiobook", page_icon="🇦🇺")

st.title("📄🇦🇺 PDF Audiobook Reader")
st.markdown("### Accent: *Australian Female*")

uploaded_file = st.file_uploader("Upload a scientific or technical PDF", type=["pdf"])

if uploaded_file:
    # We store the text in session_state so it doesn't disappear on click
    if "processed_text" not in st.session_state:
        with st.spinner("Extracting and processing text..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            st.session_state.processed_text = normalize_text(raw_text)

    full_text = st.session_state.processed_text

    if not full_text:
        st.error("The PDF appears to be empty or unreadable.")
    else:
        st.success(f"Successfully loaded {len(full_text)} characters!")

        # Preview section
        with st.expander("🔍 Preview Text"):
            st.write(full_text[:1500] + "...")

        # Action Button
        if st.button("🔊 Generate Full Audiobook"):
            # Chunking logic: gTTS and Browsers struggle with massive files.
            # We split the text into 3000-character segments (approx 3-5 mins each).
            chunk_size = 3000
            chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
            
            st.info(f"Creating {len(chunks)} audio segments. You can listen as they generate:")
            
            for idx, chunk in enumerate(chunks):
                generate_audio_player(chunk, f"Part {idx + 1}")
            
            st.balloons()
