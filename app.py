import streamlit as st
import google.generativeai as genai

# 1. Seite konfigurieren
st.set_page_config(page_title="KI PDF Reader", page_icon="🎙️", layout="centered")

st.title("🎙️ Intelligenter PDF-Vorleser")
st.markdown("Liest kurze PDFs direkt vor und fasst lange Dokumente automatisch zusammen.")

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

# 4. Datei-Upload
uploaded_file = st.file_uploader("Wähle eine PDF-Datei aus", type=["pdf"])

if uploaded_file:
    with st.spinner("Analysiere Dokumentgröße..."):
        try:
            pdf_bytes = uploaded_file.getvalue()
            
            # Wir schicken eine kurze Vor-Anfrage, um die Länge zu prüfen
            # (Oder wir nutzen die Dateigröße als Indikator)
            file_size_kb = len(pdf_bytes) / 1024
            
            # Entscheidungshilfe: Alles unter 500KB behandeln wir als "kurz"
            # Das entspricht grob 10-15 Seiten Text.
            if file_size_kb < 500:
                mode = "Direktes Vorlesen"
                prompt = "Gib den gesamten Text des Dokuments wortwörtlich auf Deutsch wieder. Keine Einleitung, keine Zusammenfassung."
            else:
                mode = "Zusammenfassung"
                prompt = "Dieses Dokument ist sehr lang. Erstelle eine ausführliche Zusammenfassung auf Deutsch, die sich gut zum Vorlesen eignet."

            st.info(f"Modus: **{mode}** (Dateigröße: {file_size_kb:.1f} KB)")

            # KI Antwort generieren
            response = model.generate_content([
                {"mime_type": "application/pdf", "data": pdf_bytes},
                prompt
            ])
            
            final_text = response.text
            
            # Anzeige
            st.subheader(mode)
            st.write(final_text)

            # 5. Vorlese-Funktion
            st.divider()
            
            # Reinigung
            clean_text = final_text.replace("**", "").replace("*", "").replace("#", "").replace("_", "")
            safe_text = clean_text.replace("'", "").replace('"', '').replace("\n", " ").replace("\r", "")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔊 Start"):
                    js_code = f"""
                    <script>
                    function speak() {{
                        window.speechSynthesis.cancel();
                        var msg = new SpeechSynthesisUtterance('{safe_text}');
                        msg.lang = 'de-DE';
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

st.caption("System: Automatische Umschaltung zwischen Volltext und Zusammenfassung aktiv.")
