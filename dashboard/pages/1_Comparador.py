"""
Comparador de Pokémon — sprites, radar de stats y tabla comparativa.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import (
    load_data,
    TYPE_COLORS, TYPE_ES, STAT_COLS, STAT_LABELS,
    type_badge_html, pokemon_display_name,
)

st.set_page_config(page_title="Comparador", layout="wide")
st.title("Comparador de Pokémon")
st.caption("Selecciona 2 a 6 Pokémon para comparar sus estadísticas base.")

df_all = load_data()
df     = df_all[df_all["id"] < 10000].sort_values("id")

seleccion = st.multiselect(
    "Pokémon a comparar",
    df["name"].tolist(),
    default=["bulbasaur", "charmander", "squirtle"],
    format_func=pokemon_display_name,
    max_selections=6,
)

if len(seleccion) < 2:
    st.info("Selecciona al menos 2 Pokémon para comparar.")
    st.stop()

sel = df[df["name"].isin(seleccion)].copy()

# ── Fila de sprites ───────────────────────────────────────────────────────
st.divider()
sprite_cols = st.columns(len(sel))
for col, (_, row) in zip(sprite_cols, sel.iterrows()):
    with col:
        sprite = row["sprite_default"]
        if pd.notna(sprite) and sprite:
            st.image(sprite, width=120)
        st.markdown(f"**{pokemon_display_name(row['name'])}**")
        badges = type_badge_html(row["type1"], "13px")
        if pd.notna(row["type2"]):
            badges += " " + type_badge_html(row["type2"], "13px")
        st.markdown(badges, unsafe_allow_html=True)

st.divider()

# ── Radar de stats ────────────────────────────────────────────────────────
st.subheader("Radar de estadísticas base")

fallback_palette = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]
fig = go.Figure()

for i, (_, row) in enumerate(sel.iterrows()):
    vals        = [int(row[c]) if pd.notna(row[c]) else 0 for c in STAT_COLS]
    vals_closed = vals + [vals[0]]
    lbl_closed  = STAT_LABELS + [STAT_LABELS[0]]
    t1          = row["type1"]
    color       = TYPE_COLORS.get(t1, fallback_palette[i % len(fallback_palette)])

    fig.add_trace(go.Scatterpolar(
        r=vals_closed,
        theta=lbl_closed,
        fill="toself",
        name=pokemon_display_name(row["name"]),
        line=dict(color=color, width=2),
        opacity=0.75,
    ))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 255])),
    template="plotly_dark",
    height=520,
    legend=dict(font=dict(size=13)),
)
st.plotly_chart(fig, use_container_width=True)

# ── Tabla comparativa ─────────────────────────────────────────────────────
st.subheader("Tabla comparativa")

cols_show = ["name", "type1", "type2"] + STAT_COLS + ["bst", "gen", "categoria"]
table = sel[cols_show].copy()
table["name"] = table["name"].apply(pokemon_display_name)
table["tipo"] = table.apply(
    lambda r: TYPE_ES.get(r["type1"], r["type1"]) + (
        f" / {TYPE_ES.get(r['type2'], r['type2'])}" if pd.notna(r["type2"]) else ""
    ), axis=1
)
table = table.drop(columns=["type1", "type2"])
table.columns = ["Nombre", "Tipo"] + STAT_LABELS + ["BST", "Gen", "Categoría"]
table = table.set_index("Nombre")

st.dataframe(
    table.style.highlight_max(axis=0, color="#2a5e2e",
                              subset=STAT_LABELS + ["BST"]),
    use_container_width=True,
)
