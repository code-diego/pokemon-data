"""
Dashboard maqueta — Pokemon Data Explorer
Ejecutar: streamlit run dashboard/app.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ── Constantes de tema ────────────────────────────────────────────────────
TYPE_COLORS = {
    "normal": "#A8A77A",   "fire": "#EE8130",    "water": "#6390F0",
    "electric": "#F7D02C", "grass": "#7AC74C",   "ice": "#96D9D6",
    "fighting": "#C22E28", "poison": "#A33EA1",  "ground": "#E2BF65",
    "flying": "#A98FF3",   "psychic": "#F95587", "bug": "#A6B91A",
    "rock": "#B6A136",     "ghost": "#735797",   "dragon": "#6F35FC",
    "dark": "#705746",     "steel": "#B7B7CE",   "fairy": "#D685AD",
}
TYPE_ES = {
    "normal": "Normal",      "fire": "Fuego",      "water": "Agua",
    "electric": "Electrico", "grass": "Planta",    "ice": "Hielo",
    "fighting": "Lucha",     "poison": "Veneno",   "ground": "Tierra",
    "flying": "Volador",     "psychic": "Psiquico","bug": "Bicho",
    "rock": "Roca",          "ghost": "Fantasma",  "dragon": "Dragon",
    "dark": "Siniestro",     "steel": "Acero",     "fairy": "Hada",
}
GEN_MAP = {
    "generation-i": "Gen I",     "generation-ii": "Gen II",
    "generation-iii": "Gen III", "generation-iv": "Gen IV",
    "generation-v": "Gen V",     "generation-vi": "Gen VI",
    "generation-vii": "Gen VII", "generation-viii": "Gen VIII",
    "generation-ix": "Gen IX",
}
GEN_ORDER = ["Gen I","Gen II","Gen III","Gen IV","Gen V",
             "Gen VI","Gen VII","Gen VIII","Gen IX"]
STAT_COLS = ["hp","attack","defense","special-attack","special-defense","speed"]

# ── Carga de datos ────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    """Carga y une todas las tablas necesarias. @st.cache_data evita releer en cada interacción."""
    db = next(
        (p / "data" / "pokemon.db"
         for p in [Path.cwd(), *Path.cwd().parents]
         if (p / "data" / "pokemon.db").exists()),
        None,
    )
    if db is None:
        st.error("No se encontró data/pokemon.db. Ejecuta: python scripts/build_db.py")
        st.stop()

    con = sqlite3.connect(db)

    pokemon = pd.read_sql("SELECT * FROM pokemon", con)
    stats_l = pd.read_sql("SELECT * FROM pokemon_stats", con)
    species = pd.read_sql("SELECT * FROM species", con)
    tipos_db = pd.read_sql("SELECT * FROM pokemon_types", con)
    con.close()

    stats = (stats_l
             .pivot(index="pokemon_id", columns="stat_name", values="base_value")
             .reset_index())
    stats.columns.name = None

    tipo1 = (tipos_db[tipos_db["slot"] == 1][["pokemon_id", "type_name"]]
             .rename(columns={"type_name": "type1"}))
    tipo2 = (tipos_db[tipos_db["slot"] == 2][["pokemon_id", "type_name"]]
             .rename(columns={"type_name": "type2"}))

    df = (pokemon
          .merge(stats, left_on="id", right_on="pokemon_id", how="left").drop(columns="pokemon_id")
          .merge(tipo1, left_on="id", right_on="pokemon_id", how="left").drop(columns="pokemon_id")
          .merge(tipo2, left_on="id", right_on="pokemon_id", how="left").drop(columns="pokemon_id")
          .merge(species[["id","is_legendary","is_mythical","generation",
                           "capture_rate","base_happiness"]], on="id", how="left"))

    df["bst"] = df[STAT_COLS].sum(axis=1)
    df["categoria"] = "Normal"
    df.loc[df["is_legendary"] == 1, "categoria"] = "Legendario"
    df.loc[df["is_mythical"]  == 1, "categoria"] = "Mitico"
    df["dual_tipo"] = df["type2"].notna()
    df["height_m"]  = df["height"] / 10
    df["weight_kg"] = df["weight"] / 10
    df["gen"] = df["generation"].map(GEN_MAP).fillna(df["generation"])
    df["is_form"] = df["id"] >= 10000

    return df


# ── Layout principal ──────────────────────────────────────────────────────
st.set_page_config(page_title="Pokemon Explorer", page_icon="", layout="wide")
st.title("Pokémon Data Explorer")
st.caption("Dashboard maqueta — datos de PokéAPI vía SQLite")

df_all = load_data()

# ── Sidebar: filtros ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")

    incluir_formas = st.checkbox(
        "Incluir formas alternativas",
        value=False,
        help="Las 325 formas (mega, regional, gmax…) usan id ≥ 10 000. "
             "Desmarca para trabajar solo con los 1 025 Pokémon del Pokédex nacional.",
    )

    gens_disponibles = [g for g in GEN_ORDER if g in df_all["gen"].values]
    gen_sel = st.multiselect("Generación", gens_disponibles, default=gens_disponibles)

    tipos_disponibles = sorted(TYPE_COLORS.keys())
    tipo_sel = st.multiselect(
        "Tipo primario",
        tipos_disponibles,
        default=tipos_disponibles,
        format_func=lambda t: f"{TYPE_ES.get(t, t)} ({t})",
    )

    cat_sel = st.multiselect(
        "Categoría",
        ["Normal", "Legendario", "Mitico"],
        default=["Normal", "Legendario", "Mitico"],
    )

# ── Aplicar filtros ───────────────────────────────────────────────────────
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
col1, col2, col3, col4 = st.columns(4)
col1.metric("Pokémon", len(df))
col2.metric("BST medio", f"{df['bst'].mean():.0f}" if len(df) else "—")
col3.metric("Legendarios + Míticos",
            int((df["categoria"] != "Normal").sum()))
col4.metric("Dual-tipo",
            f"{df['dual_tipo'].sum()} ({df['dual_tipo'].mean()*100:.0f}%)" if len(df) else "—")

st.divider()

# ── Gráficas ──────────────────────────────────────────────────────────────
if df.empty:
    st.warning("Ningún Pokémon coincide con los filtros actuales.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Tipos", "Peso & Altura", "BST por Generación"])

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

with tab3:
    df_g = df[df["gen"].isin(GEN_ORDER)].copy()
    if not df_g.empty:
        sg = (df_g.groupby("gen")["bst"]
              .agg(media="mean", mediana="median", n="count")
              .reindex(GEN_ORDER).dropna())
        fig3 = px.line(
            sg.reset_index(), x="gen", y="media",
            markers=True,
            error_y=None,
            labels={"gen": "Generación", "media": "BST medio"},
            title="BST medio por generación",
            template="plotly_dark",
        )
        fig3.add_scatter(x=sg.index, y=sg["mediana"],
                         mode="lines+markers", name="Mediana BST",
                         line=dict(dash="dash", color="#87ceeb"))
        for gen, row in sg.iterrows():
            fig3.add_annotation(x=gen, y=row["media"],
                                text=f"n={int(row['n'])}",
                                showarrow=False, yshift=14,
                                font=dict(size=9, color="#aaa"))
        fig3.update_layout(height=420)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Sin datos de generación para los filtros actuales.")

# ── Tabla filtrada ────────────────────────────────────────────────────────
st.divider()
st.subheader(f"Tabla — {len(df)} Pokémon")
cols_tabla = ["id", "name", "type1", "type2", "bst", "gen", "categoria",
              "height_m", "weight_kg"]
st.dataframe(
    df[cols_tabla].sort_values("id").reset_index(drop=True),
    use_container_width=True,
    height=340,
)
