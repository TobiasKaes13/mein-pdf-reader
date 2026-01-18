import streamlit as st
import google.generativeai as genai
import re

# 1. Seite & Design (Kontrast-Fix für Buttons)
st.set_page_config(page_title="PDF Reader Pro v3.2", page_icon="🎙️", layout="wide")

st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #262730 !important; /* Dunkler Hintergrund */
        color: white !important;             /* Weiße Schrift */
        font-weight: bold;
        border: 1px solid #4B4B4B;
    }
    .stButton>button:hover {
        background-color: #4B4B4B !important;
        border: 1px solid #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v3.2 - Design & Voice Fix"):
    st.markdown("""
    * 🎨 **Button-Kontrast:** Buttons sind jetzt dunkel mit weißer Schrift (bessere Lesbarkeit).
    * 🗣️ **Voice-Engine Pro:** Verbesserte Suche nach Microsoft Online & Google Stimmen.
    * 🧹 **No-Trash Filter:** Aggressivere Reinigung von PDF-Artefakten.
    """)

st.title("🎙️ PDF Vorleser Pro")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Bitte hinterlege deinen GEMINI_API_KEY in den Streamlit Secrets.")
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
    
    # Auswahl-Buttons
    st.markdown("### 1. Modus wählen")
    c1, c2 = st.columns(2)
    with c1: btn_read = st.button("📖 Ganze PDF lesen")
    with c2: btn_sum = st.button("📝 Zusammenfassung")

    if btn_read or btn_sum:
        with st.spinner("KI verarbeitet Text..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                prompt = ("Gib NUR den reinen deutschen Text wieder. Keine Kommentare, kein Müll." 
                          if btn_read else "Fasse das Dokument flüssig auf Deutsch zusammen.")
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                # Harte Reinigung von Sonderzeichen
                cleaned = re.sub(r'[*#_\\-]', '', response.text)
                st.session_state["text"] = cleaned
                st.session_state["fid"] = file_id
            except Exception as e:
                st.error(f"Fehler: {e}")

    if "text" in st.session_state and st.session_state["fid"] == file_id:
        text_ready = st.session_state["text"]
        
        with st.expander("Extrahierten Text prüfen"):
            st.write(text_ready)

        # 6. Audio Steuerung
        st.markdown("### 2. Sprachausgabe")
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text_ready) if len(s) > 3]
        
        col_play, col_stop = st.columns(2)
        with col_play:
            if st.button("▶️ JETZT VORLESEN"):
                js_code = f"""
                <script>
                (function() {{
                    window.speechSynthesis.cancel();
                    
                    // Kleine Verzögerung damit Stimmen geladen werden können
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
                                // Priorisierung der besten Stimmen
                                const bestVoice = voices.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online'))) 
                                              || voices.find(v => v.lang.includes('de') && v.name.includes('Google'))
                                              || voices.find(v => v.lang.startsWith('de'));
                                
                                if (bestVoice) utter.voice = bestVoice;
                                utter.onend = () => {{ i++; speakNext(); }};
                                synth.speak(utter);
                            }}
                        }}
                        speakNext();
                    }}, 200); 
                }})();
                </script>
                """
                st.components.v1.html(js_code, height=0)

        with col_stop:
            if st.button("⏹️ STOPP"):
                st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

st.caption(f"v3.2 Pro | Modell aktiv: {model.model_name if model else 'Suche...'}")
