import streamlit as st
import google.generativeai as genai
import re

# 1. Seite & Design
st.set_page_config(page_title="PDF Reader Pro v3.6", page_icon="🎙️", layout="wide")

# Styling für die Buttons und das Layout
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #262730 !important;
        color: white !important;
        font-weight: 600;
        border: 1px solid #4B4B4B;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #FF4B4B;
        color: #FF4B4B !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Disclaimer Pop-up (erscheint beim ersten Laden)
@st.dialog("⚠️ Wichtiger Hinweis")
def show_disclaimer():
    st.write("""
        ### Vor der Wiedergabe beachten:
        Bitte stelle **Lautstärke** und **Geschwindigkeit** in der Seitenleiste ein, 
        **bevor** du die Wiedergabe startest. 
        
        **Warum?** Nachträgliche Änderungen während des Lesens führen dazu, dass die App 
        die aktuelle Warteschlange löschen muss und beim nächsten Klick wieder von vorne beginnt.
    """)
    if st.button("Verstanden & Schließen"):
        st.rerun()

if "disclaimer_shown" not in st.session_state:
    st.session_state.disclaimer_shown = True
    show_disclaimer()

# --- GESAMTE PATCHNOTES HISTORIE ---
with st.expander("📜 Projekt-Historie & Patchnotes (v1.0 - v3.6)"):
    st.markdown("""
    **v3.6 (Aktuell)**
    * 🏷️ UI-Anpassung: Credits unter Audio-Konsole verschoben.
    * 📚 Historie: Alle Entwicklungsschritte dokumentiert.
    
    **v3.5**
    * 🔔 Disclaimer Pop-up integriert.
    * 💅 Button-Design modernisiert (kompakter).
    
    **v3.3 - v3.4**
    * 🚫 **Smart Skip:** Automatische Erkennung und Überspringen von Inhaltsverzeichnissen.
    * 💎 **Branding:** 'Coded by Tobias Kaes' hinzugefügt.
    
    **v3.0 - v3.2**
    * 🎤 **Audio Engine 2.0:** Wechsel auf satzweise Verarbeitung für stabilere Regler-Steuerung.
    * 🛡️ **Halluzinations-Schutz:** Strengere KI-Prompts gegen "erfundenen" Text.
    * 🧹 **Deep Clean:** Filterung von Binärcode und PDF-Artefakten.
    
    **v1.0 - v2.1**
    * 💎 **Premium-Support:** Umstellung auf Pay-as-you-go (Gemini 1.5 Pro).
    * 🛠️ **Universal Fix:** Dynamische Modell-Suche gegen 404-Fehler.
    * 🛡️ **Quota-Schutz:** Automatisches Failover zwischen Modellen.
    """)

st.title("🎙️ PDF Vorleser Pro")

# 3. API & Modell-Setup
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key fehlt in den Secrets!")
    st.stop()

@st.cache_resource
def get_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        prio = ["models/gemini-1.5-pro", "models/gemini-1.5-flash"]
        for p in prio:
            if p in models: return genai.GenerativeModel(p)
        return genai.GenerativeModel(models[0])
    except: return None

model = get_model()

# 4. Sidebar mit Credits an der gewünschten Stelle
st.sidebar.header("🎚️ Audio-Konsole")
vol = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)
rate = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
st.sidebar.markdown(f"<div style='text-align: center; padding-top: 10px; font-weight: bold;'>Coded by Tobias Kaes</div>", unsafe_allow_html=True)
st.sidebar.divider()
st.sidebar.info("Tipp: Nutze Microsoft Edge für die besten 'Natural' Stimmen.")

# 5. Upload & Logik
uploaded_file = st.file_uploader("PDF Dokument hochladen", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    st.markdown("### 🛠️ Modus wählen")
    c1, c2 = st.columns(2)
    with c1: btn_read = st.button("📖 Volltext (Skip Inhaltsverzeichnis)")
    with c2: btn_sum = st.button("📝 Zusammenfassung")

    if btn_read or btn_sum:
        with st.spinner("KI verarbeitet das Dokument..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                prompt = ("Extrahiere den flüssigen Haupttext. Überspringe Inhaltsverzeichnis und Metadaten." if btn_read else "Fasse den Inhalt flüssig auf Deutsch zusammen.")
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                st.session_state["text"] = re.sub(r'[*#_\\-]', '', response.text)
                st.session_state["fid"] = file_id
            except Exception as e:
                st.error(f"Fehler bei der KI-Verarbeitung: {e}")

    if "text" in st.session_state and st.session_state["fid"] == file_id:
        st.divider()
        st.markdown("### 🔊 Wiedergabe")
        
        # Text in Sätze zerlegen
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', st.session_state["text"]) if len(s) > 3]
        
        cp, cs = st.columns(2)
        with cp:
            if st.button("▶️ START / NEUSTART"):
                js = f"""
                <script>
                (function() {{
                    window.speechSynthesis.cancel();
                    setTimeout(() => {{
                        const sents = {sentences};
                        let i = 0;
                        function speak() {{
                            if (i < sents.length) {{
                                const u = new SpeechSynthesisUtterance(sents[i]);
                                u.lang = 'de-DE'; u.volume = {vol}; u.rate = {rate};
                                const vs = window.speechSynthesis.getVoices();
                                u.voice = vs.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online'))) || vs.find(v => v.lang.startsWith('de'));
                                u.onend = () => {{ i++; speak(); }};
                                window.speechSynthesis.speak(u);
                            }}
                        }}
                        speak();
                    }}, 300);
                }})();
                </script>
                """
                st.components.v1.html(js, height=0)
        with cs:
            if st.button("⏹️ STOPP"):
                st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

# 6. Kleiner Footer
st.caption("v3.6 Pro | Coded by Tobias Kaes")
