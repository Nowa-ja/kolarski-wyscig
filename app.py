```python
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
# STYL UI
# CSS jest responsywny i został przygotowany przede wszystkim
# z myślą o ekranach smartfonów.
# ============================================================

st.markdown(
    """
    <style>
        /* Główne tło */
        .stApp {
            background:
                radial-gradient(
                    circle at 50% -10%,
                    rgba(255, 107, 53, 0.18),
                    transparent 35%
                ),
                #090b0f;
            color: #f5f7fa;
        }

        /* Ograniczenie szerokości głównej zawartości */
        .block-container {
            max-width: 760px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* Nagłówek */
        .hero {
            text-align: center;
            padding: 1rem 0 1.5rem 0;
        }

        .hero-icon {
            font-size: 4rem;
            line-height: 1;
            margin-bottom: 0.7rem;
        }

        .hero h1 {
            font-size: clamp(2rem, 8vw, 3.5rem);
            font-weight: 800;
            letter-spacing: -0.04em;
            margin: 0;
            color: #ffffff;
        }

        .hero p {
            color: #9da5b4;
            font-size: 1rem;
            margin-top: 0.7rem;
        }

        /* Karty */
        .card {
            background: rgba(22, 25, 32, 0.92);
            border: 1px solid #292e38;
            border-radius: 20px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 35px rgba(0, 0, 0, 0.25);
        }

        .section-title {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #8f98a8;
            margin-bottom: 0.8rem;
        }

        /* Informacja o trasie */
        .route-card {
            background: linear-gradient(
                135deg,
                rgba(255, 107, 53, 0.15),
                rgba(22, 25, 32, 0.95)
            );
            border: 1px solid rgba(255, 107, 53, 0.35);
            border-radius: 20px;
            padding: 1.2rem;
            margin: 1rem 0;
        }

        .route-name {
            font-size: 1.35rem;
            font-weight: 800;
            color: #ffffff;
        }

        .route-meta {
            color: #aab1bd;
            margin-top: 0.35rem;
            font-size: 0.9rem;
        }

        /* Komentarz */
        .commentary {
            background: #101319;
            border-left: 4px solid #ff6b35;
            border-radius: 12px;
            padding: 1rem 1.1rem;
            line-height: 1.7;
            color: #e8ebef;
            max-height: 360px;
            overflow-y: auto;
        }

        /* Status */
        .status {
            text-align: center;
            padding: 0.7rem;
            border-radius: 12px;
            background: rgba(255, 107, 53, 0.08);
            color: #ff9a76;
            margin: 1rem 0;
        }

        /* Stopka */
        .footer {
            text-align: center;
            color: #626a78;
            font-size: 0.78rem;
            margin-top: 2rem;
        }

        /* Przyciski */
        div.stButton > button {
            width: 100%;
            border-radius: 14px;
            min-height: 3.2rem;
            font-weight: 800;
            font-size: 1rem;
        }

        /* Na telefonach */
        @media (max-width: 600px) {
            .block-container {
                padding: 1rem 0.8rem 2rem 0.8rem;
            }

            .card {
                border-radius: 16px;
                padding: 1rem;
            }

            .hero {
                padding-top: 0.5rem;
            }

            .hero-icon {
                font-size: 3rem;
            }

            .commentary {
                font-size: 0.95rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DANE WYŚCIGÓW
# ============================================================

RACES = {
    "🚴 Wielka Pętla Małopolski": {
        "available": True,
        "description": "Etap lokalny • Darmowy",
        "distance": "42 km",
        "terrain": "Góry + szosa",
    },
    "🔒 Wielki Wyścig Narodowy": {
        "available": False,
        "description": "Premium • Wkrótce",
        "distance": "—",
        "terrain": "—",
    },
    "🔒 Sekretny Tunel Miejski": {
        "available": False,
        "description": "Premium • Wkrótce",
        "distance": "—",
        "terrain": "—",
    },
}


# ============================================================
# KOMENTARZ WYŚCIGU
#
# {USER_NAME} jest dynamicznym placeholderem.
# Po kliknięciu START zostanie zastąpiony imieniem użytkownika.
#
# Tekst wykorzystuje fikcyjne nazwy zgodnie z założeniami MVP.
# ============================================================

COMMENTARY_TEMPLATE = """
Witamy na trasie Wielkiej Pętli Małopolski!

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

{USER_NAME} wygrywa etap Wielkiej Pętli Małopolski!

Co za debiut!

Co za emocje!

Cała Polska wstrzymała oddech!
"""


# ============================================================
# FUNKCJE
# ============================================================

def generate_commentary(user_name: str) -> str:
    """Podstawia nazwę użytkownika w przygotowanym scenariuszu."""
    return COMMENTARY_TEMPLATE.replace("{USER_NAME}", user_name)


@st.cache_data(show_spinner=False)
def generate_audio(text: str) -> bytes:
    """
    Generuje MP3 przez Google Text-to-Speech.

    Funkcja jest cache'owana, dzięki czemu ponowne odtworzenie
    tego samego komentarza nie wymaga ponownego generowania audio.
    """
    audio_buffer = io.BytesIO()

    tts = gTTS(
        text=text,
        lang="pl",
        slow=False,
    )

    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    return audio_buffer.read()


def audio_player(audio_bytes: bytes):
    """
    Osadza natywny HTML5 audio player.

    Dzięki temu użytkownik telefonu otrzymuje standardowy
    przycisk Play/Pause i może słuchać komentarza przez słuchawki.
    """
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    player = f"""
        <audio
            controls
            preload="metadata"
            style="
                width: 100%;
                margin-top: 10px;
                border-radius: 12px;
            "
        >
            <source
                src="data:audio/mpeg;base64,{audio_base64}"
                type="audio/mpeg"
            >
            Twoja przeglądarka nie obsługuje elementu audio.
        </audio>
    """

    st.markdown(player, unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "started" not in st.session_state:
    st.session_state.started = False

if "commentary" not in st.session_state:
    st.session_state.commentary = ""

if "audio" not in st.session_state:
    st.session_state.audio = None


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-icon">🚴</div>
        <h1>PELOTON LIVE</h1>
        <p>Poczuj się jak zawodowiec.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# WYBÓR WYŚCIGU
# ============================================================

st.markdown('<div class="card">', unsafe_allow_html=True)

st.markdown(
    '<div class="section-title">Wybierz etap</div>',
    unsafe_allow_html=True,
)

selected_race = st.selectbox(
    "Etap",
    options=list(RACES.keys()),
    label_visibility="collapsed",
)

race_info = RACES[selected_race]

if race_info["available"]:
    st.markdown(
        f"""
        <div class="route-card">
            <div class="route-name">{html.escape(selected_race)}</div>
            <div class="route-meta">
                {race_info["description"]}
                &nbsp; • &nbsp;
                {race_info["distance"]}
                &nbsp; • &nbsp;
                {race_info["terrain"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info(
        "🔒 Ten etap jest obecnie zablokowany. "
        "Zostanie udostępniony w jednej z przyszłych aktualizacji."
    )

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# PERSONALIZACJA
# ============================================================

st.markdown('<div class="card">', unsafe_allow_html=True)

st.markdown(
    '<div class="section-title">Twój zawodnik</div>',
    unsafe_allow_html=True,
)

user_name = st.text_input(
    "Imię i nazwisko",
    value="Anonimowy Kolarz",
    max_chars=60,
    placeholder="np. Jan Kowalski",
    label_visibility="collapsed",
)

st.caption(
    "Komentator będzie używał tego imienia podczas relacji."
)

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# START
# ============================================================

if not race_info["available"]:
    st.button(
        "🔒 ETAP ZABLOKOWANY",
        disabled=True,
        use_container_width=True,
    )
else:
    if st.button(
        "🔥 START WYŚCIGU",
        type="primary",
        use_container_width=True,
    ):
        clean_name = user_name.strip()

        if not clean_name:
            clean_name = "Anonimowy Kolarz"

        with st.spinner("🎙️ Komentator przygotowuje relację..."):
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

                st.warning(
                    "Nie udało się wygenerować nagrania audio. "
                    "Sprawdź połączenie z internetem."
                )


# ============================================================
# EKRAN WYŚCIGU
# ============================================================

if st.session_state.started:

    st.markdown(
        """
        <div class="status">
            🔴 RELACJA LIVE • JEDZIEMY!
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">🎙️ Relacja komentatora</div>',
        unsafe_allow_html=True,
    )

    # Escapowanie tekstu chroni przed przypadkowym wykonaniem
    # HTML wpisanego przez użytkownika.
    safe_commentary = html.escape(
        st.session_state.commentary
    ).replace("\n", "<br>")

    st.markdown(
        f"""
        <div class="commentary">
            {safe_commentary}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # HTML5 audio z natywnym Play/Pause
    if st.session_state.audio:
        audio_player(st.session_state.audio)

    st.markdown("</div>", unsafe_allow_html=True)

    # Przydatne podczas testowania MVP.
    with st.expander("📜 Pokaż pełny tekst relacji"):
        st.write(st.session_state.commentary)


# ============================================================
# INFORMACJE / INSTRUKCJA
# ============================================================

st.markdown('<div class="card">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="section-title">🎧 Jak korzystać?</div>

    <p style="color:#aab1bd; line-height:1.7;">
        1. Załóż słuchawki.<br>
        2. Wpisz swoje imię i nazwisko.<br>
        3. Wybierz dostępny etap.<br>
        4. Naciśnij <b>START WYŚCIGU</b>.<br>
        5. Uruchom relację i ruszaj!
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
        PELOTON LIVE • MVP<br>
        Fikcyjny wyścig sportowy • Projekt demonstracyjny
    </div>
    """,
    unsafe_allow_html=True,
)
```
