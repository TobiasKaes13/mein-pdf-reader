import streamlit as st
import google.generativeai as genai
import re

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader v1.6", page_icon="🎙️", layout="centered")

# --- KOMPLETTE PATCH NOTES ---
with st.expander("🚀 Patch Notes & Historie (v1.6)"):
    st.markdown("""
    **Aktuell: Version 1.6**
    * 🎤 **Premium Voice Fix:** Verbesserte Logik zur Auswahl natürlicher Stimmen im Browser.
    * 🧠 **Smart-Analysis:** Filtert jetzt Binär-Müll und störende Zahlen automatisch aus.
    * 📝 **Vollständige Historie:** Alle bisherigen Features in einer Übersicht.

    **Ältere Versionen:**
    * **v1.5.1:** Fix für '404 Model Not Found' durch automatische Modellsuche.
    * **v1.5:** Satz-für-Satz Vorlesen für schnellere Updates von Speed & Volume.
    * **v1.4:** Quota-Schutz (Caching) gegen den '429 Too Many Requests' Fehler.
    * **v1.3:** Einführung der Lautstärkeregelung.
    * **v1.2:** Einführung des Geschwindigkeitsreglers.
    """)

st.title("🎙️ Intelligenter PDF-Vorleser")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt in den Streamlit Cloud Secrets!")
    st.stop()

# 3. Dynamisches Modell-Setup
@st.cache_resource
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        flash_models = [m for m in models if "flash" in m]
        selected = flash_models[0] if flash_models else models[0]
        return genai.GenerativeModel(selected)
    except Exception as e:
        st.error(f"Modell-Suche fehlgeschlagen: {e}")
        return None

model = get_best_model()

# 4. Einstellungen in der Seitenleiste
st.sidebar.header("Audio-Einstellungen")
speech_speed = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
speech_volume = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)

# 5. Datei-Upload & Verarbeitung
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if "last_result" not in st.session_state or st.session_state.get("last_file_id") != file_id:
        with st.spinner("KI bereitet Text vor..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                file_size_kb = len(pdf_bytes) / 1024
                
                # Verschärfter Prompt gegen "Müll-Text" und für korrekte Zusammenfassung
                if file_size_kb < 300: # Grenze etwas gesenkt für mehr Sicherheit
                    prompt = "Lies den Text des PDFs aus. Gib NUR den relevanten, lesbaren Text auf Deutsch wieder. Ignoriere Binärzahlen, Wortwolken-Listen oder Metadaten-Müll."
                    mode = "Direktes Vorlesen"
                else:
                    prompt = "Dieses PDF ist groß. Erstelle eine sehr ausführliche, gut strukturierte Zusammenfassung auf Deutsch. Ignoriere technische Daten-Fragmente."
                    mode = "Zusammenfassung"
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                
                st.session_state["last_result"] = response.text
                st.session_state["last_file_id"] = file_id
                st.session_state["last_mode"] = mode
            except Exception as e:
                st.error(f"KI-Fehler: {e}")
                st.stop()

    final_text = st.session_state["last_result"]
    st.info(f"Modus: **{st.session_state.get('last_mode')}**")
    with st.expander("Textinhalt anzeigen"):
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
                
                // Wir erzwingen das Laden der Stimmen
                var synth = window.speechSynthesis;
                
                sentences.forEach((text) => {{
                    var msg = new SpeechSynthesisUtterance(text);
                    msg.lang = 'de-DE';
                    msg.rate = {speech_speed};
                    msg.volume = {speech_volume};
                    
                    var voices = synth.getVoices();
                    // Priorität: 1. Microsoft Online/Natural, 2. Google, 3. Erste deutsche Stimme
                    var bestVoice = voices.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online')))
                                   || voices.find(v => v.lang.includes('de') && v.name.includes('Google'))
                                   || voices.find(v => v.lang.includes('de'));
                    
                    if (bestVoice) msg.voice = bestVoice;
                    synth.speak(msg);
                }});
            }}
            // Fix für Browser, die Stimmen erst verzögert bereitstellen
            if (speechSynthesis.onvoiceschanged !== undefined) {{
                speechSynthesis.onvoiceschanged = speak;
            }}
            speak();
            </script>
            """
            st.components.v1.html(js_code, height=0)
    
    with col2:
        if st.button("⏹️ Stopp"):
            st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

st.caption("v1.6 | Optimized Logic & Premium Voices")
