import streamlit as st
import google.generativeai as genai

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader v1.3", page_icon="🎙️", layout="centered")

# --- PATCH NOTES ---
with st.expander("🚀 Was ist neu? (Patch Notes v1.3)"):
    st.markdown("""
    **Version 1.3**
    * 🔊 **Lautstärkeregelung:** Du kannst die Lautstärke jetzt in der Seitenleiste anpassen.
    * 🏎️ **Geschwindigkeitsregler:** (v1.2) Kontrolle über das Lesetempo.
    * ✨ **Intelligenter Modus:** (v1.2) Automatische Wahl zwischen Direktlesen und Zusammenfassung.
    """)

st.title("🎙️ Intelligenter PDF-Vorleser")

# 2. API Key aus den Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt in den Secrets!")
    st.stop()

# 3. Modell-Setup
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
    model = genai.GenerativeModel(target_model)
except Exception as e:
    st.error(f"Modell-Fehler: {e}")
    st.stop()

# 4. Einstellungen in der Seitenleiste
st.sidebar.header("Audio-Einstellungen")
speech_speed = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
speech_volume = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1) # NEU: 0.0 bis 1.0

# 5. Datei-Upload
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file:
    with st.spinner("Analysiere Dokument..."):
        try:
            pdf_bytes = uploaded_file.getvalue()
            file_size_kb = len(pdf_bytes) / 1024
            
            if file_size_kb < 500:
                mode = "Direktes Vorlesen"
                prompt = "Gib den gesamten Text des Dokuments wortwörtlich auf Deutsch wieder. Keine Einleitung, keine Zusammenfassung."
            else:
                mode = "Zusammenfassung"
                prompt = "Dieses Dokument ist sehr lang. Erstelle eine ausführliche Zusammenfassung auf Deutsch, die sich gut zum Vorlesen eignet."

            st.info(f"Modus: **{mode}**")

            response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
            final_text = response.text
            
            st.subheader("Textinhalt")
            st.write(final_text)

            # 6. Vorlese-Funktion
            st.divider()
            
            clean_text = final_text.replace("**", "").replace("*", "").replace("#", "").replace("_", "")
            safe_text = clean_text.replace("'", "").replace('"', '').replace("\n", " ").replace("\r", "")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔊 Vorlesen starten"):
                    js_code = f"""
                    <script>
                    function speak() {{
                        window.speechSynthesis.cancel();
                        var msg = new SpeechSynthesisUtterance('{safe_text}');
                        msg.lang = 'de-DE';
                        msg.rate = {speech_speed}; 
                        msg.volume = {speech_volume}; // NEU: Lautstärke wird hier gesetzt

                        var voices = window.speechSynthesis.getVoices();
                        var bestVoice = voices.find(v => v.lang.startsWith('de') && 
                            (v.name.includes('Google') || v.name.includes('Online') || v.name.includes('Natural'))) 
                            || voices.find(v => v.lang.startsWith('de'));
                        
                        if (bestVoice) msg.voice = bestVoice;
                        window.speechSynthesis.speak(msg);
                    }}
                    if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                        window.speechSynthesis.onvoiceschanged = speak;
                    }}
                    speak();
                    </script>
                    """
                    st.components.v1.html(js_code, height=0)
            
            with col2:
                if st.button("⏹️ Stopp"):
                    st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

        except Exception as e:
            st.error(f"Fehler: {e}")

st.caption("v1.3 | Erstellt mit Gemini & Streamlit")
