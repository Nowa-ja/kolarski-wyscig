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
# STYL UI (Zachowany w 100% z Twojego kodu)
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
# INITIALIZATION / SESSION STATE
# Dynamiczna baza wyścigów zintegrowana z Twoim słownikiem RACES
# ============================================================

if "dynamic_races" not in st.session_state:
    st.session_state.dynamic_races = {
        "🚴 Wielka Pętla Małopolski": {
            "available": True,
            "description": "Etap lokalny • Darmowy",
            "distance": "42 km",
            "terrain": "Góry + szosa",
            "is_custom": False,
            "kolarze": [],
            "relacja_live": []
        },
        "🔒 Wielki Wyścig Narodowy": {
            "available": False,
            "description": "Premium • Wkrótce",
            "distance": "—",
            "terrain": "—",
            "is_custom": False,
            "kolarze": [],
            "relacja_live": []
        },
        "🔒 Sekretny Tunel Miejski": {
            "available": False,
            "description": "Premium • Wkrótce",
            "distance": "—",
            "terrain": "—",
            "is_custom": False,
            "kolarze": [],
            "relacja_live": []
        },
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
        <p>Poczuj się jak zawodowiec.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KREATOR NOWYCH WYŚCIGÓW
# ============================================================

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">➕ Stwórz nowy wyścig komentatorski</div>', unsafe_allow_html=True)
with st.expander("Kliknij tutaj, aby dodać nowy radiowy wyścig"):
    nazwa_nowego = st.text_input("Nazwa wyścigu:", placeholder="np. Wyścig Dookoła Tatr")
    dystans_nowego = st.text_input("Dystans etapu:", placeholder="np. 85 km")
    teren_nowego = st.text_input("Ukształtowanie terenu:", placeholder="np. Ciężkie podjazdy, szosa")
    
    if st.button("Zapisz i utwórz wyścig"):
        if nazwa_nowego.strip():
            klucz = f"🚴 {nazwa_nowego}"
            st.session_state.dynamic_races[klucz] = {
                "available": True,
                "description": "Transmisja radiowa live • Własny wyścig",
                "distance": dystans_nowego if dystans_nowego else "—",
                "terrain": teren_nowego if teren_nowego else "—",
                "is_custom": True,
                "kolarze": [],
                "relacja_live": []
            }
            st.success(f"Dodano wyścig: {klucz}!")
            st.rerun()
        else:
            st.error("Wpisz nazwę wyścigu!")
st.markdown("</div>", unsafe_allow_html=True)
# ============================================================
# WYBÓR WYŚCIGU
# ============================================================

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Wybierz etap</div>', unsafe_allow_html=True)

selected_race = st.selectbox(
    "Etap",
    options=list(st.session_state.dynamic_races.keys()),
    label_visibility="collapsed",
)

race_info = st.session_state.dynamic_races[selected_race]

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
# TRYB 1: FABRYCZNY (Z Twoją pełną logiką zakończenia)
# ============================================================
if race_info["available"] and not race_info["is_custom"]:

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

    # PRZYCISK START
    if st.button("🔥 START WYŚCIGU", type="primary", use_container_width=True):
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
                st.warning("Nie udało się wygenerować nagrania audio. Sprawdź połączenie z internetem.")

    # EKRAN TRANSMISJI FABRYCZNEJ
    if st.session_state.started:
        st.markdown('<div class="status">🔴 RELACJA LIVE • JEDZIEMY!</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎙️ Relacja komentatora</div>', unsafe_allow_html=True)
        
        safe_commentary = html.escape(st.session_state.commentary).replace("\n", "<br>")
        st.markdown(f'<div class="commentary">{safe_commentary}</div>', unsafe_allow_html=True)
        
        # Twój player HTML5 z natywnym Play/Pause
        if st.session_state.audio:
            audio_player(st.session_state.audio)

        st.markdown("</div>", unsafe_allow_html=True)

        # Przydatne podczas testowania MVP.
        with st.expander("📜 Pokaż pełny tekst relacji"):
            st.write(st.session_state.commentary)
# ============================================================
# TRYB 2: WŁASNY WYŚCIG (Dynamiczne Studio Komentatorskie Live)
# ============================================================
elif race_info["available"] and race_info["is_custom"]:

    # Panel dodawania nowych kolarzy
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">👥 Uczestnicy wyścigu i nowe twarze</div>', unsafe_allow_html=True)
    c_k1, c_k2 = st.columns()
    with c_k1:
        nowy_zawodnik = st.text_input("Dodaj nowego, nieznanego zawodnika:", placeholder="np. Marian Kowal (Team Custom)", label_visibility="collapsed")
    with c_k2:
        if st.button("➕ Dodaj", use_container_width=True):
            if nowy_zawodnik.strip() and nowy_zawodnik not in race_info["kolarze"]:
                race_info["kolarze"].append(nowy_zawodnik.strip())
                st.rerun()
                
    if race_info["kolarze"]:
        st.caption("**Lista nowych zawodników w tym wyścigu:** " + ", ".join(race_info["kolarze"]))
    st.markdown("</div>", unsafe_allow_html=True)

    # Panel Mikrofonu Komentatora
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎙️ MIKROFON KOMENTATORA LIVE</div>', unsafe_allow_html=True)
    
    tekst_komunikatu = st.text_area("Wpisz na bieżąco tekst relacji radiowej:", height=100, placeholder="np. Niewiarygodny moment! Nowy zawodnik ucieka z grupy...")
    
    if st.button("🔊 WYŚLIJ KOMUNIKAT NA ANTENĘ", type="primary", use_container_width=True):
        if tekst_komunikatu.strip():
            race_info["relacja_live"].insert(0, tekst_komunikatu.strip())
            try:
                st.session_state.custom_audio = generate_audio(tekst_komunikatu.strip())
            except:
                st.session_state.custom_audio = None
                st.warning("Błąd sieci gTTS przy generowaniu audio.")
            st.rerun()

    if st.session_state.custom_audio:
        st.markdown('**Ostatnie nagranie audio:**')
        audio_player(st.session_state.custom_audio)

    # Kronika wydarzeń
    st.markdown('<div class="section-title" style="margin-top: 1.5rem;">📜 KRONIKA WYDARZEŃ (Od najnowszych)</div>', unsafe_allow_html=True)
    if race_info["relacja_live"]:
        historia_html = "<br><br>".join([f"• {html.escape(wpis)}" for wpis in race_info["relacja_live"]])
        st.markdown(f'<div class="commentary">{historia_html}</div>', unsafe_allow_html=True)
    else:
        st.caption("Cisza w eterze. Napisz swój pierwszy komunikat wyżej!")
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# INFORMACJE / INSTRUKCJA (Twoja sekcja końcowa)
# ============================================================

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="section-title">🎧 Jak korzystać?</div>
    <p style="color:#aab1bd; line-height:1.7;">
        1. Załóż słuchawki.<br>
        2. Wpisz swoje imię i nazwisko (lub twórz własne wyścigi).<br>
        3. Wybierz dostępny etap.<br>
        4. Naciśnij <b>START WYŚCIGU</b> ut nadawaj komunikaty live.<br>
        5. Uruchom relację i ruszaj!
    </p>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# STOPKA (Twoja autorska stopka MVP)
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
