import streamlit as st
import google.generativeai as genai
import re

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader v1.5.1", page_icon="🎙️", layout="centered")

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v1.5.1"):
    st.markdown("""
    * 🔧 **Fix:** Automatische Modellsuche behebt den '404 Not Found' Fehler.
    * ⚡ **Fast-Live Update:** Lautstärke/Speed werden pro Satz aktualisiert.
    * 🛡️ **Quota-Schutz:** Vermeidet Fehler 429 durch Caching.
    """)

st.title("🎙️ Intelligenter PDF-Vorleser")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt in den Streamlit Cloud Secrets!")
    st.stop()

# 3. Dynamisches Modell-Setup (DIESER TEIL BEHEBT DEN 404 FEHLER)
@st.cache_resource
def get_best_model():
    try:
        # Liste alle Modelle auf, die Content generieren können
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Suche bevorzugt nach Flash 1.5, sonst nimm das erste verfügbare
        flash_models = [m for m in models if "flash" in m]
        selected = flash_models[0] if flash_models else models[0]
        return genai.GenerativeModel(selected)
    except Exception as e:
        st.error(f"Konnte kein Modell finden: {e}")
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
        with st.spinner("KI analysiert PDF..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                # Entscheidung Logik (Größe)
                prompt = "Gib den Text wortwörtlich auf Deutsch wieder. Falls zu lang, fasse präzise zusammen."
                
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
                    var bestVoice = voices.find(v => v.lang.startsWith('de') && (v.name.includes('Google') || v.name.includes('Online'))) || voices.find(v => v.lang.startsWith('de'));
                    if (bestVoice) msg.voice = bestVoice;
                    window.speechSynthesis.speak(msg);
                }});
            }}
            speak();
            </script>
            """
            st.components.v1.html(js_code, height=0)
    
    with col2:
        if st.button("⏹️ Stopp"):
            st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

st.caption("v1.5.1 | Auto-Model-Discovery aktiv")
