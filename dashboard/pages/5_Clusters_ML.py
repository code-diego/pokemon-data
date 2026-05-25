"""
Clustering de Pokémon por perfil de estadísticas base (K-means + PCA).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import load_data, STAT_COLS, STAT_LABELS

try:
    from ml import cluster_pokemon, label_archetype, ARCHETYPE_COLORS, sklearn_available
    _ML_OK = sklearn_available()
except ImportError:
    _ML_OK = False

st.set_page_config(page_title="Clustering ML", layout="wide")
st.title("Clustering de Arquetipos")
st.caption(
    "K-means sobre estadísticas base estandarizadas. "
    "Agrupa Pokémon por perfil, sin etiquetas previas — aprendizaje no supervisado."
)

if not _ML_OK:
    st.error("scikit-learn no está instalado. Ejecuta: `pip install scikit-learn`")
    st.stop()

df_all = load_data()
df_base = df_all[df_all["id"] < 10000].copy()

# ── Controles ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parámetros del modelo")
    k = st.slider("Número de clusters (k)", min_value=2, max_value=10, value=5)
    features_sel = st.multiselect(
        "Features (stats)",
        STAT_COLS, default=STAT_COLS,
        format_func=lambda c: dict(zip(STAT_COLS, STAT_LABELS))[c],
    )
    if len(features_sel) < 2:
        st.warning("Selecciona al menos 2 features.")
        st.stop()

# ── Ajuste del modelo ─────────────────────────────────────────────────────
with st.spinner("Ajustando K-means..."):
    df_cl, profiles, inertias = cluster_pokemon(df_base, k=k, features=features_sel)

archetypes = label_archetype(profiles, features_sel)
df_cl["arquetipo"] = df_cl["cluster"].map(archetypes)
color_map = {archetypes[i]: ARCHETYPE_COLORS[i % len(ARCHETYPE_COLORS)] for i in range(k)}

# ── Scatter PCA ───────────────────────────────────────────────────────────
st.subheader("Visualización PCA (2 componentes)")
st.caption("Cada punto es un Pokémon. Pasa el cursor para ver el nombre.")

fig_pca = px.scatter(
    df_cl, x="pca_x", y="pca_y",
    color="arquetipo",
    color_discrete_map=color_map,
    hover_name="name",
    hover_data={"pca_x": False, "pca_y": False, "bst": True, "cluster": False},
    labels={"pca_x": "PC 1", "pca_y": "PC 2", "arquetipo": "Arquetipo"},
    title=f"K-means k={k} — proyección PCA",
    template="plotly_dark",
    opacity=0.75,
)
fig_pca.update_traces(marker=dict(size=5))
fig_pca.update_layout(height=520, legend_title_text="Arquetipo")
st.plotly_chart(fig_pca, use_container_width=True)

# ── Perfil de clusters ────────────────────────────────────────────────────
st.subheader("Perfil medio por arquetipo")
st.caption("Media de cada stat base en la escala original. El color indica el valor relativo.")

feat_labels = [dict(zip(STAT_COLS, STAT_LABELS)).get(f, f) for f in features_sel]
prof_show = profiles[features_sel].copy()
prof_show.index = [archetypes.get(i, f"Grupo {i}") for i in prof_show.index]
prof_show.columns = feat_labels

fig_prof = px.imshow(
    prof_show,
    text_auto=".0f",
    color_continuous_scale="YlOrRd",
    aspect="auto",
    template="plotly_dark",
)
fig_prof.update_layout(height=300 + k * 20,
                       xaxis_title="Stat", yaxis_title="Arquetipo")
st.plotly_chart(fig_prof, use_container_width=True)

# ── Curva de codo ─────────────────────────────────────────────────────────
with st.expander("Gráfica de codo — cómo elegir k"):
    import numpy as np
    k_range = list(range(2, len(inertias) + 2))
    fig_elbow = px.line(
        x=k_range, y=inertias,
        markers=True,
        labels={"x": "k (clusters)", "y": "Inercia (WCSS)"},
        title="Curva de codo — inercia por número de clusters",
        template="plotly_dark",
    )
    fig_elbow.add_vline(x=k, line_dash="dash", line_color="#ffd700",
                        annotation_text=f"k={k} seleccionado")
    st.plotly_chart(fig_elbow, use_container_width=True)
    st.caption(
        "El 'codo' es el punto donde añadir más clusters deja de reducir "
        "significativamente la inercia. Elige k en ese punto de inflexión."
    )

# ── Tabla de Pokémon por arquetipo ────────────────────────────────────────
st.subheader("Pokémon por arquetipo")
arquetipo_sel = st.selectbox(
    "Ver Pokémon del arquetipo",
    sorted(df_cl["arquetipo"].unique()),
)
subset = (df_cl[df_cl["arquetipo"] == arquetipo_sel]
          [["name", "type1", "type2"] + features_sel + ["bst", "gen", "categoria"]]
          .sort_values("bst", ascending=False)
          .reset_index(drop=True))
subset["name"] = subset["name"].str.capitalize()
st.dataframe(subset, use_container_width=True, height=360)
