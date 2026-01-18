import streamlit as st
import google.generativeai as genai

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader v1.5", page_icon="🎙️", layout="centered")

# --- PATCH NOTES ---
with st.expander("🚀 Was ist neu? (Patch Notes v1.5)"):
    st.markdown("""
    **Version 1.5**
    * ⚡ **Fast-Live Update:** Durch Satz-Segmentierung werden Änderungen an Lautstärke/Speed schneller übernommen.
    * 🛡️ **Quota-Schutz:** Ergebnisse werden im Session-State gecached (vermeidet Fehler 429).
    * 🎙️ **Smart-Mode:** Automatische Entscheidung zwischen Volltext und Zusammenfassung.
    """)

st.title("🎙️ Intelligenter PDF-Vorleser")

# 2. API Key Check
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key fehlt in den Streamlit Cloud Secrets!")
    st.stop()

# 3. Modell-Setup (Wir nutzen das stabilste Modell)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Modell-Fehler: {e}")
    st.stop()

# 4. Einstellungen in der Seitenleiste
st.sidebar.header("Audio-Einstellungen")
speech_speed = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
speech_volume = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)
st.sidebar.info("Änderungen werden nach dem aktuellen Satz übernommen.")

# 5. Datei-Upload & KI Verarbeitung
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file:
    # Eindeutige ID für das Dokument erstellen (Name + Größe)
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    # Prüfen, ob wir dieses Dokument schon im Speicher haben (vermeidet 429 Fehler)
    if "last_result" not in st.session_state or st.session_state.get("last_file_id") != file_id:
        with st.spinner("KI analysiert PDF... (Bitte warten)"):
            try:
                pdf_bytes = uploaded_file.getvalue()
                file_size_kb = len(pdf_bytes) / 1024
                
                if file_size_kb < 500:
                    mode = "Volltext"
                    prompt = "Gib den Text des Dokuments wortwörtlich auf Deutsch wieder. Keine Formatierung."
                else:
                    mode = "Zusammenfassung"
                    prompt = "Erstelle eine ausführliche Zusammenfassung auf Deutsch zum Vorlesen."

                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                
                # In Session speichern
                st.session_state["last_result"] = response.text
                st.session_state["last_file_id"] = file_id
                st.session_state["last_mode"] = mode
                
            except Exception as e:
                if "429" in str(e):
                    st.error("⏳ Limit erreicht! Google erlaubt nur 5 Anfragen/Min. Bitte warte 60 Sekunden.")
                else:
                    st.error(f"Fehler: {e}")
                st.stop()

    # Daten aus Session laden
    final_text = st.session_state["last_result"]
    st.info(f"Modus: **{st.session_state['last_mode']}**")
    
    with st.expander("Text anzeigen"):
        st.write(final_text)

    # 6. Vorlese-Funktion (Satz-für-Satz für Quasi-Live-Steuerung)
    st.divider()
    
    # Reinigung von Markdown-Zeichen
    clean_text = final_text.replace("**", "").replace("*", "").replace("#", "").replace("_", "")
    # Den Text in Sätze zerlegen (anhand von Punkten, Ausrufe- und Fragezeichen)
    import re
    sentences = re.split(r'(?<=[.!?]) +', clean_text)
    # Sätze für JavaScript vorbereiten (Liste daraus machen)
    safe_sentences = [s.replace("'", "").replace('"', '').replace("\n", " ").strip() for s in sentences if len(s) > 2]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔊 Vorlesen / Update"):
            # JavaScript, das die Sätze nacheinander abspielt
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
                    var bestVoice = voices.find(v => v.lang.startsWith('de') && 
                        (v.name.includes('Google') || v.name.includes('Online') || v.name.includes('Natural'))) 
                        || voices.find(v => v.lang.startsWith('de'));
                    
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

st.caption("v1.5 | Quota-Safe & Sentence-Sync")
