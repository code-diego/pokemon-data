"""
genera data/sample.db — base de datos reducida (generaciones I–III, ~150 Pokémon).
para el deploy en Streamlit Community Cloud sin necesidad del ETL completo.

>python scripts/build_sample_db.py
* requiere que data/pokemon.db exista (ejecutar build_db.py primero).
"""
import sqlite3
import sys
from pathlib import Path

GENS = ("generation-i", "generation-ii", "generation-iii")

# ── Localizar la BD fuente ────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
SRC  = ROOT / "data" / "pokemon.db"
DST  = ROOT / "data" / "sample.db"

if not SRC.exists():
    print("ERROR: No se encontró data/pokemon.db. Ejecuta primero build_db.py.")
    sys.exit(1)

if DST.exists():
    DST.unlink()

print(f"Fuente:  {SRC}")
print(f"Destino: {DST}")
print(f"Gens:    {', '.join(GENS)}")

src = sqlite3.connect(SRC)
dst = sqlite3.connect(DST)

# ── IDs de Pokémon de las generaciones objetivo (solo formas base) ────────
gen_in = ",".join(f"'{g}'" for g in GENS)
ids = {
    row[0]
    for row in src.execute(
        f"SELECT id FROM species WHERE generation IN ({gen_in}) AND id < 10000"
    )
}
ids_sql = ",".join(str(i) for i in sorted(ids))
print(f"Pokémon incluidos: {len(ids)}")

# ── Mapeo de tabla → filtro WHERE ────────────────────────────────────────
TABLE_FILTERS: dict[str, str] = {
    "pokemon":           f"WHERE id IN ({ids_sql})",
    "species":           f"WHERE id IN ({ids_sql})",
    "pokemon_stats":     f"WHERE pokemon_id IN ({ids_sql})",
    "pokemon_types":     f"WHERE pokemon_id IN ({ids_sql})",
    "pokemon_abilities": f"WHERE pokemon_id IN ({ids_sql})",
    "pokemon_moves":     f"WHERE pokemon_id IN ({ids_sql})",
}
# Las tablas de referencia (types, abilities, moves) se copian completas.

# ── Copiar tablas ─────────────────────────────────────────────────────────
tables = [
    row[0]
    for row in src.execute("SELECT name FROM sqlite_master WHERE type='table'")
]

for table in tables:
    schema_row = src.execute(
        f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"
    ).fetchone()
    if schema_row is None:
        continue
    dst.execute(schema_row[0])

    where = TABLE_FILTERS.get(table, "")
    rows = src.execute(f"SELECT * FROM {table} {where}").fetchall()
    if rows:
        placeholders = ",".join(["?"] * len(rows[0]))
        dst.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    print(f"  {table}: {len(rows)} filas")

dst.commit()
src.close()
dst.close()
print(f"\nListo. sample.db generado en: {DST}")
print("Recuerda: el archivo ya está en .gitignore como excepción (!data/sample.db).")
