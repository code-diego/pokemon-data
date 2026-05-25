"""
Ficha individual de un Pokémon: sprite, tipos, estadísticas y debilidades.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from data import (
    load_data, defensive_profile,
    TYPE_ES, STAT_COLS, STAT_LABELS,
    type_badge_html,
)

st.set_page_config(page_title="Ficha Pokémon", layout="wide")
st.title("Ficha Individual")

df_all = load_data()
df     = df_all[df_all["id"] < 10000].sort_values("id")

id_map = df.set_index("name")["id"].to_dict()
nombre = st.selectbox(
    "Buscar Pokémon",
    df["name"].tolist(),
    format_func=lambda n: f"#{id_map[n]:04d}  {n.capitalize()}",
)

row = df[df["name"] == nombre].iloc[0]

# ── Cabecera ──────────────────────────────────────────────────────────────
col_img, col_info = st.columns([1, 3])

with col_img:
    sprite = row.get("sprite_default") if hasattr(row, "get") else row["sprite_default"]
    if pd.notna(sprite) and sprite:
        st.image(sprite, width=160)
    else:
        st.caption("(sin sprite)")

with col_info:
    st.header(row["name"].capitalize())

    badges = type_badge_html(row["type1"], "15px")
    if pd.notna(row.get("type2") if hasattr(row, "get") else row["type2"]):
        badges += "  " + type_badge_html(row["type2"], "15px")
    st.markdown(badges, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BST",        int(row["bst"]) if pd.notna(row["bst"]) else "—")
    m2.metric("Generación", row["gen"] if pd.notna(row["gen"]) else "—")
    m3.metric("Categoría",  row["categoria"])
    m4.metric("Captura",    int(row["capture_rate"]) if pd.notna(row["capture_rate"]) else "—")

st.divider()

# ── Stats + Debilidades ───────────────────────────────────────────────────
col_stats, col_weak = st.columns([1, 1])

with col_stats:
    st.subheader("Estadísticas base")
    vals = [int(row[c]) if pd.notna(row.get(c) if hasattr(row,"get") else row[c]) else 0
            for c in STAT_COLS]
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
        height=300,
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=60, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Físico
    col_a, col_b = st.columns(2)
    col_a.metric("Altura",  f"{row['height_m']:.1f} m"  if pd.notna(row["height_m"])  else "—")
    col_b.metric("Peso",    f"{row['weight_kg']:.1f} kg" if pd.notna(row["weight_kg"]) else "—")

with col_weak:
    st.subheader("Efectividad al recibir daño")
    t1 = row["type1"]
    t2_val = row["type2"] if not (hasattr(row,"get") and row.get("type2") is None) else None
    t2 = t2_val if pd.notna(t2_val) else None
    profile = defensive_profile(t1, t2)

    buckets = {4: [], 2: [], 0.5: [], 0.25: [], 0: []}
    for atk, mult in profile.items():
        rounded = round(mult, 4)
        for key in buckets:
            if abs(rounded - key) < 0.01:
                buckets[key].append(atk)
                break

    labels_map = {
        4: "×4  Muy débil",  2:    "×2  Débil",
        0.5:"×½  Resiste",   0.25: "×¼  Muy resistente",
        0:  "×0  Inmune",
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
    if not has_any:
        st.info("Sin datos de tipo disponibles.")
