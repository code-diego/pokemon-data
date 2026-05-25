# pokemon-data

Pipeline ETL que descarga todos los datos de [PokéAPI](https://pokeapi.co) y los carga en
SQLite. Incluye un **dashboard Streamlit multipágina** interactivo, notebooks de análisis
exploratorio con Plotly y un workflow de **machine learning** (clustering K-means).

## Página principal (Dashboard)

```bash
# 1ra vez: instalar, descargar y construir la base de datos
pip install -r requirements.txt
python scripts/fetch.py       
python scripts/build_db.py   

# Muestra la pagina (dashboard)
streamlit run dashboard/App.py
```

Se abre en `http://localhost:8501`. Todas las páginas están en el menú lateral:

| Página | Descripción |
|--------|-------------|
| **Vista general** | Filtros por generación, tipo y categoría — KPIs, distribución de tipos, scatter peso/altura, BST por generación, tabla filtrada |
| **Comparador** | Selecciona 2–6 Pokémon: sprites lado a lado, radar de stats superpuesto, tabla comparativa con máximos resaltados |
| **Pokédex** | Busca cualquier Pokémon: sprite, número, tipos, métricas (BST, captura, felicidad…), stats con barra y debilidades/resistencias agrupadas (×4 / ×2 / ×½ / ×¼ / ×0) |
| **Análisis estadístico** | Mapa de calor de correlaciones, distribuciones por categoría, violín + test Mann-Whitney (legendarios vs normales) |
| **Cobertura de tipos** | Modo defensivo (¿qué te golpea y cómo?) · Modo ofensivo (¿qué tipos cubre tu equipo?) |


## Estructura

```
pokemon-data/
├── scripts/
│   ├── fetch.py          # descarga datos de PokéAPI → data/raw/
│   ├── build_db.py       # construye pokemon.db (SQLite, 9 tablas relacionadas)
│   └── build_nosql.py    # construye json → data/pokemon_docs.json (MongoDB)
├── notebooks/
│   ├── relational.ipynb  # análisis exploratorio en SQLite (Plotly — hover, zoom)
│   ├── clustering.ipynb  # clustering K-means + PCA — en progreso *
│   └── nosql.ipynb       # consultas en MongoDB
├── dashboard/
│   ├── app.py            # página principal —  (filtros, KPIs, gráficas)
│   ├── data.py           # módulo compartido: carga cacheada, type-chart, helpers
│   └── pages/
│       ├── 1_Comparador.py           # stats para 2-6 Pokémon
│       ├── 2_Pokedex.py             
│       ├── 3_Analisis_estadistico.py # test Mann-Whitney
│       └── 4_Cobertura_de_tipos.py   # calculadora defensiva/ofensiva de tipos
├── docs/
│   └── MONGO_GUIDE.md    # guía de instalación de MongoDB 
├── requirements.txt
└── data/                 # archivos generados —  .gitignore
    ├── raw/              # caché JSON por fetch.py
    │   ├── pokemon/      # 1,350 archivos 
    │   ├── species/      # 1,025 archivos 
    │   ├── types/        #    21 archivos 
    │   ├── abilities/    #   371 archivos 
    │   └── moves/        #   937 archivos
    ├── pokemon.db        # Base de datos SQLite (build_db.py)
    └── pokemon_docs.json # Respaldo JSON para MongoDB (build_nosql.py)
```

## Requisitos

```bash
pip install -r requirements.txt
```

| Paquete        | Uso |
|----------------|-----|
| `aiohttp`      | Descargas asíncronas en `fetch.py` |
| `tqdm`         | Barra de progreso en `fetch.py` |
| `pandas`       | Análisis de datos en notebooks y dashboard |
| `numpy`        | Cálculos numéricos |
| `plotly`       | Gráficas interactivas (hover, zoom) en notebooks y dashboard |
| `streamlit`    | Dashboard multipágina |
| `scikit-learn` | K-means, PCA, StandardScaler — clustering ML (arrastra scipy) |
| `pymongo`      | Conexión con MongoDB *(solo para el backend NoSQL opcional)* |

---

## Notebooks de análisis

```bash
jupyter notebook notebooks/relational.ipynb
jupyter notebook notebooks/clustering.ipynb
```

### `relational.ipynb` — análisis exploratorio (SQLite · Plotly)

Requiere `data/pokemon.db` (`build_db.py`).

| Sección | Contenido |
|---------|-----------|
| 0 | Explorador de tablas — esquema, filas, nulos, distribuciones |
| 1 | Vista general: 1 025 formas base (excluye 325 formas alternativas) |
| 2 | Distribución de tipos primarios |
| 3 | Peso y altura |
| 4 | Stats base (BST) por tipo y generación |
| 5 | Legendarios, míticos y normales |
| 6 | Efectividad de tipos — matriz 18×18 con etiquetas coloreadas |
| 7 | Combinaciones de tipos — ranking de pares + matriz simétrica |
| 8 | Consultas SQL personalizadas |

### `clustering.ipynb` — Machine Learning (scikit-learn)

Requiere `data/pokemon.db` (`build_db.py`).

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

### Machine Learning

```
datos (SQLite) → StandardScaler → elección de k (codo + silhouette)
  → KMeans(k=5) → PCA 2D → arquetipos → validación con legendarios
```

Los clusters identifican arquetipos estadísticos sin etiquetas previas (tanques, velocistas,
atacantes especiales, Pokémon poderosos, débiles de inicio). La validación comprueba que los
legendarios se concentran en el cluster de BST alto, aunque el modelo no recibió esa información.

---

## MongoDB (backend NoSQL)

El backend MongoDB es **opcional** — el dashboard y los notebooks de análisis solo necesitan SQLite.

### Configuración

```bash
podman start mongodb            # arranca el contenedor (ver docs/MONGO_GUIDE.md)
python scripts/build_nosql.py   # genera data/pokemon_docs.json + carga MongoDB
```

> **¿Aún no tienes MongoDB?** Ver **[docs/MONGO_GUIDE.md](docs/MONGO_GUIDE.md)**.

### `nosql.ipynb` — consultas documentales

Requiere MongoDB corriendo y la colección cargada (`build_nosql.py`).

| Sección | Contenido |
|---------|-----------|
| 1 | Conexión a MongoDB |
| 2 | Estructura de un documento |
| 3 | Búsqueda por nombre o ID |
| 4 | Legendarios y míticos |
| 5 | Aggregation Pipeline — BST promedio por tipo |
| 6 | Búsqueda por movimiento (`$elemMatch`) |
| 7 | Filtro combinado por tipo y BST mínimo |

### ¿Cuándo usar cada backend?

|  | SQLite | MongoDB |
|--|--------|---------|
| Modelo | 9 tablas relacionadas | 1 documento por Pokémon |
| Consultar un Pokémon | JOIN de 5+ tablas | `find_one({"name": "..."})` |
| Filtros en arrays | Subconsulta + JOIN | `$elemMatch` directo |
| Ideal para | Estadísticas, ML, análisis exploratorio | APIs, recuperación rápida, esquema flexible |

### Variable de entorno

Si MongoDB no corre en `localhost:27017`:

```bash
MONGO_URI="mongodb://mi-servidor:27017" python scripts/build_nosql.py
```

---

## Posibles mejoras

- **Evoluciones** — añadir `evolution-chain` de PokéAPI para analizar cadenas evolutivas.
- **Tests** — pruebas unitarias para los loaders con una muestra pequeña de JSON fijos.
- **CI/CD** — GitHub Actions para ejecutar tests y lint en cada push.
- **Despliegue** — publicar el dashboard en Streamlit Community Cloud con una BD de muestra versionada.
- **Clusters en el dashboard** — página interactiva de K-means una vez validado el modelo en el notebook.
- **Actualización incremental** — `build_db.py` reconstruye la BD completa; se puede hacer incremental.
