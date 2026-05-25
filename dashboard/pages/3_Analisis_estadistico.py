"""
Análisis estadístico: correlaciones, distribuciones y comparación de grupos.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from data import load_data, STAT_COLS, STAT_LABELS, TYPE_COLORS, TYPE_ES, pokemon_display_name

st.set_page_config(page_title="Análisis Estadístico", layout="wide")
st.title("Análisis Estadístico")
st.caption("Solo formas base (1 025 Pokémon, id < 10 000).")

df_all = load_data()
df     = df_all[df_all["id"] < 10000].copy()

tab1, tab2, tab3, tab4 = st.tabs(["Correlaciones", "Distribuciones", "Comparación de grupos", "BST por tipo"])

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

    # Insight automático: par de stats más y menos correlacionados
    stat_corr = corr.loc[STAT_LABELS, STAT_LABELS].copy()
    stat_corr = stat_corr.where(~np.eye(stat_corr.shape[0], dtype=bool))
    upper = stat_corr.where(np.triu(np.ones(stat_corr.shape, dtype=bool), k=1))
    flat  = upper.stack()
    if len(flat) >= 2:
        max_pair = flat.idxmax()
        min_pair = flat.idxmin()
        st.caption(
            f"💡 Mayor correlación entre stats: **{max_pair[0]} ↔ {max_pair[1]}** "
            f"(r = {flat[max_pair]:.2f}) · "
            f"menor: **{min_pair[0]} ↔ {min_pair[1]}** (r = {flat[min_pair]:.2f})"
        )

    st.markdown("""
**Cómo leer la matriz:**
- **r ≈ +1** (rojo): cuando una sube, la otra también tiende a subir.
- **r ≈ −1** (azul): relación inversa.
- **r ≈ 0** (blanco): sin correlación lineal.

