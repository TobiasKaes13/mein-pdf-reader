import streamlit as st
import google.generativeai as genai
import os

# 1. Konfiguration
st.set_page_config(page_title="Free PDF Reader AI", layout="centered")
st.title("📄 PDF Vorlese-Assistent")

# API Key aus den Umgebungsvariablen laden (Sicherheit!)
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 2. Upload-Bereich
    uploaded_file = st.file_uploader("Lade ein PDF hoch", type=["pdf"])

    if uploaded_file:
        with st.spinner("Analysiere PDF..."):
            # PDF an Gemini senden
            # Wir nutzen hier die Fähigkeit von Gemini, Dateien direkt zu verarbeiten
            pdf_data = uploaded_file.read()
            contents = [
                {"mime_type": "application/pdf", "data": pdf_data},
                "Fasse dieses Dokument in 3-5 Sätzen zusammen und bereite den Text so vor, dass man ihn gut vorlesen kann."
            ]

            response = model.generate_content(contents)
            text_to_read = response.text

            st.subheader("Zusammenfassung:")
            st.write(text_to_read)

            # 3. Die Vorlese-Funktion (JavaScript Trick)
            st.subheader("Vorlesen")
            if st.button("Jetzt laut vorlesen"):
                js_code = f"""
                <script>
                var msg = new SpeechSynthesisUtterance({repr(text_to_read)});
                msg.lang = 'de-DE';
                window.speechSynthesis.speak(msg);
                </script>
                """
                st.components.v1.html(js_code, height=0)
else:
    st.warning("Bitte gib links deinen Gemini API Key ein, um zu starten.")