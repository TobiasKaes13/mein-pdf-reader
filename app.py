import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="PDF Reader", layout="centered")
st.title("📄 PDF Vorlese-Assistent")

# API Key Eingabe
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Wir nutzen 'gemini-1.5-flash', aber mit dem vollen Pfad
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        uploaded_file = st.file_uploader("Lade ein PDF hoch", type=["pdf"])

        if uploaded_file:
            with st.spinner("Analysiere PDF..."):
                # PDF Daten korrekt auslesen
                pdf_bytes = uploaded_file.getvalue()
                
                # Inhalt für die API vorbereiten
                prompt = "Fasse dieses Dokument kurz zusammen, damit ich es vorlesen kann. Antworte auf Deutsch."
                contents = [
                    {"mime_type": "application/pdf", "data": pdf_bytes},
                    prompt
                ]
                
                # Anfrage senden
                response = model.generate_content(contents)
                text_result = response.text
                
                st.subheader("Zusammenfassung:")
                st.write(text_result)

                # Vorlese-Funktion
                st.subheader("Vorlesen")
                if st.button("Jetzt laut vorlesen"):
                    # Text für JavaScript sicher machen (Anführungszeichen entfernen)
                    safe_text = text_result.replace("'", "").replace('"', '').replace("\n", " ")
                    js_code = f"""
                    <script>
                    var msg = new SpeechSynthesisUtterance('{safe_text}');
                    msg.lang = 'de-DE';
                    window.speechSynthesis.speak(msg);
                    </script>
                    """
                    st.components.v1.html(js_code, height=0)
                    
    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
else:
    st.info("Bitte gib deinen Gemini API Key in der Seitenleiste ein.")
