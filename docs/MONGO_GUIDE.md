# Guía de MongoDB para este proyecto

Esta guía te lleva desde cero hasta tener MongoDB corriendo y los datos Pokémon cargados.

---

## ¿Qué es MongoDB y por qué usarlo aquí?

| | SQLite (`pokemon.db`) | MongoDB (`pokemon_data`) |
|---|---|---|
| Modelo | Tablas relacionadas (9 tablas) | Documentos JSON anidados |
| Consultar un Pokémon | JOIN de 5+ tablas | Un solo `find()` |
| Estructura | Fija (columnas declaradas) | Flexible (cada doc puede variar) |
| Ideal para | Análisis con SQL, agregaciones | Exploración, APIs, filtros complejos |

En este proyecto ambas bases coexisten con los mismos datos, pero en formatos distintos.
Así puedes comparar el estilo SQL vs. el estilo documento.

---

## 1. Instalar MongoDB en Fedora

MongoDB no está en los repositorios oficiales de Fedora, pero el repo de RHEL 9 funciona.

### Paso 1 — Agregar el repositorio

Crea el archivo `/etc/yum.repos.d/mongodb-org-8.0.repo` con este contenido:

```ini
[mongodb-org-8.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/9/mongodb-org/8.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-8.0.asc
```

Puedes crearlo con:

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

### Paso 2 — Instalar

```bash
sudo dnf install -y mongodb-org
```

---

## 2. Iniciar, detener y verificar el servicio

```bash
# Iniciar MongoDB
sudo systemctl start mongod

# Que inicie automáticamente al arrancar la PC (opcional)
sudo systemctl enable mongod

# Ver si está corriendo
sudo systemctl status mongod

# Detener
sudo systemctl stop mongod
```

Una salida como `Active: active (running)` confirma que está listo.

---

## 3. Verificar que funciona

```bash
mongosh --eval "db.runCommand({ping: 1})"
```

Deberías ver:

```
{ ok: 1 }
```

Si ves ese `ok: 1`, MongoDB está listo para recibir datos.

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
  "stats": {"hp": 35, "attack": 55, "speed": 90, ...},
  "abilities": [{"name": "static", "is_hidden": false, "effect": "..."}],
  "species": {"is_legendary": false, "generation": "generation-i", ...},
  "moves": [{"name": "thunder-shock", "power": 40, ...}]
}
```

Todo lo que en SQLite está en 5 tablas distintas, aquí está en un solo documento.

---

## 5. Cargar los datos Pokémon

Primero asegúrate de haber descargado los datos crudos:

```bash
python fetch.py       # Descarga ~3,700 JSON de PokéAPI (solo la primera vez)
```

Luego carga a MongoDB:

```bash
python build_nosql.py
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

El script es idempotente: si lo corres dos veces, la segunda vez dirá
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
pip install pymongo
# o con el requirements.txt del proyecto:
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

Para queries más avanzadas con pandas y visualizaciones, abre `analysis.ipynb`
y ve a la sección **"10. Consultas MongoDB"**.

---

## 8. Cambiar la URL de conexión (MONGO_URI)

Por defecto el proyecto conecta a `mongodb://localhost:27017`. Si necesitas cambiar esto
(por ejemplo cuando agregues Docker más adelante), usa la variable de entorno:

```bash
# Linux/macOS
export MONGO_URI="mongodb://localhost:27017"
python build_nosql.py

# O en una sola línea
MONGO_URI="mongodb://mi-servidor:27017" python build_nosql.py
```

---

## 9. Próximos pasos — Docker

Cuando quieras aprender Docker, el siguiente paso natural es crear un `docker-compose.yml`
que levante MongoDB (y opcionalmente `mongo-express`, una UI web para ver los datos)
sin necesidad de instalarlo en el sistema. El script `build_nosql.py` ya está preparado:
solo cambia `MONGO_URI` y funcionará igual.

```
# En el futuro:
docker compose up -d
MONGO_URI="mongodb://localhost:27017" python build_nosql.py
```

---

## Resumen de comandos del día a día

```bash
# 1. Iniciar MongoDB (si no está corriendo)
sudo systemctl start mongod

# 2. Cargar / actualizar datos
python build_nosql.py

# 3. Abrir notebook
jupyter notebook analysis.ipynb

# 4. Explorar en consola
mongosh
```
