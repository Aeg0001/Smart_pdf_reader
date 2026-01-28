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
    # Collapse all whitespace (PDFs are messy)
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
# LEVEL 1: REMOVE REFERENCES
# ----------------------------------
def remove_references(text):
    patterns = [
        r'\breferences\b',
        r'\bbibliography\b',
        r'\bworks cited\b',
        r'\breference list\b',
        r'\bliterature cited\b',
        r'\breferences and notes\b'
    ]

    lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            return text[:match.start()]

    return text

# ----------------------------------
# LEVEL 2: REMOVE IN-TEXT CITATIONS
# ----------------------------------
def remove_inline_citations(text):
    # APA / Harvard style citations
    text = re.sub(
        r'\([^()]*\b\d{4}\b[^()]*\)',
        '',
        text
    )

    # IEEE style citations
    text = re.sub(
        r'\[\s*\d+(\s*[-–]\s*\d+)?\s*\]',
        '',
        text
    )

    return text

# ----------------------------------
# LEVEL 3: MAIN SECTIONS ONLY
# ----------------------------------
def extract_main_sections(text):
    headers = [
        "abstract",
        "introduction",
        "method",
        "methodology",
        "materials and methods",
        "results",
        "discussion",
        "conclusion",
        "conclusions"
    ]

    text_lower = text.lower()
    indices = [text_lower.find(h) for h in headers if text_lower.find(h) != -1]

    if not indices:
        return text

    start = min(indices)

    end_match = re.search(r'\breferences\b', text_lower)
    end = end_match.start() if end_match else len(text)

    return text[start:end]

# ----------------------------------
# AUDIO PLAYER
# ----------------------------------
def generate_audio_player(text, label):
    try:
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang="en", tld="com.au")
        tts.write_to_fp(mp3_fp)

        b64 = base64.b64encode(mp3_fp.getvalue()).decode()

        html = f"""
        <div style="margin-bottom:20px; padding:15px; background:#262730;
                    border-radius:10px; border-left:5px solid #FF4B4B;">
            <p style="color:white; font-weight:bold;">{label}</p>
            <audio controls style="width:100%;">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Audio generation failed: {e}")

# ----------------------------------
# STREAMLIT UI
# ----------------------------------
st.set_page_config(page_title="Aussie PDF Audiobook", page_icon="🇦🇺")
st.title("📄🇦🇺 PDF Audiobook Reader")
st.markdown("### Accent: *Australian Female*")

filter_level = st.radio(
    "🧠 Smart filtering level:",
    [
        "Level 1 – Skip references",
        "Level 2 – Skip references + citations",
        "Level 3 – Main sections only"
    ]
)

uploaded_file = st.file_uploader(
    "Upload a scientific or technical PDF",
    type=["pdf"]
)

# Track filter changes
if "last_filter_level" not in st.session_state:
    st.session_state.last_filter_level = None

if uploaded_file:
    if (
        "processed_text" not in st.session_state
        or st.session_state.last_filter_level != filter_level
    ):
        with st.spinner("Extracting and processing text..."):
            text = extract_text_from_pdf(uploaded_file)
            text = normalize_text(text)

            if filter_level == "Level 1 – Skip references":
                text = remove_references(text)

            elif filter_level == "Level 2 – Skip references + citations":
                text = remove_inline_citations(text)
                text = remove_references(text)

            elif filter_level == "Level 3 – Main sections only":
                text = extract_main_sections(text)
                text = remove_inline_citations(text)

            st.session_state.processed_text = text
            st.session_state.last_filter_level = filter_level

    full_text = st.session_state.processed_text

    st.success(f"Loaded {len(full_text)} characters")

    with st.expander("🔍 Preview cleaned text"):
        st.write(full_text[:1500] + "...")

    if st.button("🔊 Generate Full Audiobook"):
        chunk_size = 3000
        chunks = [
            full_text[i:i + chunk_size]
            for i in range(0, len(full_text), chunk_size)
        ]

        st.info(f"Generating {len(chunks)} audio segments")

        for i, chunk in enumerate(chunks):
            generate_audio_player(chunk, f"Part {i + 1}")

