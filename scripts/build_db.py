"""
Lee el JSON de data/raw/ y construye data/pokemon.db (SQLite).
> python scripts/build_db.py
* requiere haber ejecutado scripts/fetch.py primero.
"""

import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DB_PATH  = Path(__file__).parent.parent / "data" / "pokemon.db"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS pokemon (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    height           INTEGER,
    weight           INTEGER,
    base_experience  INTEGER,
    sprite_default   TEXT
);

CREATE TABLE IF NOT EXISTS pokemon_stats (
    pokemon_id  INTEGER REFERENCES pokemon(id),
    stat_name   TEXT,
    base_value  INTEGER,
    effort      INTEGER,
    PRIMARY KEY (pokemon_id, stat_name)
);

CREATE TABLE IF NOT EXISTS pokemon_types (
    pokemon_id  INTEGER REFERENCES pokemon(id),
    type_name   TEXT,
    slot        INTEGER,
    PRIMARY KEY (pokemon_id, slot)
);

CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id    INTEGER REFERENCES pokemon(id),
    ability_name  TEXT,
    is_hidden     INTEGER,
    slot          INTEGER,
    PRIMARY KEY (pokemon_id, slot)
);

CREATE TABLE IF NOT EXISTS species (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    color           TEXT,
    shape           TEXT,
    habitat         TEXT,
    is_legendary    INTEGER,
    is_mythical     INTEGER,
    generation      TEXT,
    capture_rate    INTEGER,
    gender_rate     INTEGER,
    base_happiness  INTEGER
);

CREATE TABLE IF NOT EXISTS types (
    name                  TEXT PRIMARY KEY,
    double_damage_to      TEXT,
    half_damage_to        TEXT,
    no_damage_to          TEXT,
    double_damage_from    TEXT,
    half_damage_from      TEXT,
    no_damage_from        TEXT
);

CREATE TABLE IF NOT EXISTS abilities (
    name    TEXT PRIMARY KEY,
    effect  TEXT
);

CREATE TABLE IF NOT EXISTS moves (
    name          TEXT PRIMARY KEY,
    power         INTEGER,
    accuracy      INTEGER,
    pp            INTEGER,
    type_name     TEXT,
    damage_class  TEXT
);

