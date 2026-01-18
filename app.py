import streamlit as st
import google.generativeai as genai
import re
import time

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader v1.7", page_icon="🎙️", layout="centered")

# --- KOMPLETTE PATCH NOTES ---
with st.expander("🚀 Patch Notes & Historie (v1.7)"):
    st.markdown("""
    **Aktuell: Version 1.7**
    * 🔄 **Modell-Wechsel:** Nutzt jetzt primär `gemini-1.5-flash`, um das strenge 20-Anfragen-Limit von v2.5 zu umgehen.
    * ⏳ **Limit-Anzeige:** Verbesserte Fehlermeldungen bei Quota-Überschreitung.
    * 🎤 **Stimmen-Upgrade:** Optimierte Suche nach Microsoft & Google Premium-Stimmen.
    * 🧠 **Müll-Filter:** Unterdrückt Binärzahlen und technische Fragmente im PDF.
    """)

st.title("🎙️ Intelligenter PDF-Vorleser")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt in den Streamlit Cloud Secrets!")
    st.stop()

# 3. Stabiles Modell-Setup
@st.cache_resource
def get_stable_model():
    try:
        # Wir versuchen gezielt 1.5-flash zu finden, da das Tageslimit dort viel höher ist
        models = [m.name for m in genai.list_models()]
        if 'models/gemini-1.5-flash' in models:
            return genai.GenerativeModel('gemini-1.5-flash')
        elif 'models/gemini-1.5-pro' in models:
            return genai.GenerativeModel('gemini-1.5-pro')
        return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Modell-Suche fehlgeschlagen: {e}")
        return None

model = get_stable_model()

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
                
                # Prompt-Logik für sauberen Text
                if file_size_kb < 300:
                    prompt = "Lies den Text des PDFs aus. Gib NUR den lesbaren Haupttext auf Deutsch wieder. Ignoriere Binärzahlen, Seitenzahlen-Header und unleserliche Zeichen."
                    mode = "Direktes Vorlesen"
                else:
                    prompt = "Fasse dieses Dokument ausführlich auf Deutsch zusammen. Ignoriere dabei technische Tabellen oder Daten-Müll."
                    mode = "Zusammenfassung"
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                
                st.session_state["last_result"] = response.text
                st.session_state["last_file_id"] = file_id
                st.session_state["last_mode"] = mode
            except Exception as e:
                if "429" in str(e):
                    st.error("🛑 Tageslimit erreicht! Google erlaubt nur wenige Anfragen pro Tag für dieses Modell. Bitte versuche es in einer Stunde oder morgen wieder.")
                else:
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
                var synth = window.speechSynthesis;
                
                sentences.forEach((text) => {{
                    var msg = new SpeechSynthesisUtterance(text);
                    msg.lang = 'de-DE';
                    msg.rate = {speech_speed};
                    msg.volume = {speech_volume};
                    
                    var voices = synth.getVoices();
                    var bestVoice = voices.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online')))
                                   || voices.find(v => v.lang.includes('de') && v.name.includes('Google'))
                                   || voices.find(v => v.lang.includes('de'));
                    
                    if (bestVoice) msg.voice = bestVoice;
                    synth.speak(msg);
                }});
            }}
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

st.caption("v1.7 | Stable Model Policy")
