"""
Pokédex — Ficha individual: sprite, tipos, estadísticas y efectividad de tipos.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from data import (
    load_data, defensive_profile,
    TYPE_COLORS, TYPE_ES, STAT_COLS, STAT_LABELS,
    type_badge_html, pokemon_display_name,
)

st.set_page_config(page_title="Pokédex", layout="wide")
st.title("Pokédex")
st.caption(
    "Ficha individual: stats, tipos, métricas de juego y tabla completa de debilidades y resistencias. "
    "Busca por nombre en el selector o desplázate por el Pokédex."
)

df_all = load_data()
df     = df_all[df_all["id"] < 10000].sort_values("id")

id_map = df.set_index("name")["id"].to_dict()
nombre = st.selectbox(
    "Buscar Pokémon",
    df["name"].tolist(),
    format_func=lambda n: f"#{id_map[n]:04d}  {pokemon_display_name(n)}",
)

row = df[df["name"] == nombre].iloc[0]

st.divider()

# ── Layout principal ──────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 2])

with col_left:
    # Franja de color del tipo primario
    t_color = TYPE_COLORS.get(row["type1"], "#888888")
    st.markdown(
        f'<div style="background:linear-gradient(90deg,{t_color},{t_color}22,transparent);'
        f'height:5px;border-radius:4px;margin-bottom:14px;"></div>',
        unsafe_allow_html=True,
    )

    # Sprite
    sprite = row["sprite_default"]
    if pd.notna(sprite) and sprite:
        st.image(sprite, width=220)
    else:
        st.caption("*(sin sprite)*")

    # Número Pokédex (estilo badge)
    st.markdown(
        f'<div style="color:#666;font-size:.8em;letter-spacing:3px;'
        f'margin-top:10px;font-family:monospace;">#{row["id"]:04d}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {pokemon_display_name(row['name'])}")

    # Badges de tipo
    badges = type_badge_html(row["type1"], "15px")
    if pd.notna(row["type2"]):
        badges += "  " + type_badge_html(row["type2"], "15px")
    st.markdown(badges, unsafe_allow_html=True)

    st.divider()

    # Métricas con emoji
    m1, m2 = st.columns(2)
    m1.metric(
        "⚔️ BST",
        int(row["bst"]) if pd.notna(row["bst"]) else "—",
        help="Base Stat Total — suma de los 6 stats base. "
             "Media global: 427 · Legendarios suelen superar 580.",
    )
    m2.metric("🌍 Generación", row["gen"] if pd.notna(row["gen"]) else "—")

    m3, m4 = st.columns(2)
    m3.metric("⭐ Categoría", row["categoria"])
    m4.metric(
        "🎯 Captura",
        int(row["capture_rate"]) if pd.notna(row["capture_rate"]) else "—",
        help="Tasa de captura: 255 = muy fácil · 45 = difícil · 3 = extremadamente difícil.",
    )

    m5, m6 = st.columns(2)
    m5.metric("📏 Altura",  f"{row['height_m']:.1f} m"   if pd.notna(row["height_m"])  else "—")
    m6.metric("⚖️ Peso",    f"{row['weight_kg']:.1f} kg"  if pd.notna(row["weight_kg"]) else "—")

    if pd.notna(row["base_happiness"]):
        st.metric(
            "😊 Felicidad",
            int(row["base_happiness"]),
            help="Felicidad base al capturarlo. Afecta evoluciones por amistad "
                 "y la potencia de algunos movimientos.",
        )

with col_right:
    tab_stats, tab_weak = st.tabs(["Estadísticas base", "Efectividad de tipos"])

    with tab_stats:
        vals = [int(row[c]) if pd.notna(row[c]) else 0 for c in STAT_COLS]
        fig = px.bar(
            x=vals, y=STAT_LABELS,
            orientation="h",
            color=vals,
            color_continuous_scale="RdYlGn",
            range_x=[0, 255],
            text=vals,
            labels={"x": "Valor", "y": ""},
            template="plotly_dark",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=340,
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
            margin=dict(l=10, r=60, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_weak:
        t1 = row["type1"]
        t2 = row["type2"] if pd.notna(row["type2"]) else None
        profile = defensive_profile(t1, t2)

        buckets = {4: [], 2: [], 0.5: [], 0.25: [], 0: []}
        for atk, mult in profile.items():
            rounded = round(mult, 4)
            for key in buckets:
                if abs(rounded - key) < 0.01:
                    buckets[key].append(atk)
                    break

        labels_map = {
            4:    "×4  Muy débil",
            2:    "×2  Débil",
            0.5:  "×½  Resiste",
            0.25: "×¼  Muy resistente",
            0:    "×0  Inmune",
        }
        has_any = False
        for mult_key in [4, 2, 0.5, 0.25, 0]:
            types = buckets[mult_key]
            if types:
                has_any = True
                st.markdown(f"**{labels_map[mult_key]}**")
                st.markdown(" ".join(type_badge_html(t) for t in sorted(types)),
                            unsafe_allow_html=True)
                st.write("")

        neutral = [atk for atk, mult in profile.items()
                   if abs(round(mult, 4) - 1.0) < 0.01]
        if neutral:
            with st.expander(f"Neutral (×1) — {len(neutral)} tipos"):
                st.markdown(" ".join(type_badge_html(t) for t in sorted(neutral)),
                            unsafe_allow_html=True)

        if not has_any and not neutral:
            st.info("Sin datos de tipo disponibles.")
