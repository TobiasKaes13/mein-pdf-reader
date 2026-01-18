import streamlit as st
import google.generativeai as genai
import re

# 1. Seite & Design fixen
st.set_page_config(page_title="PDF Reader Pro v3.1", page_icon="🎙️", layout="wide")

# Korrektur des HTML-Arguments (unsafe_allow_html statt unsafe_allow_index)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v3.1 - Bugfix & Audio"):
    st.markdown("""
    * 🐛 **Bugfix:** TypeError bei Seiten-Design behoben.
    * 🔊 **Audio-Sync:** Lautstärke- und Geschwindigkeits-Parameter korrigiert.
    * 💎 **Pro Model:** Nutzt deine Abo-Power für saubere Text-Extraktion.
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
    except:
        return None

model = get_model()

# 4. Seitenleiste
st.sidebar.header("🎚️ Audio-Einstellungen")
vol = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)
rate = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)

# 5. Upload & Verarbeitung
uploaded_file = st.file_uploader("PDF Dokument hochladen", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    c1, c2 = st.columns(2)
    with c1: btn_read = st.button("📖 Ganze PDF lesen")
    with c2: btn_sum = st.button("📝 Zusammenfassung")

    if btn_read or btn_sum:
        with st.spinner("KI verarbeitet Text..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                if btn_read:
                    prompt = "Extrahiere den Text wortwörtlich. Entferne NUR Seitenzahlen und unleserlichen Daten-Müll. Antworte nur mit dem Text."
                else:
                    prompt = "Erstelle eine flüssige Zusammenfassung auf Deutsch ohne Aufzählungszeichen."
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                # Reinigung
                cleaned = response.text.replace("*", "").replace("#", "").replace("_", "")
                st.session_state["text"] = cleaned
                st.session_state["fid"] = file_id
            except Exception as e:
                st.error(f"Fehler: {e}")

    if "text" in st.session_state and st.session_state["fid"] == file_id:
        text_ready = st.session_state["text"]
        
        with st.expander("Vorschau des Textes"):
            st.write(text_ready)

        # 6. Audio Steuerung
        st.divider()
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text_ready) if len(s) > 3]
        
        col_play, col_stop = st.columns(2)
        with col_play:
            if st.button("▶️ Vorlesen starten"):
                # JavaScript mit korrekten Variablen-Übergaben
                js_code = f"""
                <script>
                (function() {{
                    window.speechSynthesis.cancel();
                    const sentences = {sentences};
                    let i = 0;
                    function speakNext() {{
                        if (i < sentences.length) {{
                            const utter = new SpeechSynthesisUtterance(sentences[i]);
                            utter.lang = 'de-DE';
                            utter.volume = {vol};
                            utter.rate = {rate};
                            
                            const v = window.speechSynthesis.getVoices();
                            utter.voice = v.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online'))) 
                                          || v.find(v => v.lang.includes('de') && v.name.includes('Google'))
                                          || v.find(v => v.lang.startsWith('de'));
                            
                            utter.onend = () => {{ i++; speakNext(); }};
                            window.speechSynthesis.speak(utter);
                        }}
                    }}
                    speakNext();
                }})();
                </script>
                """
                st.components.v1.html(js_code, height=0)

        with col_stop:
            if st.button("⏹️ Stopp"):
                st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

st.caption(f"v3.1 Pro | Modell: {model.model_name if model else 'Suche...'}")
