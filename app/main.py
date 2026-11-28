import os
import json
import asyncio
from datetime import date, timedelta
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
FOLK_FILE = STATIC_DIR / "data" / "slavic-folk.json"
TRANS_FILE = STATIC_DIR / "data" / "translations.json"

NAGER = "https://date.nager.at/api/v3"
KUZYAK = "https://calendar.kuzyak.in/api/calendar"

SLAVIC_COUNTRIES = [
    {"code": "RU", "name": "Россия"},
    {"code": "UA", "name": "Украина"},
    {"code": "BY", "name": "Беларусь"},
    {"code": "PL", "name": "Польша"},
    {"code": "BG", "name": "Болгария"},
    {"code": "SR", "name": "Сербия"},
    {"code": "HR", "name": "Хорватия"},
    {"code": "SI", "name": "Словения"},
    {"code": "SK", "name": "Словакия"},
    {"code": "CZ", "name": "Чехия"},
    {"code": "MK", "name": "Северная Македония"},
    {"code": "ME", "name": "Черногория"},
    {"code": "BA", "name": "Босния и Герцеговина"},
]

app = FastAPI(title="Календарь славянских праздников (открытые данные)")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

CALENDAR_CACHE: dict[tuple[str, int], list[dict]] = {}
TRANSLATIONS: dict[str, dict[str, str]] = {}


def load_json_file(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_folk_holidays() -> list[dict]:
    return load_json_file(FOLK_FILE, [])


def load_translations() -> dict[str, dict[str, str]]:
    return load_json_file(TRANS_FILE, {})


def translate_holiday(country_code: str, name: str) -> str:
    """Переводит название праздника на русский, если есть в словаре."""
    cc = country_code.upper()
    table = TRANSLATIONS.get(cc, {})
    return table.get(name, name)


async def fetch_json(client: httpx.AsyncClient, url: str):
    resp = await client.get(url, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


async def get_nager_holidays(country_code: str, year: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        try:
            data = await fetch_json(
                client, f"{NAGER}/PublicHolidays/{year}/{country_code.upper()}"
            )
        except Exception:
            return []
    return [
        {
            "date": h["date"],
            "name": h.get("localName") or h.get("name"),
            "country": country_code.upper(),
            "type": "state",
            "source": "nager",
        }
        for h in data
    ]


sem = asyncio.Semaphore(25)


async def fetch_kuzyak_day(client: httpx.AsyncClient, y: int, m: int, d: int):
    async with sem:
        try:
            data = await fetch_json(
                client, f"{KUZYAK}/{y}/{m:02d}/{d:02d}"
            )
            if data.get("holiday"):
                return {
                    "date": data["date"][:10],
                    "name": data["holiday"],
                    "country": "RU",
                    "type": "state",
                    "source": "kuzyak",
                    "isWorkingDay": data.get("isWorkingDay", True),
                    "isShortDay": data.get("isShortDay", False),
                }
        except Exception:
            pass
        return None


async def get_ru_holidays_from_kuzyak(year: int) -> list[dict]:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    results: list[dict] = []

    async with httpx.AsyncClient() as client:
        tasks = []
        cur = start
        while cur <= end:
            tasks.append(fetch_kuzyak_day(client, cur.year, cur.month, cur.day))
            cur += timedelta(days=1)
        for coro in asyncio.as_completed(tasks):
            res = await coro
            if res:
                results.append(res)

    results.sort(key=lambda x: x["date"])
    return results


async def get_ru_holidays(year: int) -> list[dict]:
    cache_key = ("RU", year)
    if cache_key in CALENDAR_CACHE:
        return CALENDAR_CACHE[cache_key]

    try:
        holidays = await get_ru_holidays_from_kuzyak(year)
        if holidays:
            CALENDAR_CACHE[cache_key] = holidays
            return holidays
    except Exception:
        pass

    holidays = await get_nager_holidays("RU", year)
    CALENDAR_CACHE[cache_key] = holidays
    return holidays


@app.on_event("startup")
async def startup():
    global TRANSLATIONS
    TRANSLATIONS = load_translations()


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/countries")
async def countries():
    return SLAVIC_COUNTRIES


@app.get("/api/slavic/forward")
async def slavic_forward(
    country: str = Query(default="RU"),
    days: int = Query(default=365, le=730),
):
    try:
        start = date.today()
        end = start + timedelta(days=days)
        years = sorted({start.year, end.year})
        result: list[dict] = []

        cc = country.upper()

        if cc == "RU":
            for y in years:
                result.extend(await get_ru_holidays(y))
        else:
            for y in years:
                result.extend(await get_nager_holidays(cc, y))

        # Переводим названия на русский
        for item in result:
            item["name"] = translate_holiday(cc, item["name"])

        folk = load_folk_holidays()
        for h in folk:
            try:
                d = date.fromisoformat(h["date"])
            except Exception:
                continue
            if start <= d <= end and (h.get("country", cc) == cc or h.get("country") == "ALL"):
                result.append({
                    "date": h["date"],
                    "name": translate_holiday(h.get("country", cc), h.get("name")),
                    "country": h.get("country", cc),
                    "type": "folk",
                    "source": "folk-json",
                    "weekday": d.strftime("%A"),
                })

        for item in result:
            if "weekday" not in item:
                try:
                    item["weekday"] = date.fromisoformat(item["date"]).strftime("%A")
                except Exception:
                    item["weekday"] = ""

        seen = set()
        unique = []
        for item in sorted(result, key=lambda x: x["date"]):
            key = (item["date"], item["name"])
            if key not in seen:
                seen.add(key)
                unique.append(item)

        final = [
            item for item in unique
            if start <= date.fromisoformat(item["date"]) <= end
        ]
        return final
    except Exception as e:
        return {"error": type(e).__name__ + ": " + str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
