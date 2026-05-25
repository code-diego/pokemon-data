"""
Calculadora de cobertura/efectividad de tipos.
Modo defensivo: qué te golpea y cómo.
Modo ofensivo: qué cubres con tu equipo de tipos.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from data import (
    load_type_chart, defensive_profile,
    TYPE_COLORS, TYPE_ES, type_badge_html,
)

st.set_page_config(page_title="Cobertura de Tipos", layout="wide")
st.title("Cobertura y Efectividad de Tipos")

modo = st.radio(
    "Modo",
    ["Defensivo — ¿qué me golpea?", "Ofensivo — ¿qué cubro?"],
    horizontal=True,
)

st.divider()
all_types = sorted(TYPE_COLORS.keys())

# ── Modo defensivo ────────────────────────────────────────────────────────
if modo.startswith("Defensivo"):
    st.subheader("Perfil defensivo")
    st.caption("Elige 1 o 2 tipos y ve qué tipos de ataque te golpean y cómo.")

    col_a, col_b = st.columns(2)
    with col_a:
        t1 = st.selectbox("Tipo primario", all_types,
                          format_func=lambda t: TYPE_ES.get(t, t))
    with col_b:
        t2_opts = ["(ninguno)"] + all_types
        t2_raw  = st.selectbox("Tipo secundario (opcional)", t2_opts,
                               format_func=lambda t: "—" if t == "(ninguno)" else TYPE_ES.get(t, t))
        t2 = None if t2_raw == "(ninguno)" else t2_raw

    st.markdown("**Tipos seleccionados:**")
    badges = type_badge_html(t1, "15px")
    if t2:
        badges += "  " + type_badge_html(t2, "15px")
    st.markdown(badges, unsafe_allow_html=True)
    st.write("")

    profile = defensive_profile(t1, t2)

    buckets = {4: [], 2: [], 1: [], 0.5: [], 0.25: [], 0: []}
    for atk, mult in profile.items():
        rounded = round(mult, 4)
        for key in buckets:
            if abs(rounded - key) < 0.01:
                buckets[key].append(atk)
                break

    bucket_meta = {
        4:    ("Muy débil",      "×4",  "#FF0000"),
        2:    ("Débil",          "×2",  "#FF7700"),
        1:    ("Neutral",        "×1",  "#888888"),
        0.5:  ("Resiste",        "×½",  "#0088FF"),
        0.25: ("Muy resistente", "×¼",  "#0044BB"),
        0:    ("Inmune",         "×0",  "#222222"),
    }

    for key in [4, 2, 0.5, 0.25, 0]:
        types = buckets[key]
        if not types:
            continue
        label, mult_str, _ = bucket_meta[key]
        st.markdown(f"**{mult_str}  {label}**")
        st.markdown(" ".join(type_badge_html(t) for t in sorted(types)),
                    unsafe_allow_html=True)
        st.write("")

    neutral = buckets[1]
    if neutral:
        with st.expander(f"Neutral (×1) — {len(neutral)} tipos"):
            st.markdown(" ".join(type_badge_html(t) for t in sorted(neutral)),
                        unsafe_allow_html=True)

# ── Modo ofensivo ─────────────────────────────────────────────────────────
else:
    st.subheader("Cobertura ofensiva")
    st.caption(
        "Elige hasta 4 tipos de movimientos de tu equipo. "
        "Se muestra qué tipos defensivos quedan cubiertos (≥×2) y cuáles no."
    )

    team = st.multiselect(
        "Tipos de ataque de tu equipo",
        all_types,
        default=["water", "fire", "grass"],
        format_func=lambda t: TYPE_ES.get(t, t),
        max_selections=4,
    )

    if not team:
        st.info("Selecciona al menos un tipo de ataque.")
        st.stop()

    chart = load_type_chart()
    if chart.empty:
        st.error("No se pudo cargar la tabla de tipos.")
        st.stop()

    # Para cada tipo defensor, multiplier máximo que ofrece el equipo
    results = {}
    for defender in all_types:
        best = max(chart.loc[defender, t] for t in team if t in chart.columns)
        results[defender] = best

    covered_2x   = [d for d, m in results.items() if m >= 2]
    covered_half = [d for d, m in results.items() if m == 0.5]
    not_covered  = [d for d, m in results.items() if m < 2 and m > 0]
    immune       = [d for d, m in results.items() if m == 0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Tipos cubiertos (≥×2)", len(covered_2x))
    c2.metric("Sin cobertura (<×2)", len(not_covered))
    c3.metric("Inmunes a todo el equipo", len(immune))

    st.write("")
    st.markdown("**Cubiertos ×2 o más**")
    if covered_2x:
        st.markdown(" ".join(type_badge_html(t) for t in sorted(covered_2x)),
                    unsafe_allow_html=True)
    else:
        st.caption("Ninguno.")

    st.write("")
    st.markdown("**Sin cobertura super-efectiva**")
    if not_covered:
        st.markdown(" ".join(type_badge_html(t) for t in sorted(not_covered)),
                    unsafe_allow_html=True)
    else:
        st.caption("Cobertura completa.")

    if immune:
        st.write("")
        st.markdown("**Inmunes a todo el equipo**")
        st.markdown(" ".join(type_badge_html(t) for t in sorted(immune)),
                    unsafe_allow_html=True)

    # Tabla detallada
    with st.expander("Ver tabla completa"):
        import pandas as pd
        rows = []
        for d in sorted(all_types):
            best_t = max(team, key=lambda t: chart.loc[d, t] if t in chart.columns else 0)
            best_m = results[d]
            rows.append({
                "Tipo defensor": TYPE_ES.get(d, d),
                "Mejor cobertura": TYPE_ES.get(best_t, best_t),
                "Multiplicador": best_m,
            })
        df_tbl = pd.DataFrame(rows).sort_values("Multiplicador", ascending=False)
        st.dataframe(df_tbl.set_index("Tipo defensor"), use_container_width=True)