El BST correlaciona fuerte con todos los stats porque es su suma directa.
Las correlaciones entre stats individuales revelan perfiles: un tanque suele tener
alta defensa pero baja velocidad, un velocista sacrifica resistencia.
""")

# ── Distribuciones ────────────────────────────────────────────────────────
with tab2:
    stat_options = dict(zip(STAT_LABELS + ["BST"], STAT_COLS + ["bst"]))
    stat_sel = st.selectbox("Stat a visualizar", list(stat_options.keys()), index=6)
    col_sel  = stat_options[stat_sel]

    fig2 = px.histogram(
        df,
        x=col_sel,
        color="categoria",
        color_discrete_map={
            "Normal": "#4a9eff", "Legendario": "#ffd700", "Mitico": "#ff6ec7"
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

    # Contexto: mediana por categoría
    medians = df.groupby("categoria")[col_sel].median()
    parts = [
        f"**{cat}** = {medians[cat]:.0f}"
        for cat in ["Normal", "Legendario", "Mitico"]
        if cat in medians
    ]
    if parts:
        st.caption(f"Mediana de {stat_sel} por categoría: " + " · ".join(parts))

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
    df_g["grupo"] = df_g["categoria"].replace({"Legendario": "Especial", "Mitico": "Especial"})

    fig3 = px.violin(
        df_g, y=col_g, x="grupo", color="grupo",
        color_discrete_map={"Normal": "#4a9eff", "Especial": "#ffd700"},
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

        normal = df_g[df_g["grupo"] == "Normal"][col_g].dropna()
        espec  = df_g[df_g["grupo"] == "Especial"][col_g].dropna()

        st.info(
            "**Test Mann-Whitney U** — no asume normalidad en los datos. "
            "Contrasta si los Pokémon especiales tienen, en general, mayor "
            f"*{stat_g}* que los normales. "
            "Un p-valor < 0.05 indica que la diferencia observada es poco probable que sea aleatoria."
        )

        stat_val, pvalue = sp_stats.mannwhitneyu(espec, normal, alternative="greater")

        col_u, col_p = st.columns(2)
        col_u.metric("Estadístico U", f"{stat_val:,.0f}")
        col_p.metric("p-valor", f"{pvalue:.2e}")

        if pvalue < 0.001:
            st.success(
                f"p = {pvalue:.2e} — diferencia estadísticamente muy significativa. "
                f"Los Pokémon especiales tienen {stat_g} significativamente mayor que los normales."
            )
        elif pvalue < 0.05:
            st.info(f"p = {pvalue:.2e} — diferencia significativa (p < 0.05).")
        else:
            st.warning(
                f"p = {pvalue:.2e} — sin evidencia estadística de diferencia para {stat_g}."
            )

        efecto = espec.median() - normal.median()
        sign   = "+" if efecto >= 0 else ""
        st.caption(
            f"💡 Diferencia de medianas: **{sign}{efecto:.0f} puntos** (especiales − normales) · "
            f"Mediana especiales = {espec.median():.0f} · normales = {normal.median():.0f}"
        )

    except ImportError:
        st.info("Instala scikit-learn/scipy para el test estadístico: `pip install scikit-learn`")

# ── BST por tipo ──────────────────────────────────────────────────────────
with tab4:
    st.subheader("BST por tipo primario")
    st.markdown(
        "El **BST** (Base Stat Total) es la suma de los 6 stats base de un Pokémon: "
        "HP, Ataque, Defensa, Atq. Esp., Def. Esp. y Velocidad. "
        "Es el indicador más directo del poder general de un Pokémon — "
        "a mayor BST, más flexible y potente en combate. "
        "El boxplot muestra cómo se distribuye el BST dentro de cada tipo primario."
    )

    order = (
        df.groupby("type1")["bst"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    tick_labels = [TYPE_ES.get(t, t) for t in order]

    fig4 = px.box(
        df, x="type1", y="bst",
        color="type1",
        category_orders={"type1": order},
        color_discrete_map=TYPE_COLORS,
        hover_name="name",
        labels={"type1": "Tipo", "bst": "BST", "name": "Pokémon"},
        title="Distribución de BST por tipo primario (hover = nombre del Pokémon)",
        template="plotly_dark",
    )
    fig4.update_layout(
        showlegend=False,
        height=500,
        xaxis=dict(title="", ticktext=tick_labels, tickvals=order),
        margin=dict(b=80),
    )
    st.plotly_chart(fig4, use_container_width=True)

    medians_type = df.groupby("type1")["bst"].median()
    top_type = TYPE_ES.get(medians_type.idxmax(), medians_type.idxmax())
    bot_type = TYPE_ES.get(medians_type.idxmin(), medians_type.idxmin())
    st.caption(
        f"💡 Tipo con BST mediano más alto: **{top_type}** ({medians_type.max():.0f}) · "
        f"más bajo: **{bot_type}** ({medians_type.min():.0f}) — "
        "Los tipos Dragon y Acero tienden a tener Pokémon pseudo-legendarios y legendarios, "
        "lo que eleva su mediana."
    )

    st.divider()

    # ── Ranking top 10 por BST ─────────────────────────────────────────────
    col_top, col_bot = st.columns(2)

    with col_top:
        st.markdown("**Top 10 — mayor BST**")
        top10 = (
            df.nlargest(10, "bst")[["name", "type1", "type2", "bst", "categoria"]]
            .copy()
        )
        top10["Pokémon"]   = top10["name"].apply(pokemon_display_name)
        top10["Tipo"]      = top10["type1"].map(lambda t: TYPE_ES.get(t, t))
        top10["Categoría"] = top10["categoria"]
        st.dataframe(
            top10[["Pokémon", "Tipo", "bst", "Categoría"]]
            .rename(columns={"bst": "BST"})
            .set_index("Pokémon"),
            use_container_width=True,
        )

    with col_bot:
        st.markdown("**Top 10 — menor BST**")
        bot10 = (
            df.nsmallest(10, "bst")[["name", "type1", "bst", "gen"]]
            .copy()
        )
        bot10["Pokémon"] = bot10["name"].apply(pokemon_display_name)
        bot10["Tipo"]    = bot10["type1"].map(lambda t: TYPE_ES.get(t, t))
        bot10["Gen"]     = bot10["gen"]
        st.dataframe(
            bot10[["Pokémon", "Tipo", "bst", "Gen"]]
            .rename(columns={"bst": "BST"})
            .set_index("Pokémon"),
            use_container_width=True,
        )

    st.divider()

    # ── Tabla completa por tipo ────────────────────────────────────────────
    st.markdown("**Estadísticas de BST por tipo primario**")
    tbl_stats = (
        df.groupby("type1")["bst"]
        .agg(Mediana="median", Media="mean", Máximo="max", N="count")
        .sort_values("Mediana", ascending=False)
        .reset_index()
        .rename(columns={"type1": "Tipo"})
    )
    tbl_stats["Tipo"]    = tbl_stats["Tipo"].map(lambda t: TYPE_ES.get(t, t))
    tbl_stats["Mediana"] = tbl_stats["Mediana"].round(0).astype(int)
    tbl_stats["Media"]   = tbl_stats["Media"].round(1)
    tbl_stats["Máximo"]  = tbl_stats["Máximo"].astype(int)
    st.dataframe(tbl_stats.set_index("Tipo"), use_container_width=True)
    st.caption(
        "La mediana es más robusta que la media cuando hay valores extremos "
        "(legendarios con BST muy alto pueden sesgar la media hacia arriba)."
    )
