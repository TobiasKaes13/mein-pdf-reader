import streamlit as st
import google.generativeai as genai
import re

# 1. Seite & Design
st.set_page_config(page_title="PDF Reader Pro v3.7", page_icon="🎙️", layout="wide")

# CSS für kompakte Buttons und sauberes Layout
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
    }
    .stButton>button:hover {
        border-color: #FF4B4B;
        color: #FF4B4B !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Disclaimer Pop-up
@st.dialog("⚠️ Wichtiger Hinweis")
def show_disclaimer():
    st.write("""
        ### Vor der Wiedergabe beachten:
        Bitte stelle **Lautstärke** und **Geschwindigkeit** in der Seitenleiste ein, 
        **bevor** du die Wiedergabe startest. 
        
        Nachträgliche Änderungen während des Lesens führen dazu, dass die Datei 
        wieder von vorne begonnen wird.
    """)
    if st.button("Verstanden & Schließen"):
        st.rerun()

if "disclaimer_shown" not in st.session_state:
    st.session_state.disclaimer_shown = True
    show_disclaimer()

# --- PATCHNOTES ---
with st.expander("📜 Projekt-Historie (v1.0 - v3.7)"):
    st.markdown("""
    **v3.7 (Aktuell)**
    * 🔧 **Fix:** Text-Expander (Ausklappen) wiederhergestellt.
    * 🎤 **Voice-Boost:** Verbesserte Erkennung von Premium-Stimmen (Natural/Online).
    * 📝 **Clean-Up:** Optimierte Textreinigung für flüssigeres Vorlesen.
    """)

st.title("🎙️ PDF Vorleser Pro")

# 3. API & Modell
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
st.sidebar.markdown(f"<div style='text-align: center; padding-top: 10px; font-weight: bold;'>Coded by Tobias Kaes</div>", unsafe_allow_html=True)

# 5. Upload & Logik
uploaded_file = st.file_uploader("PDF Dokument hochladen", type=["pdf"])

if uploaded_file and model:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    st.markdown("### 🛠️ Modus wählen")
    c1, c2 = st.columns(2)
    with c1: btn_read = st.button("📖 Volltext (Skip Inhaltsverzeichnis)")
    with c2: btn_sum = st.button("📝 Zusammenfassung")

    if btn_read or btn_sum:
        with st.spinner("KI verarbeitet..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                prompt = ("Extrahiere nur den flüssigen Haupttext ohne Inhaltsverzeichnis." if btn_read else "Fasse den Inhalt flüssig zusammen.")
                response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
                # Reinigung von Markdown
                st.session_state["text"] = re.sub(r'[*#_\\-]', '', response.text)
                st.session_state["fid"] = file_id
                st.session_state["mode"] = "Volltext" if btn_read else "Zusammenfassung"
            except Exception as e:
                st.error(f"Fehler: {e}")

    # TEXT WIEDER AUSKLAPPBAR MACHEN
    if "text" in st.session_state and st.session_state["fid"] == file_id:
        st.divider()
        with st.expander(f"📄 {st.session_state['mode']} anzeigen / ausklappen"):
            st.write(st.session_state["text"])
        
        st.markdown("### 🔊 Wiedergabe")
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
                        const synth = window.speechSynthesis;

                        function speak() {{
                            if (i < sents.length) {{
                                const u = new SpeechSynthesisUtterance(sents[i]);
                                u.lang = 'de-DE'; u.volume = {vol}; u.rate = {rate};
                                
                                // Aggressive Suche nach Natural-Stimmen
                                let vs = synth.getVoices();
                                let bestVoice = vs.find(v => v.lang.includes('de') && (v.name.includes('Natural') || v.name.includes('Online')))
                                                || vs.find(v => v.lang.includes('de') && v.name.includes('Google'))
                                                || vs.find(v => v.lang.startsWith('de'));
                                
                                if (bestVoice) u.voice = bestVoice;
                                u.onend = () => {{ i++; speak(); }};
                                synth.speak(u);
                            }}
                        }}
                        speak();
                    }}, 400); // Etwas mehr Zeit für die Stimmen-Liste
                }})();
                </script>
                """
                st.components.v1.html(js, height=0)
        with cs:
            if st.button("⏹️ STOPP"):
                st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

st.caption("v3.7 Pro | Coded by Tobias Kaes")
