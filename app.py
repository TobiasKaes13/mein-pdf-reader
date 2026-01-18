import streamlit as st
import google.generativeai as genai

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader", page_icon="📄", layout="centered")

st.title("📄 Dein KI PDF-Vorleser")
st.markdown("Lade ein PDF hoch und die KI fasst es zusammen und liest es dir vor.")

# 2. API Key aus den Streamlit Secrets laden
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key nicht gefunden! Bitte trage den 'GEMINI_API_KEY' in den Streamlit Secrets ein.")
    st.stop()

# 3. Modell finden (Sicherheits-Check für die Region)
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
    model = genai.GenerativeModel(target_model)
except Exception as e:
    st.error(f"Fehler beim Laden des KI-Modells: {e}")
    st.stop()

# 4. Datei-Upload
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file:
    with st.spinner("KI liest das Dokument..."):
        try:
            # PDF Daten vorbereiten
            pdf_bytes = uploaded_file.getvalue()
            
            prompt = "Fasse dieses Dokument kurz und knackig auf Deutsch zusammen, ideal zum Vorlesen."
            
            # KI Antwort generieren
            response = model.generate_content([
                {"mime_type": "application/pdf", "data": pdf_bytes},
                prompt
            ])
            
            text_result = response.text
            
            # Ergebnis anzeigen
            st.success("Analyse fertig!")
            st.subheader("Zusammenfassung")
            st.write(text_result)

            # 5. Vorlese-Funktion (Verbesserte Variante 1)
            st.divider()
            st.subheader("Sprachausgabe")
            
            if st.button("🔊 Zusammenfassung laut vorlesen"):
                # Text für JavaScript sicher machen
                safe_text = text_result.replace("'", "").replace('"', '').replace("\n", " ")
                
                js_code = f"""
                <script>
                function speak() {{
                    window.speechSynthesis.cancel(); // Stoppt laufende Sprache
                    var msg = new SpeechSynthesisUtterance('{safe_text}');
                    msg.lang = 'de-DE';
                    
                    // Suche nach einer hochwertigen Stimme
                    var voices = window.speechSynthesis.getVoices();
                    var bestVoice = voices.find(v => v.lang.startsWith('de') && 
                        (v.name.includes('Google') || v.name.includes('Online') || v.name.includes('Natural'))) 
                        || voices.find(v => v.lang.startsWith('de'));

                    if (bestVoice) msg.voice = bestVoice;
                    window.speechSynthesis.speak(msg);
                }}
                
                // Stimmen laden im Hintergrund
                if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                    window.speechSynthesis.onvoiceschanged = speak;
                }}
                speak();
                </script>
                """
                st.components.v1.html(js_code, height=0)
            
            if st.button("⏹️ Ton stoppen"):
                st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

        except Exception as e:
            st.error(f"Fehler bei der Verarbeitung: {e}")

st.info("Hinweis: Diese App nutzt deinen zentral hinterlegten API-Key.")
