# pokemon-data

Pipeline ETL que descarga todos los datos de [PokéAPI](https://pokeapi.co), los almacena como JSON en caché local y los carga en una base de datos SQLite lista para analizar.

## Estructura

```
pokemon-data/
├── fetch.py       # Descarga los datos de PokéAPI → data/
├── build_db.py    # Construye pokemon.db a partir de data/
├── analysis.ipynb # Notebook de análisis exploratorio
└── data/          # Caché JSON (ignorada por git)
    ├── pokemon/
    ├── species/
    ├── types/
    ├── abilities/
    └── moves/
```

## Requisitos

```bash
pip install aiohttp tqdm
```

`tqdm` es opcional — si no está instalado la descarga muestra progreso básico por consola.

## Uso

### 1. Descargar datos

```bash
python fetch.py
```

Descarga pokémon, especies, tipos, habilidades y movimientos de PokéAPI y los guarda en `data/`. Es **idempotente**: si ya existe un archivo JSON lo salta, así que puedes reanudar una descarga interrumpida.

### 2. Construir la base de datos

```bash
python build_db.py
```

Lee los JSON de `data/` y genera `pokemon.db` (SQLite). La base de datos incluye estas tablas:

| Tabla              | Contenido                                              |
|--------------------|--------------------------------------------------------|
| `pokemon`          | Id, nombre, altura, peso, experiencia base, sprite URL |
| `pokemon_stats`    | HP, ataque, defensa, velocidad, etc. por pokémon       |
| `pokemon_types`    | Tipos por pokémon (agua, fuego…)                       |
| `pokemon_abilities`| Habilidades por pokémon                                |
| `pokemon_moves`    | Movimientos aprendibles, método y nivel                |
| `species`          | Color, forma, hábitat, si es legendario/mítico, generación |
| `types`            | Relaciones de daño entre tipos                         |
| `abilities`        | Nombre y efecto en inglés                              |
| `moves`            | Poder, precisión, PP, tipo y clase de daño             |

### 3. Analizar

Abre `analysis.ipynb` en Jupyter y ejecuta las celdas. El notebook trabaja directamente sobre `pokemon.db` con `sqlite3` y `pandas`.

```bash
jupyter notebook analysis.ipynb
```

## Posibles mejoras

- **Exportar a otros formatos** — generar CSV o Parquet desde la base de datos para usar con Excel, Tableau o herramientas de BI.
- **Añadir evoluciones** — la tabla `evolution-chain` de PokéAPI no está incluida; agregarla permitiría análisis de cadenas evolutivas.
- **Texto en español** — los efectos de habilidades y descripciones de especies se guardan solo en inglés; se puede añadir soporte multilenguaje.
- **Actualización incremental** — actualmente `build_db.py` borra y reconstruye la BD completa; se podría hacer una carga incremental comparando versiones.
- **Dashboard interactivo** — reemplazar o complementar el notebook con un dashboard en Streamlit o Plotly Dash.
- **Tests** — añadir pruebas para los loaders de `build_db.py` con una muestra pequeña de JSON fijos.
- **Dockerizar** — empaquetar el pipeline en un contenedor para reproducibilidad sin instalar dependencias manualmente.
