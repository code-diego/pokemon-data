# pokemon-data

Pipeline ETL que descarga todos los datos de [PokéAPI](https://pokeapi.co) y los carga en dos backends:
una base de datos **SQLite** relacional y una colección **MongoDB** con documentos desnormalizados.
Incluye notebooks de análisis con Plotly, un **dashboard Streamlit multipágina** y un módulo de
**machine learning** (clustering K-means).

## Estructura

```
pokemon-data/
├── scripts/
│   ├── fetch.py          # Descarga datos de PokéAPI → data/raw/
│   ├── build_db.py       # Construye pokemon.db (SQLite, 9 tablas relacionadas)
│   └── build_nosql.py    # Construye documentos → data/pokemon_docs.json + MongoDB
├── notebooks/
│   ├── relational.ipynb  # Análisis sobre SQLite (Plotly — hover, zoom)
│   ├── nosql.ipynb       # Consultas sobre MongoDB
│   └── clustering.ipynb  # Clustering K-means + PCA — arquetipos por stats
├── dashboard/
│   ├── app.py            # Página principal — Vista general (filtros, KPIs, gráficas)
│   ├── data.py           # Módulo compartido: carga cacheada, type-chart, helpers
│   ├── ml.py             # Helper ML: cluster_pokemon(), label_archetype()
│   └── pages/
│       ├── 1_Comparador.py          # Radar de stats para 2-6 Pokémon
│       ├── 2_Ficha_individual.py    # Sprite, tipos, stats y debilidades
│       ├── 3_Analisis_estadistico.py# Correlaciones, distribuciones, test Mann-Whitney
│       ├── 4_Cobertura_de_tipos.py  # Calculadora defensiva/ofensiva de tipos
│       └── 5_Clusters_ML.py        # K-means + PCA interactivo
├── docs/
│   └── MONGO_GUIDE.md    # Guía de instalación de MongoDB (Linux/Fedora, Windows, macOS)
├── requirements.txt      # Dependencias del proyecto
└── data/                 # Archivos generados e ignorados por git
    ├── raw/              # Caché JSON descargada por fetch.py
    │   ├── pokemon/      # 1,350 archivos — datos individuales por Pokémon
    │   ├── species/      # 1,025 archivos — especie, generación, color, hábitat
    │   ├── types/        #    21 archivos — relaciones de daño entre tipos
    │   ├── abilities/    #   371 archivos — efectos de habilidades
    │   └── moves/        #   937 archivos — poder, precisión, PP, clase de daño
    ├── pokemon.db        # Base de datos SQLite (build_db.py)
    └── pokemon_docs.json # Respaldo JSON para MongoDB (build_nosql.py)
```

> Los archivos `data/pokemon.db` y `data/pokemon_docs.json` son **generados** y están en `.gitignore`.
> Ejecútalos localmente con los scripts de build.

## Requisitos

```bash
pip install -r requirements.txt
```

| Paquete         | Uso |
|-----------------|-----|
| `aiohttp`       | Descargas asíncronas en `fetch.py` |
| `tqdm`          | Barra de progreso (opcional) |
| `pandas`        | Análisis de datos en los notebooks y dashboard |
| `numpy`         | Cálculos numéricos |
| `plotly`        | Gráficas interactivas (hover, zoom) en notebooks y dashboard |
| `streamlit`     | Dashboard multipágina (`dashboard/`) |
| `scikit-learn`  | K-means, PCA, StandardScaler — clustering ML |
| `matplotlib`    | Legacy (reemplazado por Plotly en los notebooks) |
| `pymongo`       | Conexión con MongoDB |

## Inicio rápido (todo el pipeline en orden)

```bash
# 0. Instalar dependencias
pip install -r requirements.txt

# 1. Descargar los datos de PokéAPI  →  data/raw/   (solo la primera vez, ~minutos)
python scripts/fetch.py

# 2a. Construir la base SQLite  →  data/pokemon.db
python scripts/build_db.py

# 2b. Construir la colección MongoDB  →  data/pokemon_docs.json + MongoDB
podman start mongodb            # arranca MongoDB (ver docs/MONGO_GUIDE.md para instalarlo)
python scripts/build_nosql.py

# 3. Analizar
jupyter notebook notebooks/relational.ipynb   # SQLite — análisis exploratorio
jupyter notebook notebooks/nosql.ipynb        # MongoDB — consultas documentales
jupyter notebook notebooks/clustering.ipynb   # ML — arquetipos por estadísticas

# 4. Dashboard interactivo
streamlit run dashboard/app.py
```

> **Orden de dependencias:** `fetch.py` debe correr **antes** que los `build_*`
> (ellos leen de `data/raw/`). `build_db.py` y `build_nosql.py` son independientes entre sí.
> Los notebooks y el dashboard necesitan que su backend ya esté construido.

A continuación, cada paso en detalle.

## Uso

### 1. Descargar datos

```bash
python scripts/fetch.py
```

Descarga pokémon, especies, tipos, habilidades y movimientos de PokéAPI.
Es **idempotente**: si un archivo JSON ya existe lo salta; puedes reanudar descargas interrumpidas.

### 2a. Base de datos SQLite (relacional)

```bash
python scripts/build_db.py
```

Genera `data/pokemon.db` con 9 tablas relacionadas:

| Tabla               | Contenido |
|---------------------|-----------|
| `pokemon`           | Id, nombre, altura, peso, experiencia base, sprite URL |
| `pokemon_stats`     | HP, ataque, defensa, velocidad, etc. por Pokémon |
| `pokemon_types`     | Tipos por Pokémon (agua, fuego…) |
| `pokemon_abilities` | Habilidades por Pokémon |
| `pokemon_moves`     | Movimientos aprendibles, método y nivel |
| `species`           | Color, forma, hábitat, legendario/mítico, generación |
| `types`             | Relaciones de daño entre tipos |
| `abilities`         | Nombre y efecto en inglés |
| `moves`             | Poder, precisión, PP, tipo y clase de daño |

### 2b. Colección MongoDB (no relacional)

```bash
podman start mongodb        # arranca el contenedor (ver instalación en docs/MONGO_GUIDE.md)
python scripts/build_nosql.py
```

Genera `data/pokemon_docs.json` (respaldo local) y carga la colección
`mongodb://localhost:27017/pokemon_data.pokemon`.
El script es **idempotente** y avisa si MongoDB no está disponible.

> **¿Aún no tienes MongoDB?** Ver **[docs/MONGO_GUIDE.md](docs/MONGO_GUIDE.md)**.

### 3. Notebooks

```bash
jupyter notebook notebooks/relational.ipynb
jupyter notebook notebooks/nosql.ipynb
jupyter notebook notebooks/clustering.ipynb
```

#### `relational.ipynb` — 9 secciones (Plotly — hover, zoom)

| # | Contenido |
|---|-----------|
| 0 | Explorador de tablas — esquema, filas, columnas, nulos, distribuciones |
| 1 | Vista general del dataset (1 025 formas base — excluye 325 formas alt.) |
| 2 | Distribución de tipos primarios |
| 3 | Peso y altura |
| 4 | Stats base (BST) por tipo y generación |
| 5 | Legendarios, míticos y normales |
| 6 | Efectividad de tipos (matriz 18×18 con etiquetas coloreadas) |
| 7 | Combinaciones de tipos — ranking de pares + matriz simétrica dual |
| 8 | Consultas SQL personalizadas |

#### `nosql.ipynb` — 7 secciones

| # | Contenido |
|---|-----------|
| 1 | Conexión a MongoDB |
| 2 | Estructura de un documento (campos disponibles) |
| 3 | Búsqueda por nombre o ID |
| 4 | Legendarios y míticos |
| 5 | Aggregation Pipeline — BST promedio por tipo |
| 6 | Búsqueda por movimiento (`$elemMatch`) |
| 7 | Filtro combinado por tipo y BST mínimo |

#### `clustering.ipynb` — ML (scikit-learn)

| Sección | Contenido |
|---------|-----------|
| 1 | Carga de datos (SQLite) |
| 2 | EDA — distribución de los 6 stats base |
| 3 | Estandarización con `StandardScaler` |
| 4 | Elección de k — curva de codo + silhouette score |
| 5 | Ajuste K-means final (k=5) |
| 6 | Visualización PCA 2D (hover interactivo) |
| 7 | Interpretación de arquetipos — heatmap de perfiles |
| 8 | Validación — ¿los legendarios caen en el mismo cluster? |
| 9 | Conclusiones |

### 4. Dashboard interactivo

```bash
streamlit run dashboard/app.py
```

Se abre en `http://localhost:8501`. El menú lateral muestra todas las páginas:

| Página | Descripción |
|--------|-------------|
| **Vista general** | Filtros (generación, tipo, categoría), KPIs, distribución de tipos, scatter peso/altura, BST por generación, tabla |
| **Comparador** | Selecciona 2–6 Pokémon — radar de stats superpuesto + tabla comparativa |
| **Ficha individual** | Sprite, badges de tipo, barras de stats, debilidades/resistencias calculadas (×4/×2/×½/×¼/×0) |
| **Análisis estadístico** | Correlaciones entre stats, distribuciones por categoría, test Mann-Whitney (legendarios vs normales) |
| **Cobertura de tipos** | Modo defensivo (qué te golpea y cómo) · Modo ofensivo (qué tipos cubre tu equipo) |
| **Clusters ML** | K-means interactivo (slider de k), PCA 2D, perfil de arquetipos, curva de codo |

## Machine Learning

`notebooks/clustering.ipynb` documenta el workflow completo de aprendizaje no supervisado:

```
datos (SQLite) → StandardScaler → elección de k (codo + silhouette)
  → KMeans(k=5) → PCA 2D → arquetipos → validación con legendarios
```

Los clusters identifican arquetipos estadísticos coherentes sin etiquetas previas
(tanques, velocistas, atacantes especiales, Pokémon poderosos, débiles de inicio).
La validación comprueba que los legendarios se concentran en el cluster de BST alto
aunque el modelo nunca recibió esa información.

El helper `dashboard/ml.py` expone `cluster_pokemon()` y `label_archetype()`, reutilizados
por la página interactiva `dashboard/pages/5_Clusters_ML.py`.

## ¿Cuándo usar cada backend?

| | SQLite (`relational.ipynb`) | MongoDB (`nosql.ipynb`) |
|---|---|---|
| Modelo | 9 tablas relacionadas | 1 documento por Pokémon |
| Consultar un Pokémon | JOIN de 5+ tablas | `find_one({"name": "..."})` |
| Filtros en arrays | Subconsulta + JOIN | `$elemMatch` directo |
| Ideal para | Estadísticas, ML, análisis exploratorio | APIs, recuperación rápida, estructura flexible |

## Variable de entorno

Si MongoDB no corre en `localhost:27017`:

```bash
MONGO_URI="mongodb://mi-servidor:27017" python scripts/build_nosql.py
```

## Posibles mejoras

- **Evoluciones** — añadir `evolution-chain` de PokéAPI para analizar cadenas evolutivas.
- **Texto en español** — efectos y descripciones se guardan solo en inglés; añadir multilenguaje.
- **Tests** — pruebas unitarias para los loaders con una muestra pequeña de JSON fijos.
- **CI/CD** — GitHub Actions para ejecutar tests y lint en cada push.
- **Despliegue** — publicar el dashboard en Streamlit Community Cloud con una BD de muestra versionada.
- **Actualización incremental** — `build_db.py` reconstruye la BD completa; se puede hacer incremental.
- **Docker Compose** — levantar MongoDB en contenedor sin instalación local (ver `docs/MONGO_GUIDE.md`).