CREATE TABLE IF NOT EXISTS pokemon_moves (
    pokemon_id    INTEGER REFERENCES pokemon(id),
    move_name     TEXT,
    learn_method  TEXT,
    level_learned INTEGER,
    PRIMARY KEY (pokemon_id, move_name, learn_method)
);
"""


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_pokemon(conn: sqlite3.Connection) -> int:
    poke_dir = DATA_DIR / "pokemon"
    if not poke_dir.exists():
        print("  [AVISO] Carpeta data/raw/pokemon no encontrada. Ejecuta fetch.py primero.")
        return 0

    rows_poke, rows_stats, rows_types, rows_abilities, rows_moves = [], [], [], [], []

    for path in sorted(poke_dir.glob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        pid = d.get("id")
        if not pid:
            continue

        sprite = (d.get("sprites") or {}).get("front_default")
        rows_poke.append((
            pid, d.get("name"), d.get("height"), d.get("weight"),
            d.get("base_experience"), sprite,
        ))

        for s in d.get("stats", []):
            rows_stats.append((pid, s["stat"]["name"], s["base_stat"], s["effort"]))

        for t in d.get("types", []):
            rows_types.append((pid, t["type"]["name"], t["slot"]))

        for a in d.get("abilities", []):
            rows_abilities.append((pid, a["ability"]["name"], int(a["is_hidden"]), a["slot"]))

        for m in d.get("moves", []):
            move_name = m["move"]["name"]
            for vg in m.get("version_group_details", []):
                rows_moves.append((
                    pid, move_name,
                    vg["move_learn_method"]["name"],
                    vg["level_learned_at"],
                ))

    cur = conn.cursor()
    cur.executemany("INSERT OR REPLACE INTO pokemon VALUES (?,?,?,?,?,?)", rows_poke)
    cur.executemany("INSERT OR REPLACE INTO pokemon_stats VALUES (?,?,?,?)", rows_stats)
    cur.executemany("INSERT OR REPLACE INTO pokemon_types VALUES (?,?,?)", rows_types)
    cur.executemany("INSERT OR REPLACE INTO pokemon_abilities VALUES (?,?,?,?)", rows_abilities)
    cur.executemany("INSERT OR REPLACE INTO pokemon_moves VALUES (?,?,?,?)", rows_moves)
    conn.commit()
    return len(rows_poke)


def load_species(conn: sqlite3.Connection) -> int:
    sp_dir = DATA_DIR / "species"
    if not sp_dir.exists():
        return 0

    rows = []
    for path in sorted(sp_dir.glob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        sid = d.get("id")
        if not sid:
            continue

        rows.append((
            sid, d.get("name"),
            (d.get("color") or {}).get("name"),
            (d.get("shape") or {}).get("name"),
            (d.get("habitat") or {}).get("name"),
            int(d.get("is_legendary", False)),
            int(d.get("is_mythical", False)),
            (d.get("generation") or {}).get("name"),
            d.get("capture_rate"),
            d.get("gender_rate"),
            d.get("base_happiness"),
        ))

    conn.cursor().executemany("INSERT OR REPLACE INTO species VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    return len(rows)


def _damage_names(dr: dict, key: str) -> str:
    return ",".join(x["name"] for x in dr.get(key, []))


def load_types(conn: sqlite3.Connection) -> int:
    t_dir = DATA_DIR / "types"
    if not t_dir.exists():
        return 0

    rows = []
    for path in sorted(t_dir.glob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        dr = d.get("damage_relations", {})
        rows.append((
            d.get("name"),
            _damage_names(dr, "double_damage_to"), _damage_names(dr, "half_damage_to"),
            _damage_names(dr, "no_damage_to"),     _damage_names(dr, "double_damage_from"),
            _damage_names(dr, "half_damage_from"), _damage_names(dr, "no_damage_from"),
        ))

    conn.cursor().executemany("INSERT OR REPLACE INTO types VALUES (?,?,?,?,?,?,?)", rows)
    conn.commit()
    return len(rows)


def load_abilities(conn: sqlite3.Connection) -> int:
    a_dir = DATA_DIR / "abilities"
    if not a_dir.exists():
        return 0

    rows = []
    for path in sorted(a_dir.glob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        effect = next(
            (e["effect"] for e in d.get("effect_entries", []) if e.get("language", {}).get("name") == "en"),
            None,
        )
        rows.append((d.get("name"), effect))

    conn.cursor().executemany("INSERT OR REPLACE INTO abilities VALUES (?,?)", rows)
    conn.commit()
    return len(rows)


def load_moves(conn: sqlite3.Connection) -> int:
    m_dir = DATA_DIR / "moves"
    if not m_dir.exists():
        return 0

    rows = []
    for path in sorted(m_dir.glob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        rows.append((
            d.get("name"),
            d.get("power"),
            d.get("accuracy"),
            d.get("pp"),
            (d.get("type") or {}).get("name"),
            (d.get("damage_class") or {}).get("name"),
        ))

    conn.cursor().executemany("INSERT OR REPLACE INTO moves VALUES (?,?,?,?,?,?)", rows)
    conn.commit()
    return len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    print("Cargando datos en SQLite…")

    n_poke     = load_pokemon(conn)
    n_species  = load_species(conn)
    n_types    = load_types(conn)
    n_abil     = load_abilities(conn)
    n_moves    = load_moves(conn)

    conn.close()

    print(f"\nBase de datos creada en: {DB_PATH}")
    print(f"  Pokémon:    {n_poke}")
    print(f"  Especies:   {n_species}")
    print(f"  Tipos:      {n_types}")
    print(f"  Habilidades:{n_abil}")
    print(f"  Movimientos:{n_moves}")


if __name__ == "__main__":
    main()
