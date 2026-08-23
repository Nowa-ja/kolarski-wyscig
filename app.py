import base64
import io
import html
import streamlit as st
from gtts import gTTS

# ============================================================
# KONFIGURACJA APLIKACJI
# ============================================================

st.set_page_config(
    page_title="Peloton Live",
    page_icon="🚴",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# STYL UI (Zachowany Twój styl + poprawki dla kategorii)
# ============================================================

st.markdown(
    """
    <style>
        .stApp {
            background: radial-gradient(circle at 50% -10%, rgba(255, 107, 53, 0.18), transparent 35% ), #090b0f;
            color: #f5f7fa;
        }
        .block-container { max-width: 760px; padding-top: 2rem; padding-bottom: 3rem; }
        .hero { text-align: center; padding: 1rem 0 1.5rem 0; }
        .hero-icon { font-size: 4rem; line-height: 1; margin-bottom: 0.7rem; }
        .hero h1 { font-size: clamp(2rem, 8vw, 3.5rem); font-weight: 800; letter-spacing: -0.04em; margin: 0; color: #ffffff; }
        .hero p { color: #9da5b4; font-size: 1rem; margin-top: 0.7rem; }
        .card { background: rgba(22, 25, 32, 0.92); border: 1px solid #292e38; border-radius: 20px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 10px 35px rgba(0, 0, 0, 0.25); }
        .section-title { font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #8f98a8; margin-bottom: 0.8rem; }
        .route-card { background: linear-gradient(135deg, rgba(255, 107, 53, 0.15), rgba(22, 25, 32, 0.95)); border: 1px solid rgba(255, 107, 53, 0.35); border-radius: 20px; padding: 1.2rem; margin: 1rem 0; }
        .route-name { font-size: 1.35rem; font-weight: 800; color: #ffffff; }
        .route-meta { color: #aab1bd; margin-top: 0.35rem; font-size: 0.9rem; }
        .commentary { background: #101319; border-left: 4px solid #ff6b35; border-radius: 12px; padding: 1rem 1.1rem; line-height: 1.7; color: #e8ebef; max-height: 360px; overflow-y: auto; }
        .status { text-align: center; padding: 0.7rem; border-radius: 12px; background: rgba(255, 107, 53, 0.08); color: #ff9a76; margin: 1rem 0; }
        .footer { text-align: center; color: #626a78; font-size: 0.78rem; margin-top: 2rem; }
        div.stButton > button { width: 100%; border-radius: 14px; min-height: 3.2rem; font-weight: 800; font-size: 1rem; }
        @media (max-width: 600px) {
            .block-container { padding: 1rem 0.8rem 2rem 0.8rem; }
            .card { border-radius: 16px; padding: 1rem; }
            .hero { padding-top: 0.5rem; }
            .hero-icon { font-size: 3rem; }
            .commentary { font-size: 0.95rem; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# NOWA STRUKTURA BAZY WYŚCIGÓW (Z podziałem na Twoje kategorie!)
# ============================================================

if "dynamic_races" not in st.session_state:
    st.session_state.dynamic_races = {
        "🏙️ Wyścigi Wojewódzkie": {
            "🚴 Wielka Pętla Małopolski": {
                "available": True, "description": "Etap lokalny • Darmowy", "distance": "42 km", "terrain": "Szosa • Lekkie pagórki",
                "is_custom": False, "kolarze": [], "relacja_live": [], "password": ""
            },
            "🔒 Śląski Klasyk Miejski": {
                "available": False, "description": "Premium • Wymaga kodu", "distance": "55 km", "terrain": "Kostka • Szybkie kryterium",
                "is_custom": False, "kolarze": [], "relacja_live": [], "password": "SLASK"
            }
        },
        "🏔️ Wyścigi Górskie (Krew i Łzy)": {
            "🔒 Sekretny Tunel Miejski": {
                "available": False, "description": "Premium • Wyciskacz potu", "distance": "12 km", "terrain": "Tunel • Ściana płaczu (15%)",
                "is_custom": False, "kolarze": [], "relacja_live": [], "password": "TUNEL"
            },
            "🔒 Tatrzański Piekielny Podjazd": {
                "available": False, "description": "Premium • Hardkorowy trening", "distance": "28 km", "terrain": "Mordercze góry",
                "is_custom": False, "kolarze": [], "relacja_live": [], "password": "TATRY"
            }
        },
        "🦅 Wyścigi Ogólnopolskie / Zagraniczne": {
            "🔒 Wielki Wyścig Narodowy": {
                "available": False, "description": "Premium • Królewski etap", "distance": "180 km", "terrain": "Pełny przekrój",
                "is_custom": False, "kolarze": [], "relacja_live": [], "password": "POLSKA"
            }
        }
    }

if "started" not in st.session_state:
    st.session_state.started = False
if "commentary" not in st.session_state:
    st.session_state.commentary = ""
if "audio" not in st.session_state:
    st.session_state.audio = None
if "custom_audio" not in st.session_state:
    st.session_state.custom_audio = None
# ============================================================
# KOMENTARZ WYŚCIGU (Twój oryginalny szablon)
# ============================================================

COMMENTARY_TEMPLATE = """
Witamy na trasie wyścigu!

Pogoda jest upiorna, wieje silny wiatr, a przed nami wymagający etap!

Na czele peletonu ucieka mocna grupa:
Tadeusz Pogaczar, Remco Even oraz debiutant,
na którego patrzą dzisiaj wszyscy – {USER_NAME}!

Niesamowite!

{USER_NAME} decyduje się na atak na podjeździe!

Przyspiesza! Jeszcze jeden mocny obrót korbą!
Peleton zaczyna tracić kontakt!

Tadeusz Pogaczar próbuje odpowiedzieć,
ale {USER_NAME} jest dzisiaj w fenomenalnej formie!

Co za akcja!

Remco Even również rusza w pogoń,
a za nimi Jonas Vinger i Primus Roglicz próbują
zorganizować kontratak.

Ale {USER_NAME} nie zwalnia!

Szczyt podjazdu jest już blisko!

Jeszcze pięćdziesiąt metrów...
czterdzieści...
trzydzieści...

I jest!

{USER_NAME} przejeżdża przez szczyt jako pierwszy!

Teraz zjazd!

Wiatr wieje prosto w twarz,
ale tempo jest niewiarygodne.

Cała grupa jedzie na granicy możliwości!

Czy debiutant utrzyma przewagę?

Ostatni kilometr!

Publiczność krzyczy!

{USER_NAME} wychodzi na ostatnią prostą!

To będzie finisz!

Trzydzieści metrów!
Dwadzieścia!
Dziesięć!

I JEST!!!

{USER_NAME} wygrywa ten etap!

Co za debiut!

Co za emocje!

Cała Polska wstrzymała oddech!
"""

# ============================================================
# FUNKCJE
# ============================================================

def generate_commentary(user_name: str) -> str:
    return COMMENTARY_TEMPLATE.replace("{USER_NAME}", user_name)

@st.cache_data(show_spinner=False)
def generate_audio(text: str) -> bytes:
    audio_buffer = io.BytesIO()
    tts = gTTS(text=text, lang="pl", slow=False)
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()

def audio_player(audio_bytes: bytes):
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    player = f"""
        <audio controls preload="metadata" style="width: 100%; margin-top: 10px; border-radius: 12px;">
            <source src="data:audio/mpeg;base64,{audio_base64}" type="audio/mpeg">
            Twoja przeglądarka nie obsługuje elementu audio.
        </audio>
    """
    st.markdown(player, unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-icon">🚴</div>
        <h1>PELOTON LIVE</h1>
        <p>Wyciśnij z siebie pot, krew i łzy.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# NOWY PANEL WYBORU (KATEGORIA -> ETAP)
# ============================================================

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Wybierz kategorię i etap wyścigu</div>', unsafe_allow_html=True)

# 1. Wybór kategorii wyścigu
selected_category = st.selectbox(
    "Kategoria",
    options=list(st.session_state.dynamic_races.keys()),
)

# 2. Wybór etapu z wybranej kategorii
races_in_cat = st.session_state.dynamic_races[selected_category]
selected_race = st.selectbox(
    "Etap",
    options=list(races_in_cat.keys()),
)

race_info = races_in_cat[selected_race]

# TUTAJ BYŁ BŁĄD - Nawiasy zostały teraz poprawnie zamknięte:
st.markdown(
    f"""
    <div class="route-card">
        <div class="route-name">{html.escape(selected_race)}</div>
        <div class="route-meta">
            {race_info["description"]}<br>
            Dystans: <b>{race_info["distance"]}</b> &nbsp;•&nbsp; Teren: <b>{race_info["terrain"]}</b>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# SYSTEM ODBLOKOWYWANIA HASŁEM (PAYWALL MVP)
if not race_info["available"]:
    st.markdown("<p style='color:#ff9a76; font-size:0.9rem;'>🔒 <b>Ten etap wymaga licencji Premium.</b><br>Wyślij 5 zł BLIK na numer telefonu organizatora, aby otrzymać kod dostępu.</p>", unsafe_allow_html=True)
    kod_wpisany = st.text_input("Wpisz kod dostępu, aby odblokować trasę:", type="password", placeholder="Wpisz kod tutaj...")
    
    if st.button("🔓 Sprawdź i odblokuj kod"):
        if kod_wpisany.strip() == race_info["password"]:
            race_info["available"] = True
            st.success("🎉 Kod poprawny! Trasa została trwale odblokowana w tej sesji!")
            st.rerun()
        else:
            st.error("Nieprawidłowy kod dostępu. Spróbuj ponownie lub skontaktuj się z organizatorem.")

st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# LOGIKA URUCHAMIANIA TRANSMISJI (Tylko dla odblokowanych)
# ============================================================
if race_info["available"]:

    # PERSONALIZACJA
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Twój zawodnik</div>', unsafe_allow_html=True)

    user_name = st.text_input(
        "Imię i nazwisko",
        value="Anonimowy Kolarz",
        max_chars=60,
        placeholder="np. Jan Kowalski",
        label_visibility="collapsed",
    )
    st.caption("Komentator będzie używał tego imienia podczas relacji.")
    st.markdown("</div>", unsafe_allow_html=True)

    # PRZYCISK START WYŚCIGU
    if st.button("🔥 START WYŚCIGU", type="primary", use_container_width=True):
        clean_name = user_name.strip()
        if not clean_name:
            clean_name = "Anonimowy Kolarz"

        with st.spinner("🎙️ Komentator przygotowuje relację..."):
            # Generowanie komentarza dostosowanego pod zawodnika
            personalized_text = generate_commentary(clean_name)
            try:
                audio = generate_audio(personalized_text)
                st.session_state.commentary = personalized_text
                st.session_state.audio = audio
                st.session_state.started = True
            except Exception as error:
                st.session_state.commentary = personalized_text
                st.session_state.audio = None
                st.session_state.started = True
                st.warning("Nie udało się wygenerować nagrania audio. Sprawdź połączenie z internetem.")

    # EKRAN AKTYWNEJ RELACJI LIVE
    if st.session_state.started and st.session_state.commentary:
        st.markdown('<div class="status">🔴 RELACJA LIVE • JEDZIEMY!</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎙️ Relacja komentatora</div>', unsafe_allow_html=True)
        
        safe_commentary = html.escape(st.session_state.commentary).replace("\n", "<br>")
        st.markdown(f'<div class="commentary">{safe_commentary}</div>', unsafe_allow_html=True)
        
        # Odtwarzacz HTML5 z przyciskami Play/Pause
        if st.session_state.audio:
            audio_player(st.session_state.audio)

        st.markdown("</div>", unsafe_allow_html=True)

        # Sekcja diagnostyczna MVP
        with st.expander("📜 Pokaż pełny tekst relacji"):
            st.write(st.session_state.commentary)

else:
    # Blokada przycisku startu, gdy użytkownik nie wpisał poprawnego hasła BLIK
    st.button("🔒 ETAP ZABLOKOWANY (WYMAGANA LICENCJA)", disabled=True, use_container_width=True)


# ============================================================
# INFORMACJE / INSTRUKCJA (Twoja sekcja końcowa)
# ============================================================

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="section-title">🎧 Jak korzystać?</div>
    <p style="color:#aab1bd; line-height:1.7;">
        1. Załóż słuchawki.<br>
        2. Wybierz kategorię wyścigów (np. Górskie) oraz konkretny etap.<br>
        3. Odblokuj trasę Premium kodem dostępu lub wybierz etap darmowy.<br>
        4. Wpisz swoje imię i naciśnij <b>START WYŚCIGU</b>.<br>
        5. Uruchom relację głosową i wyciśnij z siebie siódme poty!
    </p>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# STOPKA
# ============================================================

st.markdown(
    """
    <div class="footer">
        PELOTON LIVE • PREMIUM MVP<br>
        Fikcyjny wyścig sportowy • Projekt demonstracyjny komercyjny
    </div>
    """,
    unsafe_allow_html=True,
)
