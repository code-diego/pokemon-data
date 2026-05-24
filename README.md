# pokemon-data

Pipeline ETL que descarga todos los datos de [PokéAPI](https://pokeapi.co) y los carga en dos backends:
una base de datos **SQLite** relacional y una colección **MongoDB** con documentos desnormalizados.

## Estructura

```
pokemon-data/
├── scripts/
│   ├── fetch.py          # Descarga datos de PokéAPI → data/raw/
│   ├── build_db.py       # Construye pokemon.db (SQLite, 9 tablas relacionadas)
│   └── build_nosql.py    # Construye documentos → data/pokemon_docs.json + MongoDB
├── notebooks/
│   ├── relational.ipynb  # Análisis sobre SQLite
│   └── nosql.ipynb       # Consultas sobre MongoDB
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

| Paquete      | Uso |
|--------------|-----|
| `aiohttp`    | Descargas asíncronas en `fetch.py` |
| `tqdm`       | Barra de progreso (opcional) |
| `pandas`     | Análisis de datos en los notebooks |
| `matplotlib` | Visualizaciones |
| `numpy`      | Cálculos numéricos |
| `pymongo`    | Conexión con MongoDB |

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
jupyter notebook notebooks/relational.ipynb   # SQLite
jupyter notebook notebooks/nosql.ipynb        # MongoDB
```

> **Orden de dependencias:** `fetch.py` debe correr **antes** que los `build_*`
> (ellos leen de `data/raw/`). `build_db.py` y `build_nosql.py` son independientes entre sí:
> puedes correr uno, el otro, o ambos. Los notebooks necesitan su backend ya construido.

A continuación, cada paso en detalle.

## Uso

### 1. Descargar datos

```bash
python scripts/fetch.py
```

Descarga pokémon, especies, tipos, habilidades y movimientos de PokéAPI.
Durante la descarga muestra el directorio exacto donde se guarda cada recurso:

```
Descargando datos…
  pokemon: 1350 por descargar (0 ya en caché)…
  → guardado en: /home/usuario/pokemon-data/data/raw/pokemon  (1350 archivos nuevos)
  ...
```

Es **idempotente**: si un archivo JSON ya existe lo salta, puedes reanudar descargas interrumpidas.

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

Primero asegúrate de que MongoDB esté corriendo, luego carga los datos:

```bash
podman start mongodb        # arranca el contenedor (ver instalación en docs/MONGO_GUIDE.md)
python scripts/build_nosql.py
```

Genera dos salidas:

- **`data/pokemon_docs.json`** — respaldo JSON local con todos los documentos.
- **`mongodb://localhost:27017/pokemon_data.pokemon`** — colección MongoDB.

Cada documento tiene un Pokémon completo con tipos, stats, habilidades, especie y movimientos **todo embebido**.
El script es **idempotente**: si lo vuelves a correr actualiza los documentos existentes sin duplicar.

> Si MongoDB no está corriendo el script avisa y genera el JSON de todas formas.
> **¿Aún no tienes MongoDB?** La instalación para Linux/Fedora, Windows y macOS está en
> **[docs/MONGO_GUIDE.md](docs/MONGO_GUIDE.md)**.

### 3. Analizar

```bash
jupyter notebook notebooks/relational.ipynb   # análisis sobre SQLite
jupyter notebook notebooks/nosql.ipynb        # consultas sobre MongoDB
```

#### `relational.ipynb` — 10 secciones

| # | Contenido |
|---|-----------|
| 0 | Explorador de tablas — esquema, filas, columnas, nulos, distribuciones |
| 1 | Vista general del dataset |
| 2 | Distribución de tipos primarios |
| 3 | Peso y altura |
| 4 | Stats base (BST) por tipo y generación |
| 5 | Legendarios, míticos y normales |
| 6 | Efectividad de tipos (matriz 18×18) |
| 7 | Combinaciones de tipos |
| 8 | Consultas SQL personalizadas |
| 9 | Visor de Pokémon — ficha individual |

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
- **Actualización incremental** — `build_db.py` reconstruye la BD completa; se puede hacer incremental.
- **Dashboard interactivo** — complementar los notebooks con Streamlit o Plotly Dash.
- **Docker Compose** — levantar MongoDB en contenedor sin instalación local (ver `docs/MONGO_GUIDE.md`).
- **Tests** — pruebas unitarias para los loaders con una muestra pequeña de JSON fijos.
