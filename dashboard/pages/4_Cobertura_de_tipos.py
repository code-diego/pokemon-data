"""
Calculadora de cobertura/efectividad de tipos.
Modo defensivo: qué te golpea y cómo.
Modo ofensivo: qué cubres con tu equipo de tipos.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from data import (
    load_type_chart, defensive_profile,
    TYPE_COLORS, TYPE_ES, type_badge_html,
)

st.set_page_config(page_title="Cobertura de Tipos", layout="wide")
st.title("Cobertura y Efectividad de Tipos")


def _inject_type_button_css() -> None:
    css = []
    for t_en, color in TYPE_COLORS.items():
        t_es = TYPE_ES.get(t_en, t_en)
        css.append(
            f'button[aria-label="{t_es}"][data-testid="baseButton-secondary"]'
            f'{{border:2px solid {color}!important;color:{color}!important;}}'
        )
        css.append(
            f'button[aria-label="{t_es}"][data-testid="baseButton-primary"]'
            f'{{background:{color}!important;border-color:{color}!important;color:#fff!important;}}'
        )
    st.markdown(f"<style>{''.join(css)}</style>", unsafe_allow_html=True)


_inject_type_button_css()

# ── Estado inicial ────────────────────────────────────────────────────────
if "cob_def" not in st.session_state:
    st.session_state.cob_def = ["normal"]
if "cob_off" not in st.session_state:
    st.session_state.cob_off = ["water", "fire", "grass"]

all_types = sorted(TYPE_COLORS.keys())
type_rows  = [all_types[i:i+6] for i in range(0, 18, 6)]


def _toggle_def(t: str) -> None:
    cur = list(st.session_state.cob_def)
    if t in cur:
        new = [x for x in cur if x != t]
        if new:  # siempre mantener al menos 1 tipo
            st.session_state.cob_def = new
    else:
        if len(cur) < 2:
            st.session_state.cob_def = cur + [t]
        else:
            st.session_state.cob_def = [cur[0], t]  # reemplaza el 2.º tipo


def _toggle_off(t: str) -> None:
    cur = list(st.session_state.cob_off)
    if t in cur:
        st.session_state.cob_off = [x for x in cur if x != t]
    elif len(cur) < 4:
        st.session_state.cob_off = cur + [t]


def _type_grid(prefix: str, selected: list) -> None:
    """Renderiza una cuadrícula 3×6 de botones de tipo."""
    for row_types in type_rows:
        cols = st.columns(6)
        for col, t in zip(cols, row_types):
            with col:
                is_sel = t in selected
                if st.button(
                    TYPE_ES.get(t, t),
                    key=f"{prefix}_{t}",
                    type="primary" if is_sel else "secondary",
                    use_container_width=True,
                ):
                    if prefix == "def":
                        _toggle_def(t)
                    else:
                        _toggle_off(t)
                    st.rerun()


# ── Tabs modo ─────────────────────────────────────────────────────────────
tab_def, tab_off = st.tabs(["🛡️ Defensivo — ¿qué me golpea?", "⚔️ Ofensivo — ¿qué cubro?"])

# ── Modo defensivo ────────────────────────────────────────────────────────
with tab_def:
    st.subheader("Perfil defensivo")
    st.caption(
        "Selecciona 1 o 2 tipos. "
        "Click en un tipo seleccionado para quitarlo (mínimo 1)."
    )

    _type_grid("def", st.session_state.cob_def)

    # Mostrar tipos activos como badges
    st.write("")
    sel_html = "".join(type_badge_html(t, "15px") + "&nbsp;" for t in st.session_state.cob_def)
    st.markdown(f"**Combinación activa:** {sel_html}", unsafe_allow_html=True)
    st.divider()

    t1 = st.session_state.cob_def[0]
    t2 = st.session_state.cob_def[1] if len(st.session_state.cob_def) > 1 else None
    profile = defensive_profile(t1, t2)

    buckets = {4: [], 2: [], 1: [], 0.5: [], 0.25: [], 0: []}
    for atk, mult in profile.items():
        rounded = round(mult, 4)
        for key in buckets:
            if abs(rounded - key) < 0.01:
                buckets[key].append(atk)
                break

    for key in [4, 2, 0.5, 0.25, 0]:
        types = buckets[key]
        if not types:
            continue
        labels_map = {
            4: "×4  Muy débil", 2: "×2  Débil",
            0.5: "×½  Resiste", 0.25: "×¼  Muy resistente", 0: "×0  Inmune",
        }
        st.markdown(f"**{labels_map[key]}**")
        st.markdown(" ".join(type_badge_html(t) for t in sorted(types)),
                    unsafe_allow_html=True)
        st.write("")

    neutral = buckets[1]
    if neutral:
        with st.expander(f"Neutral (×1) — {len(neutral)} tipos"):
            st.markdown(" ".join(type_badge_html(t) for t in sorted(neutral)),
                        unsafe_allow_html=True)

# ── Modo ofensivo ─────────────────────────────────────────────────────────
with tab_off:
    st.subheader("Cobertura ofensiva")
    n_sel = len(st.session_state.cob_off)
    st.caption(
        f"Selecciona hasta 4 tipos de ataque ({n_sel}/4 seleccionados). "
        "Se muestra qué tipos defensivos quedan cubiertos (≥×2) y cuáles no."
    )

    _type_grid("off", st.session_state.cob_off)

    team = st.session_state.cob_off
    if not team:
        st.info("Selecciona al menos un tipo de ataque.")
        st.stop()

    # Mostrar tipos activos
    st.write("")
    off_html = "".join(type_badge_html(t, "15px") + "&nbsp;" for t in team)
    st.markdown(f"**Equipo activo:** {off_html}", unsafe_allow_html=True)
    st.divider()

    chart = load_type_chart()
    if chart.empty:
        st.error("No se pudo cargar la tabla de tipos.")
        st.stop()

    results = {
        defender: max(chart.loc[defender, t] for t in team if t in chart.columns)
        for defender in all_types
    }

    covered_2x  = [d for d, m in results.items() if m >= 2]
    not_covered = [d for d, m in results.items() if 0 < m < 2]
    immune      = [d for d, m in results.items() if m == 0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Tipos cubiertos (≥×2)", len(covered_2x))
    c2.metric("Sin cobertura super-efectiva", len(not_covered))
    c3.metric("Inmunes al equipo", len(immune))

    st.write("")
    if covered_2x:
        st.markdown("**Cubiertos ×2 o más**")
        st.markdown(" ".join(type_badge_html(t) for t in sorted(covered_2x)),
                    unsafe_allow_html=True)
    else:
        st.caption("Ningún tipo cubierto super-efectivamente.")

    if not_covered:
        st.write("")
        st.markdown("**Sin cobertura super-efectiva**")
        st.markdown(" ".join(type_badge_html(t) for t in sorted(not_covered)),
                    unsafe_allow_html=True)
    else:
        st.write("")
        st.caption("Cobertura completa — todos los tipos son alcanzados con ≥×2.")

    if immune:
        st.write("")
        st.markdown("**Inmunes a todo el equipo**")
        st.markdown(" ".join(type_badge_html(t) for t in sorted(immune)),
                    unsafe_allow_html=True)

    with st.expander("Ver tabla completa"):
        rows = []
        for d in sorted(all_types):
            best_t = max(team, key=lambda t: chart.loc[d, t] if t in chart.columns else 0)
            rows.append({
                "Tipo defensor":   TYPE_ES.get(d, d),
                "Mejor cobertura": TYPE_ES.get(best_t, best_t),
                "Multiplicador":   results[d],
            })
        df_tbl = pd.DataFrame(rows).sort_values("Multiplicador", ascending=False)
        st.dataframe(df_tbl.set_index("Tipo defensor"), use_container_width=True)
