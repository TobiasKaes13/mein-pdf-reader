import streamlit as st
import google.generativeai as genai
import re

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader v2.0", page_icon="🎙️", layout="centered")

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v2.0 - Premium Edition"):
    st.markdown("""
    **Version 2.0**
    * 💎 **Premium-Support:** Optimiert für Nutzer mit bezahltem API-Plan (höhere Limits).
    * 🛠️ **Wahl-Modus:** Du entscheidest jetzt selbst: Volltext oder Zusammenfassung.
    * 🔊 **Dynamic Audio:** Lautstärke und Speed werden pro Satz aktualisiert.
    * 📄 **Long-PDF:** Unterstützung für deutlich längere Dokumente.
    """)

st.title("🎙️ Intelligenter PDF-Vorleser Pro")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt in den Secrets!")
    st.stop()

# 3. Modell-Setup
@st.cache_resource
def get_pro_model():
    # Da du zahlst, nutzen wir das leistungsstärkste 1.5 Pro oder Flash Modell
    return genai.GenerativeModel('gemini-1.5-pro') # Pro ist besser für lange PDFs

model = get_pro_model()

# 4. Einstellungen in der Seitenleiste
st.sidebar.header("Audio-Einstellungen")
speech_speed = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
speech_volume = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)
st.sidebar.info("Änderungen werden beim nächsten Satz aktiv.")

# 5. Datei-Upload
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    # Buttons zur Auswahl des Modus
    col_a, col_b = st.columns(2)
    with col_a:
        btn_full = st.button("📖 Ganze PDF lesen")
    with col_b:
        btn_sum = st.button("📝 Zusammenfassung")

    # Verarbeitung starten, wenn einer der Buttons gedrückt wurde
    if btn_full or btn_sum:
        st.session_state["mode"] = "Volltext" if btn_full else "Zusammenfassung"
        
        with st.spinner(f"KI erstellt {st.session_state['mode']}..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                if btn_full:
                    prompt = "Gib den kompletten Text des PDFs wortwörtlich auf Deutsch wieder. Ignoriere nur Seitenzahlen und Müll-Zeichen."
                else:
                    prompt = "Erstelle eine sehr ausführliche Zusammenfassung dieses PDFs auf Deutsch, ideal zum Vorlesen."
                
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                st.session_state["last_result"] = response.text
                st.session_state["last_file_id"] = file_id
            except Exception as e:
                st.error(f"Fehler: {e}")
                st.stop()

    # Wenn Text vorhanden ist, anzeigen und Vorlese-Optionen bieten
    if "last_result" in st.session_state and st.session_state.get("last_file_id") == file_id:
        final_text = st.session_state["last_result"]
        
        st.subheader(f"Inhalt ({st.session_state['mode']})")
        with st.expander("Text anzeigen"):
            st.write(final_text)

        # 6. Vorlese-Funktion
        st.divider()
        clean_text = final_text.replace("**", "").replace("*", "").replace("#", "").replace("_", "")
        # Zerlegen in Sätze für dynamische Updates
        sentences = re.split(r'(?<=[.!?]) +', clean_text)
        safe_sentences = [s.replace("'", "").replace('"', '').replace("\n", " ").strip() for s in sentences if len(s) > 2]

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Vorlesen starten"):
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
