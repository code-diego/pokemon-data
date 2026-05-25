"""
Módulo compartido: constantes, carga de datos cacheada y helpers.
Importado por app.py y todas las páginas en dashboard/pages/.
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Constantes de tema ────────────────────────────────────────────────────
TYPE_COLORS = {
    "normal":   "#A8A77A", "fire":    "#EE8130", "water":    "#6390F0",
    "electric": "#F7D02C", "grass":   "#7AC74C", "ice":      "#96D9D6",
    "fighting": "#C22E28", "poison":  "#A33EA1", "ground":   "#E2BF65",
    "flying":   "#A98FF3", "psychic": "#F95587", "bug":      "#A6B91A",
    "rock":     "#B6A136", "ghost":   "#735797", "dragon":   "#6F35FC",
    "dark":     "#705746", "steel":   "#B7B7CE", "fairy":    "#D685AD",
}
TYPE_ES = {
    "normal":   "Normal",   "fire":    "Fuego",    "water":   "Agua",
    "electric": "Electrico","grass":   "Planta",   "ice":     "Hielo",
    "fighting": "Lucha",    "poison":  "Veneno",   "ground":  "Tierra",
    "flying":   "Volador",  "psychic": "Psiquico", "bug":     "Bicho",
    "rock":     "Roca",     "ghost":   "Fantasma", "dragon":  "Dragon",
    "dark":     "Siniestro","steel":   "Acero",    "fairy":   "Hada",
}
GEN_MAP = {
    "generation-i":   "Gen I",    "generation-ii":  "Gen II",
    "generation-iii": "Gen III",  "generation-iv":  "Gen IV",
    "generation-v":   "Gen V",    "generation-vi":  "Gen VI",
    "generation-vii": "Gen VII",  "generation-viii":"Gen VIII",
    "generation-ix":  "Gen IX",
}
GEN_ORDER   = ["Gen I","Gen II","Gen III","Gen IV","Gen V",
               "Gen VI","Gen VII","Gen VIII","Gen IX"]
STAT_COLS   = ["hp","attack","defense","special-attack","special-defense","speed"]
STAT_LABELS = ["HP","Ataque","Defensa","Atq. Esp.","Def. Esp.","Velocidad"]


# ── Utilidades de presentación ────────────────────────────────────────────
def type_badge_html(type_en: str, size: str = "13px") -> str:
    """Span HTML con badge coloreado del tipo (para st.markdown unsafe_allow_html)."""
    color = TYPE_COLORS.get(type_en, "#888")
    label = TYPE_ES.get(type_en, type_en.capitalize())
    return (
        f'<span style="background:{color};color:#fff;'
        f'padding:3px 10px;border-radius:12px;font-size:{size};'
        f'font-weight:600;margin:2px;display:inline-block">{label}</span>'
    )


# ── Localización de la BD ─────────────────────────────────────────────────
def find_db() -> Path | None:
    for p in [Path.cwd(), *Path.cwd().parents]:
        candidate = p / "data" / "pokemon.db"
        if candidate.exists():
            return candidate
    return None


# ── Carga principal ───────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    """Carga y une todas las tablas. @st.cache_data evita releer en cada interacción."""
    db = find_db()
    if db is None:
        st.error("No se encontró data/pokemon.db. Ejecuta: python scripts/build_db.py")
        st.stop()

    con = sqlite3.connect(db)
    pokemon  = pd.read_sql("SELECT * FROM pokemon", con)
    stats_l  = pd.read_sql("SELECT * FROM pokemon_stats", con)
    species  = pd.read_sql("SELECT * FROM species", con)
    tipos_db = pd.read_sql("SELECT * FROM pokemon_types", con)
    con.close()

    stats = (stats_l
             .pivot(index="pokemon_id", columns="stat_name", values="base_value")
             .reset_index())
    stats.columns.name = None

    tipo1 = (tipos_db[tipos_db["slot"]==1][["pokemon_id","type_name"]]
             .rename(columns={"type_name":"type1"}))
    tipo2 = (tipos_db[tipos_db["slot"]==2][["pokemon_id","type_name"]]
             .rename(columns={"type_name":"type2"}))

    df = (pokemon
          .merge(stats,  left_on="id", right_on="pokemon_id", how="left").drop(columns="pokemon_id")
          .merge(tipo1,  left_on="id", right_on="pokemon_id", how="left").drop(columns="pokemon_id")
          .merge(tipo2,  left_on="id", right_on="pokemon_id", how="left").drop(columns="pokemon_id")
          .merge(species[["id","is_legendary","is_mythical","generation",
                           "capture_rate","base_happiness"]], on="id", how="left"))

    df["bst"]      = df[STAT_COLS].sum(axis=1)
    df["categoria"] = "Normal"
    df.loc[df["is_legendary"]==1, "categoria"] = "Legendario"
    df.loc[df["is_mythical"] ==1, "categoria"] = "Mitico"
    df["dual_tipo"] = df["type2"].notna()
    df["height_m"]  = df["height"] / 10
    df["weight_kg"] = df["weight"] / 10
    df["gen"]       = df["generation"].map(GEN_MAP).fillna(df["generation"])
    df["is_form"]   = df["id"] >= 10000

    return df


# ── Type chart (tabla de efectividad) ────────────────────────────────────
@st.cache_data
def load_type_chart() -> pd.DataFrame:
    """
    Devuelve una DataFrame 18×18 de multiplicadores defensivos.
    chart.loc[defensor, atacante] = multiplicador (0 / 0.5 / 1 / 2).
    Para Pokémon dual-tipo, usa defensive_profile() que multiplica ambas filas.
    """
    db = find_db()
    if db is None:
        return pd.DataFrame()

    con      = sqlite3.connect(db)
    types_df = pd.read_sql("SELECT * FROM types", con)
    con.close()

    all_types = sorted(TYPE_COLORS.keys())
    chart     = pd.DataFrame(1.0, index=all_types, columns=all_types)

    def parse(cell):
        return [t.strip() for t in str(cell).split(",") if t.strip() and t.strip() != "None"]

    for _, row in types_df.iterrows():
        defender = row["name"]
        if defender not in all_types:
            continue
        for atk in parse(row["double_damage_from"]):
            if atk in all_types:
                chart.loc[defender, atk] *= 2.0
        for atk in parse(row["half_damage_from"]):
            if atk in all_types:
                chart.loc[defender, atk] *= 0.5
        for atk in parse(row["no_damage_from"]):
            if atk in all_types:
                chart.loc[defender, atk] *= 0.0

    return chart


# ── Formateo de nombres de Pokémon ────────────────────────────────────────
_DISPLAY_NAME_OVERRIDES = {
    "nidoran-f": "Nidoran ♀",
    "nidoran-m": "Nidoran ♂",
}

def pokemon_display_name(name: str) -> str:
    """Convierte nombre interno (lowercase, guiones) a texto legible para la UI."""
    if name in _DISPLAY_NAME_OVERRIDES:
        return _DISPLAY_NAME_OVERRIDES[name]
    return name.replace("-", " ").title()


def defensive_profile(type1: str, type2: str | None = None) -> dict:
    """
    Calcula el multiplicador de daño recibido para cada tipo atacante.
    Si type2 está presente, multiplica los multiplicadores de ambos tipos.
    Retorna {tipo_atacante_en: multiplicador}.
    """
    chart = load_type_chart()
    if chart.empty or type1 not in chart.index:
        return {}
    mult = chart.loc[type1].copy()
    if type2 and type2 in chart.index:
        mult = mult * chart.loc[type2]
    return mult.to_dict()
