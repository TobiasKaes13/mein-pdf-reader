import streamlit as st
import google.generativeai as genai
import re

# 1. Seite & Design
st.set_page_config(page_title="PDF Reader Pro v3.0", page_icon="🎙️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
    </style>
    """, unsafe_allow_index=True)

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v3.0 - Professional Audio Fix"):
    st.markdown("""
    * 🎤 **Audio Engine 2.0:** Komplett neue Steuerung für Lautstärke und Geschwindigkeit.
    * 🛡️ **Halluzinations-Filter:** Verhindert das "Erfinden" von Texten durch strikte Extraktions-Prompts.
    * 🧹 **Deep Clean:** Filtert unsichtbaren PDF-Müll und Metadaten-Fragmente heraus.
    * 💎 **Pro Model Discovery:** Automatische Wahl des stärksten verfügbaren Modells.
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
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    prio = ["models/gemini-1.5-pro", "models/gemini-1.5-pro-latest", "models/gemini-1.5-flash"]
    for p in prio:
        if p in models: return genai.GenerativeModel(p)
    return genai.GenerativeModel(models[0]) if models else None

model = get_model()

# 4. Seitenleiste mit Live-Werten
st.sidebar.header("🎚️ Audio-Konsole")
vol = st.sidebar.slider("Lautstärke", 0.0, 1.0, 0.8, 0.1)
rate = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)

# 5. Upload & Verarbeitung
uploaded_file = st.file_uploader("PDF Dokument hochladen", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    c1, c2 = st.columns(2)
    with c1: btn_read = st.button("📖 Text 1:1 extrahieren")
    with c2: btn_sum = st.button("📝 Zusammenfassung erstellen")

    if btn_read or btn_sum:
        with st.spinner("KI verarbeitet Text..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                if btn_read:
                    prompt = "GIB NUR DEN REINEN TEXT DES DOKUMENTS WIEDER. Füge nichts hinzu, erfinde nichts. Ignoriere Seitenzahlen, Tabellen-Fragmente und technischen Code."
                else:
                    prompt = "Erstelle eine flüssige, lesbare Zusammenfassung des Inhalts auf Deutsch. Keine Aufzählungszeichen, nur Fließtext."
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                # Reinigung von Doppelsternen und Markdown
                cleaned = re.sub(r'[*#_]', '', response.text)
                st.session_state["text"] = cleaned
                st.session_state["fid"] = file_id
            except Exception as e:
                st.error(f"Fehler: {e}")

    if "text" in st.session_state and st.session_state["fid"] == file_id:
        text_to_show = st.session_state["text"]
        
        st.text_area("Vorschau des extrahierten Textes:", text_to_show, height=250)

        # 6. Fortschrittliches Vorlesen (JavaScript)
        st.divider()
        
        # Sätze splitten für sauberes Audio
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text_to_show) if len(s) > 5]
        
        col_play, col_stop = st.columns(2)
        
        with col_play:
            if st.button("▶️ Vorlesen starten / Aktualisieren"):
                js_code = f"""
                <script>
                (function() {{
                    window.speechSynthesis.cancel();
                    const sentences = {sentences};
                    let index = 0;

                    function speakNext() {{
                        if (index < sentences.length) {{
                            const msg = new SpeechSynthesisUtterance(sentences[index]);
                            msg.lang = 'de-DE';
                            msg.volume = {vol};
                            msg.rate = {rate};

                            const voices = window.speechSynthesis.getVoices();
                            // Suche nach Premium-Stimmen
                            const bestVoice = voices.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online')))
                                           || voices.find(v => v.lang.includes('de') && v.name.includes('Google'))
                                           || voices.find(v => v.lang.startsWith('de'));
                            
                            if (bestVoice) msg.voice = bestVoice;
                            
                            msg.onend = () => {{ index++; speakNext(); }};
                            window.speechSynthesis.speak(msg);
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

st.caption(f"Betriebsmodus: {model.model_name if model else 'Offline'}")
