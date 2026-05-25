"""
Análisis estadístico: correlaciones, distribuciones y comparación de grupos.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from data import load_data, STAT_COLS, STAT_LABELS

st.set_page_config(page_title="Análisis Estadístico", layout="wide")
st.title("Análisis Estadístico")
st.caption("Solo formas base (1 025 Pokémon, id < 10 000).")

df_all = load_data()
df     = df_all[df_all["id"] < 10000].copy()

tab1, tab2, tab3 = st.tabs(["Correlaciones", "Distribuciones", "Comparación de grupos"])

# ── Correlaciones ─────────────────────────────────────────────────────────
with tab1:
    st.subheader("Matriz de correlación")
    st.caption("Pearson entre stats, BST, altura y peso.")
    cols_c = STAT_COLS + ["bst", "height_m", "weight_kg"]
    labs_c = STAT_LABELS + ["BST", "Altura (m)", "Peso (kg)"]
    corr   = df[cols_c].rename(columns=dict(zip(cols_c, labs_c))).corr()

    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        aspect="auto",
        template="plotly_dark",
    )
    fig.update_layout(
        title="Correlación entre estadísticas base, dimensiones y BST",
        height=540,
        coloraxis_colorbar=dict(title="r"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
**Cómo leer la matriz:**
- **r ≈ +1** (rojo): cuando una sube, la otra también tiende a subir.
- **r ≈ -1** (azul): relación inversa.
- **r ≈ 0** (blanco): sin correlación lineal.

El BST correlaciona fuerte con todos los stats porque es su suma.
La correlación entre stats individuales (p.ej. velocidad vs defensa) revela
qué perfiles de Pokémon existen — un tanque no es veloz, un velocista no es un muro.
""")

# ── Distribuciones ───────────────────────────────────────────────────────
with tab2:
    stat_options = dict(zip(STAT_LABELS + ["BST"], STAT_COLS + ["bst"]))
    stat_sel = st.selectbox("Stat a visualizar", list(stat_options.keys()), index=6)
    col_sel  = stat_options[stat_sel]

    fig2 = px.histogram(
        df,
        x=col_sel,
        color="categoria",
        color_discrete_map={
            "Normal":"#4a9eff","Legendario":"#ffd700","Mitico":"#ff6ec7"
        },
        barmode="overlay",
        opacity=0.7,
        nbins=40,
        labels={col_sel: stat_sel, "categoria": "Categoría"},
        title=f"Distribución de {stat_sel} por categoría",
        template="plotly_dark",
    )
    fig2.update_layout(height=420, legend_title_text="Categoría")
    st.plotly_chart(fig2, use_container_width=True)

    desc = df.groupby("categoria")[col_sel].describe().round(1)
    st.dataframe(desc, use_container_width=True)

# ── Comparación de grupos ─────────────────────────────────────────────────
with tab3:
    st.subheader("Legendarios/Míticos vs. Normales")

    stat_opt2 = dict(zip(STAT_LABELS + ["BST"], STAT_COLS + ["bst"]))
    stat_g = st.selectbox("Stat a comparar", list(stat_opt2.keys()),
                          index=6, key="stat_group")
    col_g  = stat_opt2[stat_g]

    df_g = df.copy()
    df_g["grupo"] = df_g["categoria"].replace({"Legendario":"Especial","Mitico":"Especial"})

    fig3 = px.violin(
        df_g, y=col_g, x="grupo", color="grupo",
        color_discrete_map={"Normal":"#4a9eff","Especial":"#ffd700"},
        box=True, points="outliers",
        labels={col_g: stat_g, "grupo": "Grupo"},
        title=f"{stat_g}: Normales vs. Especiales (legendarios + míticos)",
        template="plotly_dark",
    )
    fig3.update_layout(height=460, showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

    # Test estadístico
    try:
        from scipy import stats as sp_stats

        normal = df_g[df_g["grupo"]=="Normal"][col_g].dropna()
        espec  = df_g[df_g["grupo"]=="Especial"][col_g].dropna()
        stat_val, pvalue = sp_stats.mannwhitneyu(espec, normal, alternative="greater")

        st.markdown("**Test Mann-Whitney U** (¿los especiales tienen mayor stat?)")
        col_u, col_p = st.columns(2)
        col_u.metric("Estadístico U", f"{stat_val:,.0f}")
        col_p.metric("p-valor", f"{pvalue:.2e}")

        if pvalue < 0.001:
            st.success(f"p = {pvalue:.2e} — diferencia estadísticamente muy significativa. "
                       f"Los legendarios/míticos tienen {stat_g} significativamente mayor que "
                       f"los Pokémon normales.")
        elif pvalue < 0.05:
            st.info(f"p = {pvalue:.2e} — diferencia significativa (p < 0.05).")
        else:
            st.warning(f"p = {pvalue:.2e} — sin evidencia estadística de diferencia "
                       f"para {stat_g}.")

    except ImportError:
        st.info("Instala scikit-learn/scipy para el test estadístico: "
                "`pip install scikit-learn`")
