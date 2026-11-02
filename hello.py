from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

app = FastAPI(title="TPI IoT API")

DEV_PATTERN = r"^[a-z0-9-]{1,32}$"


class Reading(BaseModel):
    # Nume de 1-32 caractere: a-z, 0-9 si cratima.
    dev: str = Field(pattern=DEV_PATTERN)
    # Numar de ordine intreg, minim 0, pentru evitarea duplicatelor.
    seq: int = Field(ge=0)
    # Timp Unix UTC peste 1.600.000.000, pentru a evita datele primele de la un senzor cu ceas nesetat.
    ts: int = Field(gt=1_600_000_000)
    # Temperatura intre -40 si 85 grade Celsius.
    temp: float = Field(ge=-40, le=85)
    # Umiditate intre 0 si 100%, optionala (nullable).
    hum: float | None = Field(default=None, ge=0, le=100)


# Citirile sunt salvate in memorie, dupa dispozitiv si seq.
DB: dict[str, dict[int, Reading]] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/readings", status_code=201)
def create_reading(reading: Reading) -> Reading:
    device_readings = DB.setdefault(reading.dev, {})

    if reading.seq in device_readings:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Citirea cu seq={reading.seq} exista deja "
                f"pentru dispozitivul '{reading.dev}'."
            ),
        )

    device_readings[reading.seq] = reading

    return reading


@app.get("/devices/{dev_id}/readings")
def readings(
    dev_id: str = Path(pattern=DEV_PATTERN),
    since: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    min_temp: float | None = Query(default=None),
) -> list[Reading]:
    device_readings = DB.get(dev_id)

    if not device_readings:
        raise HTTPException(
            status_code=404,
            detail=f"Dispozitivul '{dev_id}' nu are citiri salvate.",
        )

    ordered_readings = [
        device_readings[seq]
        for seq in sorted(device_readings)
        if seq > since
        and (min_temp is None or device_readings[seq].temp >= min_temp)
    ]

    return ordered_readings[:limit]


@app.get("/devices")
def devices() -> list[dict[str, str | int]]:
    return [
        {"dev": dev, "readings_count": len(device_readings)}
        for dev, device_readings in sorted(DB.items())
    ]
