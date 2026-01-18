import streamlit as st
import google.generativeai as genai
import re

# 1. Seite & Design
st.set_page_config(page_title="PDF Reader Pro v3.5", page_icon="🎙️", layout="wide")

# Styling für schönere, kompakte Buttons und das Layout
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

# 2. Disclaimer Pop-up (erscheint nur beim ersten Laden)
@st.dialog("⚠️ Wichtiger Hinweis")
def show_disclaimer():
    st.write("""
        Bitte stelle **Lautstärke** und **Geschwindigkeit** in der Seitenleiste ein, 
        **bevor** du die Wiedergabe startest. 
        
        Nachträgliche Änderungen während des Lesens führen dazu, dass die Datei 
        beim nächsten Klick wieder von vorne begonnen wird.
    """)
    if st.button("Verstanden & Schließen"):
        st.rerun()

if "disclaimer_shown" not in st.session_state:
    st.session_state.disclaimer_shown = True
    show_disclaimer()

# --- PATCH NOTES ---
with st.expander("🚀 Patch Notes v3.5"):
    st.markdown("""
    * 🔔 **Disclaimer Pop-up:** Erscheint einmalig beim Start der Seite.
    * 💅 **Button Design:** Kompakter, eleganter und besser aufeinander abgestimmt.
    * 👨‍💻 **Credit:** 'Coded by Tobias Kaes' hinzugefügt.
    """)

st.title("🎙️ PDF Vorleser Pro")

# 3. API & Modell (wie gehabt)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key fehlt!")
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

# 4. Sidebar
st.sidebar.header("🎚️ Audio-Konsole")
vol = st.sidebar.slider("Lautstärke", 0.0, 1.0, 1.0, 0.1)
rate = st.sidebar.slider("Geschwindigkeit", 0.5, 2.0, 1.0, 0.1)
st.sidebar.divider()
st.sidebar.caption("Coded by Tobias Kaes")

# 5. Upload & Logik
uploaded_file = st.file_uploader("PDF Dokument hochladen", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    # Kompakteres Button-Layout
    st.markdown("### 🛠️ Modus wählen")
    c1, c2 = st.columns(2)
    with c1: btn_read = st.button("📖 Volltext (Ohne Verzeichnis)")
    with c2: btn_sum = st.button("📝 Zusammenfassung")

    if btn_read or btn_sum:
        with st.spinner("KI verarbeitet..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                prompt = ("Extrahiere den Text ohne Inhaltsverzeichnis." if btn_read else "Fasse flüssig zusammen.")
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                st.session_state["text"] = re.sub(r'[*#_\\-]', '', response.text)
                st.session_state["fid"] = file_id
            except Exception as e:
                st.error(f"Fehler: {e}")

    if "text" in st.session_state and st.session_state["fid"] == file_id:
        st.divider()
        st.markdown("### 🔊 Wiedergabe")
        
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', st.session_state["text"]) if len(s) > 3]
        
        cp, cs = st.columns(2)
        with cp:
            if st.button("▶️ START"):
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

st.caption("Coded by Tobias Kaes")
