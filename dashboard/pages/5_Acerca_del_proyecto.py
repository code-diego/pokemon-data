"""
acerca del proyecto — stack técnico, volumen de datos y pipeline.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from data import IS_SAMPLE_DB

st.set_page_config(page_title="Acerca del proyecto", layout="wide")
st.title("Acerca del proyecto")

st.markdown(
    """
    **pokemon-data** es un pipeline ETL + dashboard de análisis interactivo construido
    sobre los datos de [PokéAPI](https://pokeapi.co) — la API pública más completa de
    Pokémon. Descarga y normaliza información de los **1 025 Pokémon** del Pokédex
    nacional, los almacena en SQLite, y los expone a través de este dashboard multipágina
    y una serie de notebooks de análisis exploratorio y machine learning.
    """
)

if IS_SAMPLE_DB:
    st.caption("Modo demostración: datos de generaciones I–III.")

st.divider()

# ── Stack técnico ─────────────────────────────────────────────────────────
st.subheader("Stack técnico")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Pipeline de datos**")
    st.markdown(
        """
| Tecnología | Rol |
|------------|-----|
| `aiohttp` | Descarga asíncrona de ~3 700 endpoints de PokéAPI |
| `tqdm` | Barra de progreso durante el ETL |
| `SQLite` | Base de datos relacional con 9 tablas normalizadas |
| `pymongo` *(opcional)* | Backend NoSQL documental alternativo |
        """
    )

with col2:
    st.markdown("**Análisis y visualización**")
    st.markdown(
        """
| Tecnología | Rol |
|------------|-----|
| `pandas` | Transformación y análisis de datos |
| `plotly` | Gráficas interactivas (hover, zoom) en notebooks y dashboard |
| `streamlit` | Dashboard multipágina con estado y caché |
| `scikit-learn` | K-means, PCA, StandardScaler — clustering ML |
| `scipy` | Test estadístico Mann-Whitney U |
        """
    )

st.divider()

# ── Volumen de datos ──────────────────────────────────────────────────────
st.subheader("Volumen de datos")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Pokémon (formas base)", "1 025")
m2.metric("Formas alternativas", "325")
m3.metric("Movimientos", "937")
m4.metric("Habilidades", "371")
m5.metric("Tipos", "18")

st.divider()

# ── Pipeline ──────────────────────────────────────────────────────────────
st.subheader("Pipeline de datos")

st.code(
    """
PokéAPI
  └─→ fetch.py  (aiohttp, ~3 700 requests asíncronos)
        └─→ data/raw/          ← caché JSON local
              ├── pokemon/     (1 350 archivos)
              ├── species/     (1 025 archivos)
              ├── types/       (   21 archivos)
              ├── abilities/   (  371 archivos)
              └── moves/       (  937 archivos)

data/raw/
  └─→ build_db.py  (normalización + 9 tablas SQLite)
        └─→ data/pokemon.db
              ├── pokemon          (id, nombre, altura, peso, sprite…)
              ├── species          (generación, captura, felicidad…)
              ├── pokemon_types    (tipo primario / secundario)
              ├── pokemon_stats    (HP, Ataque, Defensa… × Pokémon)
              ├── pokemon_abilities
              ├── pokemon_moves
              ├── types            (efectividades 18×18)
              ├── abilities
              └── moves

data/pokemon.db
  ├─→ dashboard/  (Streamlit multipágina)
  └─→ notebooks/  (Plotly EDA + clustering K-means + MongoDB)
""",
    language="text",
)

st.divider()

# ── Páginas del dashboard ─────────────────────────────────────────────────
st.subheader("Páginas del dashboard")

st.markdown(
    """
| Página | Qué muestra |
|--------|-------------|
| **Vista general** | KPIs, distribución de tipos, scatter peso/altura, tabla filtrable |
| **Comparador** | Sprites lado a lado, radar de stats superpuesto, BST comparado |
| **Pokédex** | Ficha individual: sprite, tipos, stats, debilidades/resistencias |
| **Análisis estadístico** | Correlaciones, distribuciones, Mann-Whitney U, BST por tipo |
| **Cobertura de tipos** | Calculadora defensiva y ofensiva de cobertura de tipos |
| **Acerca del proyecto** | Esta página |
    """
)

st.divider()

# ── Repositorio ───────────────────────────────────────────────────────────
st.subheader("Repositorio")
st.markdown(
    "El código fuente está disponible en GitHub. "
    "Para ejecutar el proyecto completo (ETL + dashboard):"
)
st.code(
    """git clone <URL-del-repo>
cd pokemon-data
pip install -r requirements.txt
python scripts/fetch.py        # ~10 min primera vez
python scripts/build_db.py
streamlit run dashboard/App.py""",
    language="bash",
)
