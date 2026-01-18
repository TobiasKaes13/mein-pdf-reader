import streamlit as st
import google.generativeai as genai
import re

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader Pro v2.1", page_icon="🎙️", layout="centered")

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v2.1 - Abo & Pro Support"):
    st.markdown("""
    **Version 2.1**
    * 💎 **Pro-Model Auto-Discovery:** Findet jetzt automatisch das beste verfügbare Modell (Pro oder Flash), ohne 404-Fehler.
    * 📖 **Long-Context:** Optimiert für sehr lange PDFs (ganze Bücher möglich).
    * 🔊 **Dynamic Audio:** Lautstärke und Speed werden beim Neustart sofort übernommen.
    * 🛠️ **Universal Fix:** Läuft stabil in allen Regionen (EU/Deutschland).
    """)

st.title("🎙️ Intelligenter PDF-Vorleser Pro")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt in den Secrets!")
    st.stop()

# 3. DYNAMISCHE MODELL-SUCHE (Verhindert 404)
@st.cache_resource
def get_best_available_model():
    try:
        # Wir fragen Google nach den verfügbaren Modellen für DEINEN Key
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Prioritätenliste (Wir suchen das stärkste Modell zuerst)
        # Wir probieren verschiedene Pfade für Pro und Flash
        priorities = [
            "models/gemini-1.5-pro-latest", 
            "models/gemini-1.5-pro", 
            "models/gemini-1.5-flash-latest", 
            "models/gemini-1.5-flash"
        ]
        
        for p in priorities:
            if p in available_models:
                return genai.GenerativeModel(p)
        
        # Fallback auf das erste verfügbare Modell
        return genai.GenerativeModel(available_models[0])
    except Exception as e:
        st.error(f"Modell-Suche fehlgeschlagen: {e}")
        return None

model = get_best_available_model()

# 4. Einstellungen in der Seitenleiste
st.sidebar.header("Audio-Einstellungen")
speech_speed = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
speech_volume = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)

# 5. Datei-Upload
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    col_a, col_b = st.columns(2)
    with col_a:
        btn_full = st.button("📖 Ganze PDF lesen")
    with col_b:
        btn_sum = st.button("📝 Zusammenfassung")

    if btn_full or btn_sum:
        st.session_state["mode"] = "Volltext" if btn_full else "Zusammenfassung"
        
        with st.spinner(f"KI ({model.model_name}) verarbeitet Dokument..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                if btn_full:
                    prompt = "Extrahiere den kompletten Text wortwörtlich auf Deutsch. Ignoriere nur Seitenzahlen und Müll."
                else:
                    prompt = "Fasse dieses Dokument ausführlich auf Deutsch zusammen."
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                st.session_state["last_result"] = response.text
                st.session_state["last_file_id"] = file_id
            except Exception as e:
                st.error(f"KI-Fehler: {e}")
                st.stop()

    if "last_result" in st.session_state and st.session_state.get("last_file_id") == file_id:
        final_text = st.session_state["last_result"]
        st.subheader(f"Inhalt ({st.session_state['mode']})")
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

st.caption(f"v2.1 Pro | Aktiv: {model.model_name if model else 'Suche...'}")
