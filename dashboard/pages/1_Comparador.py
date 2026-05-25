"""
Comparador de Pokémon — tarjetas visuales, radar de stats y BST comparado.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import (
    load_data,
    TYPE_COLORS, TYPE_ES, STAT_COLS, STAT_LABELS,
    type_badge_html, pokemon_display_name,
)

st.set_page_config(page_title="Comparador", layout="wide")
st.title("Comparador de Pokémon")
st.caption(
    "Selecciona entre 2 y 6 Pokémon para ver sus estadísticas cara a cara. "
    "El radar muestra el perfil completo de cada uno; la barra inferior compara el BST total."
)

df_all = load_data()
df     = df_all[df_all["id"] < 10000].sort_values("id")

seleccion = st.multiselect(
    "Pokémon a comparar",
    df["name"].tolist(),
    default=["bulbasaur", "charmander", "squirtle"],
    format_func=pokemon_display_name,
    max_selections=6,
)

# Colorear cada chip del multiselect con el color del tipo del Pokémon seleccionado
if seleccion:
    chip_css = []
    for i, name in enumerate(seleccion):
        row_m = df[df["name"] == name]
        if not row_m.empty:
            color = TYPE_COLORS.get(row_m.iloc[0]["type1"], "#888888")
            chip_css.append(
                f'[data-baseweb="tag"]:nth-child({i + 1})'
                f'{{background:{color}bb!important;border:1px solid {color}!important;color:#fff!important;}}'
            )
    if chip_css:
        st.markdown(f"<style>{''.join(chip_css)}</style>", unsafe_allow_html=True)

if len(seleccion) < 2:
    st.info("Selecciona al menos 2 Pokémon para comparar.")
    st.stop()

# Preservar el orden de selección del usuario (no el orden del Pokédex)
sel = df[df["name"].isin(seleccion)].set_index("name").loc[seleccion].reset_index().copy()

# ── Tarjetas de Pokémon ───────────────────────────────────────────────────
st.divider()
card_cols = st.columns(len(sel))
for col, (_, row) in zip(card_cols, sel.iterrows()):
    with col:
        t1    = row["type1"]
        color = TYPE_COLORS.get(t1, "#888888")
        sprite = row["sprite_default"]
        name   = pokemon_display_name(row["name"])
        bst    = int(row["bst"]) if pd.notna(row["bst"]) else "—"

        if pd.notna(sprite) and sprite:
            img_html = (
                f'<img src="{sprite}" width="120" '
                f'style="object-fit:contain;image-rendering:pixelated;">'
            )
        else:
            img_html = (
                '<div style="height:120px;display:flex;align-items:center;'
                'justify-content:center;color:#555;font-size:2em;">?</div>'
            )

        badges_html = type_badge_html(t1, "12px")
        if pd.notna(row["type2"]):
            badges_html += " " + type_badge_html(row["type2"], "12px")

        st.markdown(
            f"""
            <div style="background:linear-gradient(160deg,{color}28,{color}0a);
                        border:1px solid {color}66;border-radius:14px;
                        padding:20px 12px 16px;text-align:center;">
              {img_html}
              <div style="font-size:1.05em;font-weight:700;margin-top:10px;
                          color:#eee;">{name}</div>
              <div style="margin:6px 0;">{badges_html}</div>
              <div style="color:#888;font-size:.82em;letter-spacing:1px;">
                BST &nbsp; {bst}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

# ── BST comparado ─────────────────────────────────────────────────────────
st.subheader("BST total comparado")
bst_rows = [
    {"Pokémon": pokemon_display_name(r["name"]),
     "BST": int(r["bst"]),
     "tipo": r["type1"]}
    for _, r in sel.iterrows()
]
df_bst = pd.DataFrame(bst_rows)
fig_bst = px.bar(
    df_bst, x="BST", y="Pokémon",
    orientation="h",
    color="tipo", color_discrete_map=TYPE_COLORS,
    text="BST",
    range_x=[0, 750],
    labels={"BST": "Base Stat Total", "Pokémon": ""},
    template="plotly_dark",
)
fig_bst.update_traces(textposition="outside")
fig_bst.update_layout(
    height=100 + len(sel) * 52,
    showlegend=False,
    yaxis=dict(autorange="reversed"),
    margin=dict(r=80, t=10, b=10),
)
st.plotly_chart(fig_bst, use_container_width=True)

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
