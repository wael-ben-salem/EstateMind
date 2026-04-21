import pandas as pd
import streamlit as st
import pydeck as pdk

from data_loader import load_clean_data
from recommender_service import run_recommender_pipeline


st.set_page_config(
    page_title="EstateMind Recommender",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# STYLES
# =========================================================

st.markdown("""
<style>
    .main {
        background-color: #0f1117;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    h1, h2, h3 {
        color: white !important;
    }

    .hero-card {
        background: linear-gradient(135deg, #131720 0%, #1c2333 100%);
        padding: 1.5rem 1.8rem;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        margin-bottom: 1rem;
    }

    .assistant-box {
        background: #151925;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 1rem 1.2rem;
        color: #e8edf7;
        margin-bottom: 1rem;
    }

    .summary-box {
        background: #10141f;
        border-left: 4px solid #F58400;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        color: #dbe3f0;
        margin-bottom: 1rem;
    }

    .result-card {
        background: #151925;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 1rem 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }

    .result-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.4rem;
    }

    .pill {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        background: rgba(245,132,0,0.15);
        color: #ffb25b;
        font-size: 0.82rem;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }

    .metric-box {
        background: #151925;
        border-radius: 18px;
        padding: 1rem;
        border: 1px solid rgba(255,255,255,0.06);
        text-align: center;
    }

    .small-label {
        color: #9aa4b2;
        font-size: 0.82rem;
    }

    .small-value {
        color: white;
        font-size: 1.1rem;
        font-weight: 700;
    }

    .stTextInput > div > div > input {
        border-radius: 14px !important;
    }

    .stButton > button {
        border-radius: 14px !important;
        background-color: #F58400 !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def get_data():
    return load_clean_data()

df = get_data()

# =========================================================
# HELPERS
# =========================================================

def format_optional(value, default="Non disponible"):
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    return value

def build_map_dataframe(results):
    rows = []
    for item in results:
        lat = item.get("latitude")
        lon = item.get("longitude")

        if lat is not None and lon is not None:
            try:
                rows.append({
                    "title": item.get("title"),
                    "price": item.get("price"),
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "score": float(item.get("score", 0)),
                })
            except Exception:
                pass

    return pd.DataFrame(rows)

def render_result_card(item, idx):
    title = item.get("title") or f"Résultat {idx}"
    price = item.get("price", "Prix non disponible")
    city = item.get("city", "Zone non disponible")
    property_type = item.get("property_type", "Type non disponible")
    contract = item.get("contract", "Contrat non disponible")
    surface = format_optional(item.get("surface"))
    rooms = format_optional(item.get("rooms"))
    score = item.get("score", "N/A")
    explanation = item.get("explanation", "Aucune explication disponible.")
    url = item.get("url")
    reasons = item.get("reasons", [])

    reasons_html = ""
    if reasons:
        reasons_html = "".join([f'<span class="pill">{r}</span>' for r in reasons])

    st.markdown(f"""
    <div class="result-card">
        <div class="result-title">{title}</div>
        <div style="margin-bottom:0.6rem;">
            <span class="pill">{price}</span>
            <span class="pill">{city}</span>
            <span class="pill">{property_type}</span>
            <span class="pill">{contract}</span>
            <span class="pill">Surface: {surface}</span>
            <span class="pill">Pièces: {rooms}</span>
            <span class="pill">Score: {score}</span>
        </div>
        <div style="margin-bottom:0.6rem;">{reasons_html}</div>
        <div style="color:#dbe3f0; margin-bottom:0.7rem;">{explanation}</div>
    </div>
    """, unsafe_allow_html=True)

    if url:
        st.markdown(f"[Voir l'annonce]({url})")

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.title("🏡 EstateMind")
    st.markdown("Assistant immobilier intelligent connecté au moteur de recommandation.")

    st.markdown("### Suggestions")
    st.markdown("""
- appartement meublé à la marsa 1200 dt  
- maison vacances à hammamet avec piscine  
- maison familiale à sousse budget 300000  
- bien proche de la mer à hammamet pour vacances  
""")

    st.markdown("### Informations")
    st.caption("Le moteur gère la logique métier, le ranking et les explications.")
    st.caption("L’interface affiche les résultats sous forme de cards et map.")

# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="hero-card">
    <h1 style="margin-bottom:0.3rem;">EstateMind Recommender UI</h1>
    <p style="color:#c9d3e3; margin-bottom:0;">
        Recommandation immobilière intelligente avec compréhension de requête, ranking métier et visualisation des opportunités.
    </p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# INPUT AREA
# =========================================================

default_query = "appartement meuble a la marsa 1200 dt"

query = st.text_input(
    "Entrez votre recherche immobilière",
    value=default_query,
    placeholder="Ex: maison vacances à hammamet avec piscine"
)

search_clicked = st.button("Lancer la recherche")

# =========================================================
# MAIN ACTION
# =========================================================

if search_clicked and query.strip():
    response = run_recommender_pipeline(
        user_query=query,
        df=df,
        top_k=5
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="small-label">Status</div>
            <div class="small-value">{response.get("status", "-")}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        classification = response.get("classification", {})
        st.markdown(f"""
        <div class="metric-box">
            <div class="small-label">Classification</div>
            <div class="small-value">{classification.get("label", "-")}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        results_count = len(response.get("results", []))
        st.markdown(f"""
        <div class="metric-box">
            <div class="small-label">Résultats affichés</div>
            <div class="small-value">{results_count}</div>
        </div>
        """, unsafe_allow_html=True)

    if response.get("user_message"):
        st.markdown(f"""
        <div class="assistant-box">
            <strong>Assistant</strong><br><br>
            {response["user_message"]}
        </div>
        """, unsafe_allow_html=True)

    if response.get("summary"):
        st.markdown(f"""
        <div class="summary-box">
            <strong>Résumé</strong><br>
            {response["summary"]}
        </div>
        """, unsafe_allow_html=True)

    understanding = response.get("understanding")
    recommendation = response.get("recommendation")
    results = response.get("results", [])

    left_col, right_col = st.columns([1.15, 0.85])

    with left_col:
        st.subheader("Résultats recommandés")

        if recommendation and recommendation.get("global_explanation"):
            st.info(recommendation["global_explanation"])

        if recommendation and recommendation.get("used_relaxation"):
            st.warning(recommendation.get("message", "Relaxation intelligente utilisée."))

        if results:
            for idx, item in enumerate(results, start=1):
                render_result_card(item, idx)
        else:
            st.warning("Aucun résultat à afficher.")

    with right_col:
        st.subheader("Analyse de la requête")

        if understanding:
            st.json(understanding)

        st.subheader("Carte des opportunités")

        map_df = build_map_dataframe(results)

        if not map_df.empty:
            view_state = pdk.ViewState(
                latitude=map_df["latitude"].mean(),
                longitude=map_df["longitude"].mean(),
                zoom=10,
                pitch=35,
            )

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[longitude, latitude]',
                get_radius=120,
                pickable=True,
                opacity=0.8,
                stroked=True,
                filled=True,
                radius_min_pixels=6,
                radius_max_pixels=20,
                line_width_min_pixels=1,
                get_fill_color='[245, 132, 0, 180]',
                get_line_color='[255, 255, 255, 180]',
            )

            tooltip = {
                "html": "<b>{title}</b><br/>{price}<br/>Score: {score}",
                "style": {
                    "backgroundColor": "#111827",
                    "color": "white"
                }
            }

            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/dark-v11",
                initial_view_state=view_state,
                layers=[layer],
                tooltip=tooltip,
            ))
        else:
            st.info("Aucune coordonnée exploitable disponible pour afficher la carte.")

else:
    st.markdown("""
    <div class="assistant-box">
        <strong>Bienvenue</strong><br><br>
        Entrez une requête immobilière puis cliquez sur <strong>Lancer la recherche</strong> pour afficher les résultats, les explications et la carte.
    </div>
    """, unsafe_allow_html=True)