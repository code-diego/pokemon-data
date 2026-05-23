"""
Lee la caché JSON de data/raw/ y produce:
  1. data/pokemon_docs.json  — respaldo JSON local
  2. MongoDB pokemon_data.pokemon  — documentos desnormalizados listos para consultas

Requiere haber ejecutado scripts/fetch.py primero.
Requiere pymongo: pip install pymongo
"""

import json
import os
from pathlib import Path

try:
    from pymongo import MongoClient
    from pymongo.operations import UpdateOne
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

RAW_DIR  = Path(__file__).parent.parent / "data" / "raw"
OUT_FILE = Path(__file__).parent.parent / "data" / "pokemon_docs.json"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = "pokemon_data"
MONGO_COL = "pokemon"


# ---------------------------------------------------------------------------
# Cargar tablas de referencia en memoria
# ---------------------------------------------------------------------------

def load_abilities_index() -> dict[str, str | None]:
    """name → effect (EN)"""
    index = {}
    for path in (RAW_DIR / "abilities").glob("*.json"):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        effect = next(
            (e["effect"] for e in d.get("effect_entries", [])
             if e.get("language", {}).get("name") == "en"),
            None,
        )
        index[d["name"]] = effect
    return index


def load_moves_index() -> dict[str, dict]:
    """name → {power, accuracy, pp, type, damage_class}"""
    index = {}
    for path in (RAW_DIR / "moves").glob("*.json"):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        index[d["name"]] = {
            "power":        d.get("power"),
            "accuracy":     d.get("accuracy"),
            "pp":           d.get("pp"),
            "type":         (d.get("type") or {}).get("name"),
            "damage_class": (d.get("damage_class") or {}).get("name"),
        }
    return index


def load_species_index() -> dict[str, dict]:
    """name → species fields"""
    index = {}
    for path in (RAW_DIR / "species").glob("*.json"):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        flavor = next(
            (f["flavor_text"].replace("\n", " ").replace("\f", " ")
             for f in d.get("flavor_text_entries", [])
             if f.get("language", {}).get("name") == "en"),
            None,
        )
        index[d["name"]] = {
            "color":          (d.get("color") or {}).get("name"),
            "shape":          (d.get("shape") or {}).get("name"),
            "habitat":        (d.get("habitat") or {}).get("name"),
            "is_legendary":   d.get("is_legendary", False),
            "is_mythical":    d.get("is_mythical", False),
            "generation":     (d.get("generation") or {}).get("name"),
            "capture_rate":   d.get("capture_rate"),
            "gender_rate":    d.get("gender_rate"),
            "base_happiness": d.get("base_happiness"),
            "flavor_text":    flavor,
            "evolves_from":   (d.get("evolves_from_species") or {}).get("name"),
        }
    return index


def load_types_index() -> dict[str, dict]:
    """name → damage_relations"""
    index = {}
    for path in (RAW_DIR / "types").glob("*.json"):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        dr = d.get("damage_relations", {})
        index[d["name"]] = {
            "double_damage_to":   [x["name"] for x in dr.get("double_damage_to", [])],
            "half_damage_to":     [x["name"] for x in dr.get("half_damage_to", [])],
            "no_damage_to":       [x["name"] for x in dr.get("no_damage_to", [])],
            "double_damage_from": [x["name"] for x in dr.get("double_damage_from", [])],
            "half_damage_from":   [x["name"] for x in dr.get("half_damage_from", [])],
            "no_damage_from":     [x["name"] for x in dr.get("no_damage_from", [])],
        }
    return index


# ---------------------------------------------------------------------------
# Construir documentos
# ---------------------------------------------------------------------------

