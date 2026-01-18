import streamlit as st
import google.generativeai as genai
import re

# 1. Seite & Design (Kontrast-Fix & Layout)
st.set_page_config(page_title="PDF Reader Pro v3.3", page_icon="🎙️", layout="wide")

st.markdown("""
    <style>
    /* Buttons extrem gut lesbar machen */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 4em;
        background-color: #1E1E1E !important; /* Tiefschwarz */
        color: #FFFFFF !important;             /* Reinweiß */
        font-size: 18px !important;
        font-weight: 800 !important;
        border: 2px solid #FF4B4B !important;  /* Roter Rahmen für Kontrast */
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
    .stButton>button:hover {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v3.3 - Smart Skip"):
    st.markdown("""
    * 🚫 **Skip TOC:** Das Inhaltsverzeichnis wird jetzt automatisch erkannt und übersprungen.
    * 🎨 **High Contrast Buttons:** Schwarz-Rote Buttons für maximale Lesbarkeit.
    * 🗣️ **Premium Audio:** Beste verfügbare Systemstimmen werden automatisch gewählt.
    """)

st.title("🎙️PDF Reader & Summaries")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt! Bitte in den Streamlit Cloud Secrets hinterlegen.")
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

# 5. Upload & Verarbeitung
uploaded_file = st.file_uploader("PDF Dokument hochladen", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    st.markdown("### 1. Zusammenfassen oder Ganze PDF?")
    c1, c2 = st.columns(2)
    with c1: btn_read = st.button("📖 GANZE PDF LESEN")
    with c2: btn_sum = st.button("📝 ZUSAMMENFASSUNG")

    if btn_read or btn_sum:
        with st.spinner("KI filtert Inhaltsverzeichnis und bereitet Text vor..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                
                if btn_read:
                    # Der neue "Skip-TOC" Prompt
                    prompt = """Extrahiere den flüssigen Haupttext des Dokuments auf Deutsch. 
                    WICHTIG: Überspringe das Inhaltsverzeichnis, Kopfzeilen, Fußzeilen und Seitenzahlen komplett. 
                    Lies direkt beim ersten echten Textkapitel los. Gib KEINE Metadaten oder Listen von Kapiteln aus."""
                else:
                    prompt = "Fasse den Kerninhalt des Dokuments flüssig auf Deutsch zusammen. Ignoriere das Inhaltsverzeichnis."
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                
                # Säuberung von Markdown
                cleaned = re.sub(r'[*#_\\-]', '', response.text)
                st.session_state["text"] = cleaned
                st.session_state["fid"] = file_id
            except Exception as e:
                st.error(f"Fehler: {e}")

    if "text" in st.session_state and st.session_state["fid"] == file_id:
        text_ready = st.session_state["text"]
        
        with st.expander("Vorschau des gefilterten Textes"):
            st.write(text_ready)

        # 6. Audio Steuerung
        st.markdown("### 2. Wiedergabe")
        # Zerlegung in Sätze
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text_ready) if len(s) > 3]
        
        col_play, col_stop = st.columns(2)
        with col_play:
            if st.button("▶️ START / UPDATE"):
                js_code = f"""
                <script>
                (function() {{
                    window.speechSynthesis.cancel();
                    setTimeout(() => {{
                        const sentences = {sentences};
                        let i = 0;
                        const synth = window.speechSynthesis;

                        function speakNext() {{
                            if (i < sentences.length) {{
                                const utter = new SpeechSynthesisUtterance(sentences[i]);
                                utter.lang = 'de-DE';
                                utter.volume = {vol};
                                utter.rate = {rate};
                                
                                const voices = synth.getVoices();
                                const bestVoice = voices.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online'))) 
                                              || voices.find(v => v.lang.includes('de') && v.name.includes('Google'))
                                              || voices.find(v => v.lang.startsWith('de'));
                                
                                if (bestVoice) utter.voice = bestVoice;
                                utter.onend = () => {{ i++; speakNext(); }};
                                synth.speak(utter);
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

st.caption(f"v3.3 Pro | Aktiv: {model.model_name if model else 'Suche...'}")


