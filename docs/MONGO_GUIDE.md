# Guía de MongoDB para este proyecto

Esta guía te lleva desde cero hasta tener MongoDB corriendo y los datos Pokémon cargados.

---

## ¿Qué es MongoDB y por qué usarlo aquí?

| | SQLite (`data/pokemon.db`) | MongoDB (`pokemon_data`) |
|---|---|---|
| Modelo | Tablas relacionadas (9 tablas) | Documentos JSON anidados |
| Consultar un Pokémon | JOIN de 5+ tablas | Un solo `find()` |
| Estructura | Fija (columnas declaradas) | Flexible (cada doc puede variar) |
| Ideal para | Análisis con SQL, agregaciones | Exploración, APIs, filtros complejos |

En este proyecto ambas bases coexisten con los mismos datos, pero en formatos distintos.
Así puedes comparar el estilo SQL vs. el estilo documento.

---

## 1. Instalar MongoDB — aviso importante (Fedora 44 / kernel 6.19+)

> **MongoDB 8.0 no arranca en kernels 6.19 o superior** (incluyendo Fedora 44 con kernel 7.x).
> Es un bug conocido de incompatibilidad con io_uring: [SERVER-121912](https://jira.mongodb.org/browse/SERVER-121912).
> La solución correcta es correr MongoDB en un **contenedor Podman** con la versión 7.0.

Si tienes Fedora ≤ 43 (kernel < 6.19) y MongoDB 8.0 te funciona, puedes saltar al paso 2.
De lo contrario, sigue la sección de Podman a continuación.

---

## 2. Correr MongoDB con Podman (recomendado en Fedora 44+)

Podman ya viene instalado en Fedora. No necesitas Docker ni permisos de root.

### Paso 1 — Descargar la imagen

```bash
podman pull docker.io/mongo:7.0
```

### Paso 2 — Iniciar el contenedor

```bash
podman run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  docker.io/mongo:7.0
```

- `-d` lo corre en segundo plano
- `--name mongodb` le da un nombre fijo para manejarlo fácil
- `-p 27017:27017` expone el puerto al host (el script lo conecta en `localhost:27017`)
- `-v mongodb_data:/data/db` persiste los datos entre reinicios

### Paso 3 — Verificar que funciona

```bash
mongosh --quiet --eval "db.runCommand({ping: 1})"
```

Deberías ver:

```
{ ok: 1 }
```

### Autoarranque al iniciar sesión

Para que el contenedor inicie automáticamente cuando entres a tu sesión:

```bash
podman generate systemd --new --name mongodb > ~/.config/systemd/user/mongodb.service
systemctl --user daemon-reload
systemctl --user enable mongodb.service
```

### Comandos del día a día

```bash
# Ver si está corriendo
podman ps

# Iniciar (si está detenido)
podman start mongodb

# Detener
podman stop mongodb

# Reiniciar
podman restart mongodb

# Ver logs en tiempo real
podman logs -f mongodb
```

---

## 3. Instalar MongoDB directamente (solo si tu kernel < 6.19)

Si tu kernel es anterior a 6.19 y prefieres la instalación nativa de Fedora:

### Agregar el repositorio

```bash
sudo tee /etc/yum.repos.d/mongodb-org-8.0.repo << 'EOF'
[mongodb-org-8.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/9/mongodb-org/8.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-8.0.asc
EOF
```

### Instalar y arrancar

```bash
sudo dnf install -y mongodb-org
sudo systemctl enable --now mongod
sudo systemctl status mongod   # debe mostrar "active (running)"
```

---

## 4. Conceptos básicos (analogía con SQLite)

| Concepto MongoDB | Equivalente SQL | Descripción |
|---|---|---|
| **Database** | Base de datos | Contenedor principal (ej. `pokemon_data`) |
| **Collection** | Tabla | Grupo de documentos (ej. `pokemon`) |
| **Document** | Fila | Un objeto JSON (ej. los datos de Pikachu) |
| **Field** | Columna | Un campo dentro del documento (ej. `name`) |
| **`_id`** | PRIMARY KEY | Identificador único auto-generado |

La diferencia clave: en SQL cada fila tiene exactamente las mismas columnas. En MongoDB
cada documento puede tener campos distintos, y los valores pueden ser arrays u otros objetos.

Ejemplo de documento en este proyecto:
```json
{
  "_id": "...",
  "id": 25,
  "name": "pikachu",
  "types": [{"name": "electric", "slot": 1}],
  "stats": {"hp": 35, "attack": 55, "speed": 90},
  "abilities": [{"name": "static", "is_hidden": false, "effect": "..."}],
  "species": {"is_legendary": false, "generation": "generation-i"},
  "moves": [{"name": "thunder-shock", "power": 40}]
}
```

Todo lo que en SQLite está en 5 tablas distintas, aquí está en un solo documento.

---

## 5. Cargar los datos Pokémon

Primero descarga los datos crudos (si no lo has hecho):

```bash
python scripts/fetch.py       # Descarga ~3,700 JSON de PokéAPI (solo la primera vez)
```

Luego carga a MongoDB (y genera `data/pokemon_docs.json`):

```bash
python scripts/build_nosql.py
```

Deberías ver algo como:

```
Cargando índices…
  Habilidades: 371
  Movimientos: 937
  Especies:    1025
  Tipos:       21

Construyendo documentos desnormalizados…

JSON: 1350 documentos → data/pokemon_docs.json  (45.2 MB)

Conectando a MongoDB (mongodb://localhost:27017)…
MongoDB → pokemon_data.pokemon
  Insertados: 1350  |  Actualizados: 0  |  Total: 1350
```

El script es idempotente: si lo corres dos veces, la segunda dirá
`Insertados: 0 | Actualizados: 1350` (actualiza en lugar de duplicar).

---

## 6. Explorar datos con mongosh

Abre la consola de MongoDB:

```bash
mongosh
```

Comandos útiles:

```javascript
// Ver todas las bases de datos
show dbs

// Seleccionar la base de datos del proyecto
use pokemon_data

// Ver las colecciones disponibles
show collections

// Contar cuántos Pokémon hay
db.pokemon.countDocuments()

// Ver un documento completo (Bulbasaur)
db.pokemon.findOne({ name: "bulbasaur" })

// Solo algunos campos (como SELECT name, types FROM pokemon)
db.pokemon.findOne({ name: "pikachu" }, { name: 1, types: 1, stats: 1, _id: 0 })

// Buscar todos los legendarios
db.pokemon.find({ "species.is_legendary": true }, { name: 1, _id: 0 }).limit(10)

// Pokémon de tipo fuego (tipo primario)
db.pokemon.find({ "types.0.name": "fire" }, { name: 1, _id: 0 })

// Salir de mongosh
exit
```

---

## 7. Usar desde Python (pymongo)

Instala el driver:

```bash
pip install -r requirements.txt
```

Snippet básico:

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
col = client["pokemon_data"]["pokemon"]

# Buscar un Pokémon
charizard = col.find_one({"name": "charizard"})
print(charizard["stats"])

# Todos los legendarios
legendarios = list(col.find({"species.is_legendary": True}, {"name": 1, "_id": 0}))
print(f"{len(legendarios)} legendarios")

client.close()
```

Para queries con pandas y visualizaciones, abre el notebook:

```bash
jupyter notebook notebooks/nosql.ipynb
```

---

## 8. Cambiar la URL de conexión (MONGO_URI)

Por defecto el proyecto conecta a `mongodb://localhost:27017`. Si necesitas cambiar esto:

```bash
# Variable de entorno en una sola línea
MONGO_URI="mongodb://mi-servidor:27017" python scripts/build_nosql.py
```

---

## Resumen de comandos del día a día

```bash
# 1. Verificar que MongoDB está corriendo
podman ps | grep mongodb           # debe aparecer "Up"
mongosh --quiet --eval "db.runCommand({ping:1})"  # debe responder { ok: 1 }

# 2. Iniciar si está detenido
podman start mongodb

# 3. Cargar / actualizar datos
python scripts/build_nosql.py

# 4. Abrir notebook
jupyter notebook notebooks/nosql.ipynb

# 5. Explorar en consola
mongosh
```
