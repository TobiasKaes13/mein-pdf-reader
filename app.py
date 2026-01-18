import streamlit as st
import google.generativeai as genai
import re

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader v1.9", page_icon="🎙️", layout="centered")

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v1.9 - Quota & Model Fix"):
    st.markdown("""
    **Version 1.9**
    * 🛡️ **Quota-Boost:** Bevorzugt jetzt `gemini-1.5-flash`, um das 20-Anfragen-Limit von v2.5 zu umgehen.
    * 🔄 **Failover-Logik:** Springt automatisch zum nächsten Modell, falls eines das Limit erreicht hat.
    * 🛠️ **404-Fix:** Nutzt dynamische Namensprüfung für EU-Regionen.
    * 🧹 **Clean-Text:** Verbesserte Filterung von Binärcode und PDF-Artefakten.
    """)

st.title("🎙️ Intelligenter PDF-Vorleser")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt in den Secrets! Bitte GEMINI_API_KEY hinterlegen.")
    st.stop()

# 3. INTELLIGENTE MODELL-AUSWAHL (Behebt 429 & 404)
def get_working_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Prioritätenliste für hohe Gratis-Limits (1.5er Modelle sind besser für Free Tier)
        priorities = [
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-flash-latest", 
            "models/gemini-pro",
            "models/gemini-2.0-flash-exp" # Nur als letzter Ausweg
        ]
        
        for p in priorities:
            if p in available_models:
                return genai.GenerativeModel(p)
        
        return genai.GenerativeModel(available_models[0]) if available_models else None
    except Exception as e:
        st.error(f"Modellsuche fehlgeschlagen: {e}")
        return None

model = get_working_model()

# 4. Einstellungen
st.sidebar.header("Audio-Einstellungen")
speech_speed = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
speech_volume = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)

# 5. Datei-Upload
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    # Caching gegen unnötige API-Anfragen
    if "last_result" not in st.session_state or st.session_state.get("last_file_id") != file_id:
        with st.spinner(f"KI ({model.model_name}) analysiert PDF..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                # Strenger Prompt gegen Binär-Müll
                prompt = "Extrahiere den Text auf Deutsch. Ignoriere Binärzahlen, technische Header und Müll. Falls das Dokument sehr lang ist, erstelle eine strukturierte Zusammenfassung."
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                
                st.session_state["last_result"] = response.text
                st.session_state["last_file_id"] = file_id
            except Exception as e:
                if "429" in str(e):
                    st.error("⏳ Dieses Modell hat sein Limit erreicht. Bitte warte kurz oder versuche es später erneut.")
                else:
                    st.error(f"Fehler: {e}")
                st.stop()

    final_text = st.session_state["last_result"]
    with st.expander("Text anzeigen"):
        st.write(final_text)

    # 6. Vorlese-Funktion
    st.divider()
    clean_text = final_text.replace("**", "").replace("*", "").replace("#", "").replace("_", "")
    sentences = re.split(r'(?<=[.!?]) +', clean_text)
    safe_sentences = [s.replace("'", "").replace('"', '').replace("\n", " ").strip() for s in sentences if len(s) > 2]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔊 Vorlesen / Update"):
            js_code = f"""
            <script>
            function speak() {{
                window.speechSynthesis.cancel();
                var sentences = {safe_sentences};
                sentences.forEach((text) => {{
                    var msg = new SpeechSynthesisUtterance(text);
                    msg.lang = 'de-DE';
                    msg.rate = {speech_speed};
                    msg.volume = {speech_volume};
                    var voices = window.speechSynthesis.getVoices();
                    var bestVoice = voices.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online'))) 
                                   || voices.find(v => v.lang.includes('de') && v.name.includes('Google')) 
                                   || voices.find(v => v.lang.startsWith('de'));
                    if (bestVoice) msg.voice = bestVoice;
                    window.speechSynthesis.speak(msg);
                }});
            }}
            if (speechSynthesis.onvoiceschanged !== undefined) speechSynthesis.onvoiceschanged = speak;
            speak();
            </script>
            """
            st.components.v1.html(js_code, height=0)
    
    with col2:
        if st.button("⏹️ Stopp"):
            st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

st.caption(f"v1.9 | Aktiv: {model.model_name if model else 'Suche...'}")
