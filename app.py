import streamlit as st
import google.generativeai as genai
import re

# 1. Seite & Design
st.set_page_config(page_title="PDF Reader Pro v3.4", page_icon="🎙️", layout="wide")

st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 4em;
        background-color: #1E1E1E !important; 
        color: #FFFFFF !important;             
        font-size: 18px !important;
        font-weight: 800 !important;
        border: 2px solid #FF4B4B !important;  
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
    .stButton>button:hover {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    /* Disclaimer Styling */
    .disclaimer {
        padding: 15px;
        border-radius: 10px;
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
        margin-bottom: 20px;
        font-weight: bold;
        text-align: center;
    }
    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f0f2f6;
        color: #31333F;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
        border-top: 1px solid #e6e9ef;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v3.4 - Final Touch"):
    st.markdown("""
    * 📢 **User Guidance:** Disclaimer für Audio-Einstellungen hinzugefügt.
    * 🏷️ **Branding:** 'Coded by Tobias Kaes' integriert.
    * 🚫 **Skip TOC:** Inhaltsverzeichnisse werden weiterhin ignoriert.
    """)

st.title("🎙️ PDF Vorleser Pro")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt!")
    st.stop()

# 3. Modell-Suche
@st.cache_resource
def get_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        prio = ["models/gemini-1.5-pro", "models/gemini-1.5-pro-latest", "models/gemini-1.5-flash"]
        for p in prio:
            if p in models: return genai.GenerativeModel(p)
        return genai.GenerativeModel(models[0]) if models else None
    except: return None

model = get_model()

# 4. Seitenleiste
st.sidebar.header("🎚️ Audio-Einstellungen")
vol = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)
rate = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
st.sidebar.divider()
st.sidebar.markdown("👨‍💻 **Developer:** Tobias Kaes")

# 5. Upload & Verarbeitung
uploaded_file = st.file_uploader("PDF Dokument hochladen", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    st.markdown("### 1. Aktion wählen")
    c1, c2 = st.columns(2)
    with c1: btn_read = st.button("📖 PDF VOLLTEXT LESEN")
    with c2: btn_sum = st.button("📝 ZUSAMMENFASSUNG")

    if btn_read or btn_sum:
        with st.spinner("KI bereitet den Text vor..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                prompt = ("Lies den deutschen Haupttext ohne Inhaltsverzeichnis und Metadaten vor." if btn_read else "Fasse das Dokument flüssig zusammen.")
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                st.session_state["text"] = re.sub(r'[*#_\\-]', '', response.text)
                st.session_state["fid"] = file_id
            except Exception as e:
                st.error(f"Fehler: {e}")

    if "text" in st.session_state and st.session_state["fid"] == file_id:
        # 6. Disclaimer & Audio
        st.divider()
        st.markdown('<div class="disclaimer">⚠️ HINWEIS: Bitte stelle Lautstärke und Geschwindigkeit in der Seitenleiste ein, BEVOR du die Wiedergabe startest. Nachträgliche Änderungen starten das Vorlesen von vorne.</div>', unsafe_allow_html=True)
        
        st.markdown("### 2. Wiedergabe")
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', st.session_state["text"]) if len(s) > 3]
        
        col_play, col_stop = st.columns(2)
        with col_play:
            if st.button("▶️ JETZT VORLESEN"):
                js_code = f"""
                <script>
                (function() {{
                    window.speechSynthesis.cancel();
                    setTimeout(() => {{
                        const sentences = {sentences};
                        let i = 0;
                        function speakNext() {{
                            if (i < sentences.length) {{
                                const utter = new SpeechSynthesisUtterance(sentences[i]);
                                utter.lang = 'de-DE';
                                utter.volume = {vol};
                                utter.rate = {rate};
                                const v = window.speechSynthesis.getVoices();
                                utter.voice = v.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online'))) || v.find(v => v.lang.startsWith('de'));
                                utter.onend = () => {{ i++; speakNext(); }};
                                window.speechSynthesis.speak(utter);
                            }}
                        }}
                        speakNext();
                    }}, 300); 
                }})();
                </script>
                """
                st.components.v1.html(js_code, height=0)

        with col_stop:
            if st.button("⏹️ STOPP"):
                st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

# 7. Footer & Branding
st.markdown('<div class="footer">Coded by Tobias Kaes | Powered by Gemini 1.5 Pro</div>', unsafe_allow_html=True)
