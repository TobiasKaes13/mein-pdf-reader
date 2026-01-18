import streamlit as st
import google.generativeai as genai

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader", page_icon="📄", layout="centered")

st.title("📄 Dein KI PDF-Vorleser")
st.markdown("Lade ein PDF hoch. Die KI fasst es zusammen und liest es ohne störende Zeichen vor.")

# 2. API Key aus den Streamlit Secrets laden
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ API Key nicht gefunden! Bitte trage den 'GEMINI_API_KEY' in den Streamlit Secrets ein.")
    st.stop()

# 3. Modell finden (Sicherheits-Check für die Region)
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # Suche nach flash, ansonsten nimm das erste verfügbare Modell
    target_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
    model = genai.GenerativeModel(target_model)
except Exception as e:
    st.error(f"Fehler beim Laden des KI-Modells: {e}")
    st.stop()

# 4. Datei-Upload
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file:
    with st.spinner("KI analysiert das Dokument..."):
        try:
            # PDF Daten auslesen
            pdf_bytes = uploaded_file.getvalue()
            
            # Anweisung an die KI
            prompt = "Fasse dieses Dokument kurz und prägnant auf Deutsch zusammen. Nutze keine komplizierten Formatierungen, da der Text vorgelesen werden soll."
            
            # KI Antwort generieren
            response = model.generate_content([
                {"mime_type": "application/pdf", "data": pdf_bytes},
                prompt
            ])
            
            text_result = response.text
            
            # Ergebnis anzeigen (mit Sternchen für die Optik)
            st.success("Analyse fertig!")
            st.subheader("Zusammenfassung")
            st.write(text_result)

            # 5. Vorlese-Funktion (REINIGUNG DER STERNCHEN)
            st.divider()
            st.subheader("Sprachausgabe")
            
            # Textreinigung für die Stimme: Entfernt **, *, # und _
            clean_text = text_result.replace("**", "").replace("*", "").replace("#", "").replace("_", "")
            # Text für JavaScript sicher machen (entfernt Zeilenumbrüche und einfache Anführungszeichen)
            safe_text = clean_text.replace("'", "").replace('"', '').replace("\n", " ").replace("\r", "")
            
            if st.button("🔊 Zusammenfassung laut vorlesen"):
                js_code = f"""
                <script>
                function speak() {{
                    window.speechSynthesis.cancel(); // Stoppt alles, was gerade läuft
                    var msg = new SpeechSynthesisUtterance('{safe_text}');
                    msg.lang = 'de-DE';
                    msg.rate = 1.0; 

                    var voices = window.speechSynthesis.getVoices();
                    // Suche nach einer hochwertigen Online-Stimme
                    var bestVoice = voices.find(v => v.lang.startsWith('de') && 
                        (v.name.includes('Google') || v.name.includes('Online') || v.name.includes('Natural'))) 
                        || voices.find(v => v.lang.startsWith('de'));

                    if (bestVoice) msg.voice = bestVoice;
                    window.speechSynthesis.speak(msg);
                }}
                
                // Stimmen-Fix für Chrome/Edge
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

