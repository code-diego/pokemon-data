"""
Descarga todos los datos de PokéAPI y los guarda como JSON en data/raw/.
> python3 scripts/fetch.py
* salta archivos que ya existen
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import aiohttp

BASE_URL = "https://pokeapi.co/api/v2"
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
SEMAPHORE_LIMIT = 40

try:
    from tqdm.asyncio import tqdm as atqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def fetch_json(session: aiohttp.ClientSession, sem: asyncio.Semaphore, url: str) -> dict:
    async with sem:
        for attempt in range(3):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    resp.raise_for_status()
                    return await resp.json()
            except Exception as exc:
                if attempt == 2:
                    print(f"\n[ERROR] {url}: {exc}", file=sys.stderr)
                    return {}
                await asyncio.sleep(1 + attempt)
    return {}


async def download_resource(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    resource: str,
    urls: list[tuple[str, str]],  # [(name, url), ...]
) -> int:
    out_dir = DATA_DIR / resource
    out_dir.mkdir(parents=True, exist_ok=True)

    pending = [(name, url) for name, url in urls if not (out_dir / f"{name}.json").exists()]
    skipped = len(urls) - len(pending)

    if not pending:
        print(f"  {resource}: {skipped} archivos ya existían, nada que descargar.")
        return skipped

    print(f"  {resource}: {len(pending)} por descargar ({skipped} ya en caché)…")

    tasks = [fetch_json(session, sem, url) for _, url in pending]

    if HAS_TQDM:
        results = await atqdm.gather(*tasks, desc=f"  {resource}", leave=False)
    else:
        # gather preserva el orden de envío (necesario para zip(pending, results))
        # el contador de progreso se actualiza dentro de cada tarea envuelta
        completed = 0
        total_tasks = len(tasks)

        async def tracked(coro):
            nonlocal completed
            result = await coro
            completed += 1
            if completed % 50 == 0 or completed == total_tasks:
                print(f"    {completed}/{total_tasks}", end="\r")
            return result

        results = await asyncio.gather(*[tracked(t) for t in tasks])
        print()

    saved = 0
    for (name, _), data in zip(pending, results):
        if data:
            (out_dir / f"{name}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=None), encoding="utf-8"
            )
            saved += 1

    print(f"  → guardado en: {out_dir.resolve()}  ({saved} archivos nuevos)")
    return saved + skipped


# ---------------------------------------------------------------------------
# Fetch resource lists
# ---------------------------------------------------------------------------

async def get_all_urls(session: aiohttp.ClientSession, resource: str) -> list[tuple[str, str]]:
    url = f"{BASE_URL}/{resource}?limit=100000"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            resp.raise_for_status()
            payload = await resp.json()
    except Exception as exc:
        print(f"\n[ERROR] No se pudo obtener la lista de {resource}: {exc}", file=sys.stderr)
        return []
    return [(item["name"], item["url"]) for item in payload.get("results", [])]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connector = aiohttp.TCPConnector(limit=SEMAPHORE_LIMIT)
    sem = asyncio.Semaphore(SEMAPHORE_LIMIT)

    async with aiohttp.ClientSession(connector=connector) as session:
        print("Obteniendo listas de recursos…")
        resources = ["pokemon", "pokemon-species", "type", "ability", "move"]
        lists = await asyncio.gather(*[get_all_urls(session, r) for r in resources])

        pokemon_urls, species_urls, type_urls, ability_urls, move_urls = lists

        print(f"  pokemon:          {len(pokemon_urls)}")
        print(f"  pokemon-species:  {len(species_urls)}")
        print(f"  types:            {len(type_urls)}")
        print(f"  abilities:        {len(ability_urls)}")
        print(f"  moves:            {len(move_urls)}")
        print()

        print("Descargando datos…")
        await download_resource(session, sem, "pokemon", pokemon_urls)
        await download_resource(session, sem, "species", species_urls)
        await download_resource(session, sem, "types", type_urls)
        await download_resource(session, sem, "abilities", ability_urls)
        await download_resource(session, sem, "moves", move_urls)

    total = sum(len(list(p.glob("*.json"))) for p in DATA_DIR.iterdir() if p.is_dir())
    print(f"\nListo. {total} archivos JSON en {DATA_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
