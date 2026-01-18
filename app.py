import streamlit as st
import google.generativeai as genai
import re

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader v1.8", page_icon="🎙️", layout="centered")

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v1.8 - Universal Fix"):
    st.markdown("""
    **Version 1.8**
    * 🛠️ **Deep-Scan Model Discovery:** Findet Modelle jetzt über ihre internen Fähigkeiten statt über Namen. Löst den 404-Fehler endgültig.
    * 🔊 **Live-Control:** (v1.5) Geschwindigkeit und Lautstärke pro Satz steuerbar.
    * 🛡️ **Tageslimit-Schutz:** (v1.7) Bevorzugt Modelle mit hohen Gratis-Limits (1.5-Flash).
    * 🧹 **Müll-Filter:** (v1.6) Ignoriert Binär-Code und Metadaten im PDF.
    """)

st.title("🎙️ Intelligenter PDF-Vorleser")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt in den Secrets!")
    st.stop()

# 3. DIE ULTIMATIVE MODELL-SUCHE (Behebt 404 & 429)
@st.cache_resource
def find_working_model():
    try:
        # Wir listen alle verfügbaren Modelle auf
        available_models = genai.list_models()
        
        # Wir suchen Modelle, die Texte generieren können
        usable_models = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
        
        # Prioritäten-Liste: Was wir am liebsten hätten
        priorities = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest", "models/gemini-pro"]
        
        for p in priorities:
            if p in usable_models:
                return genai.GenerativeModel(p)
        
        # Falls nichts aus der Liste da ist, nimm das erste, was Text kann
        if usable_models:
            return genai.GenerativeModel(usable_models[0])
            
        return None
    except Exception as e:
        st.error(f"Konnte kein Modell finden: {e}")
        return None

model = find_working_model()

# 4. Einstellungen
st.sidebar.header("Audio-Einstellungen")
speech_speed = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
speech_volume = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)

# 5. Datei-Upload
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if "last_result" not in st.session_state or st.session_state.get("last_file_id") != file_id:
        with st.spinner("KI liest Dokument..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                # Prompt mit Müll-Filter
                prompt = "Extrahiere den deutschen Haupttext. Falls zu lang, fasse zusammen. Ignoriere Binärcode, Header und Wortwolken."
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                
                st.session_state["last_result"] = response.text
                st.session_state["last_file_id"] = file_id
            except Exception as e:
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
                                   || voices.find(v => v.lang.includes('de'));
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

st.caption(f"v1.8 | Aktiv: {model.model_name if model else 'Kein Modell'}")
