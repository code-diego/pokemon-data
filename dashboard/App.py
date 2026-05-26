"""
dashboard Pokémon — Vista general
> streamlit run dashboard/App.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import (
    TYPE_COLORS, TYPE_ES, GEN_ORDER,
    STAT_COLS, load_data, pokemon_display_name,
    IS_SAMPLE_DB,
)

st.set_page_config(page_title="Pokemon Explorer", page_icon="", layout="wide")
st.title("Pokémon Data Explorer")
st.caption(
    "Explora los 1 025 Pokémon del Pokédex nacional. "
    "Filtra por generación, tipo o categoría en el sidebar — todas las gráficas se actualizan en tiempo real."
)

if IS_SAMPLE_DB:
    st.info(
        "ℹ️ **Modo demostración** — mostrando datos de muestra (generaciones I–III, ~150 Pokémon). "
        "Para los 1 025 Pokémon completos, clona el repo y ejecuta "
        "`python scripts/fetch.py && python scripts/build_db.py`."
    )

df_all = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")
    incluir_formas = st.checkbox(
        "Incluir formas alternativas", value=False,
        help="Las 325 formas (mega, regional, gmax…) usan id ≥ 10 000. "
             "Desmarca para trabajar solo con los 1 025 del Pokédex nacional.",
    )
    gens_disponibles = [g for g in GEN_ORDER if g in df_all["gen"].values]
    gen_sel = st.multiselect("Generación", gens_disponibles, default=gens_disponibles)
    tipos_disponibles = sorted(TYPE_COLORS.keys())
    tipo_sel = st.multiselect(
        "Tipo primario", tipos_disponibles, default=tipos_disponibles,
        format_func=lambda t: f"{TYPE_ES.get(t, t)} ({t})",
    )
    cat_sel = st.multiselect(
        "Categoría", ["Normal", "Legendario", "Mitico"],
        default=["Normal", "Legendario", "Mitico"],
    )

# ── Filtros ───────────────────────────────────────────────────────────────
df = df_all.copy()
if not incluir_formas:
    df = df[df["id"] < 10000]
if gen_sel:
    df = df[df["gen"].isin(gen_sel)]
if tipo_sel:
    df = df[df["type1"].isin(tipo_sel)]
if cat_sel:
    df = df[df["categoria"].isin(cat_sel)]

# ── KPIs ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Pokémon", len(df))
col2.metric(
    "Legendarios + Míticos",
    int((df["categoria"] != "Normal").sum()),
    help="Pokémon de captura especial o no disponibles en la historia principal.",
)
col3.metric(
    "Dual-tipo",
    f"{df['dual_tipo'].sum()} ({df['dual_tipo'].mean()*100:.0f}%)" if len(df) else "—",
    help="Pokémon con dos tipos asignados — tienen interacciones de daño más complejas "
         "y pueden acumular debilidades o resistencias.",
)
st.divider()

if df.empty:
    st.warning("Ningún Pokémon coincide con los filtros actuales.")
    st.stop()

# ── Gráficas ──────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Tipos", "Peso & Altura"])

with tab1:
    counts = (df["type1"].value_counts()
              .reset_index()
              .rename(columns={"type1": "tipo", "count": "n"})
              .sort_values("n"))
    fig = px.bar(
        counts, x="n", y="tipo", orientation="h",
        color="tipo", color_discrete_map=TYPE_COLORS,
        labels={"n": "Pokémon", "tipo": "Tipo primario"},
        title="Distribución de tipos primarios",
        template="plotly_dark",
    )
    fig.update_layout(showlegend=False, height=520)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    ds = df[df["weight_kg"].notna() & df["height_m"].notna()].copy()
    if len(ds) > 1:
        ds = ds[(ds["weight_kg"] <= ds["weight_kg"].quantile(0.99)) &
                (ds["height_m"]  <= ds["height_m"].quantile(0.99))]
    fig2 = px.scatter(
        ds, x="weight_kg", y="height_m",
        color="type1", color_discrete_map=TYPE_COLORS,
        size="bst", size_max=18,
        hover_name="name",
        hover_data={"type1": True, "type2": True, "bst": True,
                    "weight_kg": ":.1f", "height_m": ":.1f"},
        labels={"weight_kg": "Peso (kg)", "height_m": "Altura (m)",
                "type1": "Tipo primario", "bst": "BST"},
        title="Peso vs Altura  (tamaño = BST)",
        template="plotly_dark",
    )
    fig2.update_layout(legend_title_text="Tipo primario", height=540)
    st.plotly_chart(fig2, use_container_width=True)


# ── Tabla filtrada ────────────────────────────────────────────────────────
st.divider()
st.subheader(f"Tabla — {len(df)} Pokémon")
cols_tabla = ["id", "name", "type1", "type2", "bst", "gen", "categoria",
              "height_m", "weight_kg"]
tbl = df[cols_tabla].sort_values("id").reset_index(drop=True).copy()
tbl["name"] = tbl["name"].apply(pokemon_display_name)
tbl.columns = ["#", "Nombre", "Tipo 1", "Tipo 2", "BST", "Gen",
               "Categoría", "Altura (m)", "Peso (kg)"]
st.dataframe(tbl, use_container_width=True, height=340)
