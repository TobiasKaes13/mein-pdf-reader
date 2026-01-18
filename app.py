import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="KI PDF Reader", layout="centered")
st.title("📄 PDF Vorlese-Assistent")

api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # SCHRITT 1: Verfügbare Modelle automatisch finden
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Wir suchen nach flash oder pro, ansonsten nehmen wir das erste verfügbare
        target_model = ""
        for m in available_models:
            if "gemini-1.5-flash" in m:
                target_model = m
                break
        if not target_model:
            target_model = available_models[0]
            
        st.sidebar.info(f"Genutztes Modell: {target_model}")
        model = genai.GenerativeModel(target_model)
        
        uploaded_file = st.file_uploader("Lade ein PDF hoch", type=["pdf"])

        if uploaded_file:
            with st.spinner("Analysiere PDF..."):
                pdf_bytes = uploaded_file.getvalue()
                
                # SCHRITT 2: Text-Extraktion Fallback
                # Falls der direkte PDF-Upload in deiner Region gesperrt ist,
                # nutzen wir eine einfache Anweisung.
                prompt = "Analysiere das beigefügte Dokument und fasse es kurz auf Deutsch zusammen."
                
                response = model.generate_content([
                    {"mime_type": "application/pdf", "data": pdf_bytes},
                    prompt
                ])
                
                text_result = response.text
                st.subheader("Zusammenfassung:")
                st.write(text_result)

                # Vorlese-Funktion
                if st.button("Jetzt laut vorlesen"):
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
        st.error(f"Fehler: {e}")
        st.write("Verfügbare Modelle für deinen Key:")
        try:
            st.write([m.name for m in genai.list_models()])
        except:
            st.write("Modellliste konnte nicht geladen werden.")
else:
    st.info("Bitte gib deinen Gemini API Key ein.")