def build_documents(
    abilities_idx: dict,
    moves_idx: dict,
    species_idx: dict,
    types_idx: dict,
) -> list[dict]:
    docs = []

    for path in sorted((RAW_DIR / "pokemon").glob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        pid = d.get("id")
        if not pid:
            continue

        # Tipos con relaciones embebidas
        types = []
        for t in d.get("types", []):
            tname = t["type"]["name"]
            types.append({
                "name": tname,
                "slot": t["slot"],
                "damage_relations": types_idx.get(tname, {}),
            })

        # Habilidades con efecto embebido
        abilities = []
        for a in d.get("abilities", []):
            aname = a["ability"]["name"]
            abilities.append({
                "name":      aname,
                "is_hidden": a["is_hidden"],
                "slot":      a["slot"],
                "effect":    abilities_idx.get(aname),
            })

        # Stats como objeto plano
        stats = {s["stat"]["name"]: s["base_stat"] for s in d.get("stats", [])}
        effort = {s["stat"]["name"]: s["effort"] for s in d.get("stats", []) if s["effort"]}

        # Movimientos — agrupa métodos por movimiento, embebe stats del move
        moves_map: dict[str, dict] = {}
        for m in d.get("moves", []):
            mname = m["move"]["name"]
            if mname not in moves_map:
                moves_map[mname] = {
                    "name":    mname,
                    "methods": [],
                    **moves_idx.get(mname, {}),
                }
            for vg in m.get("version_group_details", []):
                moves_map[mname]["methods"].append({
                    "learn_method":  vg["move_learn_method"]["name"],
                    "level":         vg["level_learned_at"],
                    "version_group": vg["version_group"]["name"],
                })

        # Especies
        species_name = (d.get("species") or {}).get("name")
        species_data = species_idx.get(species_name, {}) if species_name else {}

        doc = {
            "id":              pid,
            "name":            d.get("name"),
            "height":          d.get("height"),
            "weight":          d.get("weight"),
            "base_experience": d.get("base_experience"),
            "sprite":          (d.get("sprites") or {}).get("front_default"),
            "types":           types,
            "stats":           stats,
            "effort_values":   effort,
            "abilities":       abilities,
            "species":         species_data,
            "moves":           list(moves_map.values()),
        }
        docs.append(doc)

    return docs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not (RAW_DIR / "pokemon").exists():
        print("No se encontró data/raw/pokemon/. Ejecuta fetch.py primero.")
        return

    print("Cargando índices…")
    abilities_idx = load_abilities_index()
    moves_idx     = load_moves_index()
    species_idx   = load_species_index()
    types_idx     = load_types_index()

    print(f"  Habilidades: {len(abilities_idx)}")
    print(f"  Movimientos: {len(moves_idx)}")
    print(f"  Especies:    {len(species_idx)}")
    print(f"  Tipos:       {len(types_idx)}")

    print("\nConstruyendo documentos desnormalizados…")
    docs = build_documents(abilities_idx, moves_idx, species_idx, types_idx)
    docs.sort(key=lambda x: x["id"])

    OUT_FILE.write_text(
        json.dumps(docs, ensure_ascii=False, indent=None),
        encoding="utf-8",
    )

    size_mb = OUT_FILE.stat().st_size / 1_048_576
    print(f"\nJSON: {len(docs)} documentos → {OUT_FILE}  ({size_mb:.1f} MB)")

    load_to_mongo(docs)


# ---------------------------------------------------------------------------
# Carga a MongoDB
# ---------------------------------------------------------------------------

def load_to_mongo(docs: list[dict]) -> None:
    if not HAS_MONGO:
        print("\n[AVISO] pymongo no está instalado. Ejecuta: pip install pymongo")
        print("        Los datos siguen disponibles en data/pokemon_docs.json")
        return

    print(f"\nConectando a MongoDB ({MONGO_URI})…")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
    except Exception as exc:
        print(f"[ERROR] No se pudo conectar a MongoDB: {exc}")
        print("        Verifica que mongod esté corriendo. Consulta docs/MONGO_GUIDE.md")
        return

    col = client[MONGO_DB][MONGO_COL]

    ops = [
        UpdateOne({"id": doc["id"]}, {"$set": doc}, upsert=True)
        for doc in docs
    ]
    result = col.bulk_write(ops, ordered=False)

    inserted  = result.upserted_count
    modified  = result.modified_count
    print(f"MongoDB → {MONGO_DB}.{MONGO_COL}")
    print(f"  Insertados: {inserted}  |  Actualizados: {modified}  |  Total: {len(docs)}")
    client.close()


if __name__ == "__main__":
    main()
