import os
from datetime import date
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
NAGER_BASE = "https://date.nager.at/api/v3"

app = FastAPI(title="Календарь праздников мира")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

FALLBACK_COUNTRIES = [
    {"code": "US", "name": "США"},
    {"code": "RU", "name": "Россия"},
    {"code": "GB", "name": "Великобритания"},
    {"code": "DE", "name": "Германия"},
    {"code": "FR", "name": "Франция"},
    {"code": "IT", "name": "Италия"},
    {"code": "ES", "name": "Испания"},
    {"code": "CA", "name": "Канада"},
    {"code": "AU", "name": "Австралия"},
    {"code": "JP", "name": "Япония"},
    {"code": "CN", "name": "Китай"},
    {"code": "IN", "name": "Индия"},
    {"code": "BR", "name": "Бразилия"},
    {"code": "MX", "name": "Мексика"},
    {"code": "AR", "name": "Аргентина"},
]


async def fetch_json(client: httpx.AsyncClient, url: str):
    try:
        resp = await client.get(url, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ошибка доступа к сервису праздников: {exc}")


async def get_holidays_data(country_code: str, year: int):
    async with httpx.AsyncClient() as client:
        return await fetch_json(
            client, f"{NAGER_BASE}/PublicHolidays/{year}/{country_code.upper()}"
        )


@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/countries")
async def countries():
    async with httpx.AsyncClient() as client:
        try:
            data = await fetch_json(client, f"{NAGER_BASE}/AvailableCountries")
            return [{"code": c["countryCode"], "name": c["name"]} for c in data]
        except HTTPException:
            return FALLBACK_COUNTRIES


@app.get("/api/holidays/{country_code}")
async def holidays_by_year(country_code: str, year: int = Query(default=date.today().year)):
    return await get_holidays_data(country_code, year)


@app.get("/api/holidays/{country_code}/{year}/{month}/{day}")
async def holidays_by_date(country_code: str, year: int, month: int, day: int):
    all_holidays = await get_holidays_data(country_code, year)
    target = f"{year:04d}-{month:02d}-{day:02d}"
    return [h for h in all_holidays if h.get("date") == target]


@app.get("/api/holidays/today/{country_code}")
async def holidays_today(country_code: str):
    today = date.today()
    return await holidays_by_date(country_code, today.year, today.month, today.day)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))