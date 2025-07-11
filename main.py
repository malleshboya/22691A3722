from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from datetime import datetime, timedelta
from middleware import log_middleware
from storage import db, click_stats
import string
import random

app = FastAPI()
app.middleware("http")(log_middleware)


class URLRequest(BaseModel):
    url: HttpUrl
    validity: int = 30
    shortcode: str | None = None


class URLResponse(BaseModel):
    shortLink: str
    expiry: str


@app.post("/shorturls", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(data: URLRequest):
    shortcode = data.shortcode or generate_shortcode()
    if not shortcode.isalnum() or len(shortcode) > 20:
        raise HTTPException(status_code=400, detail="Invalid shortcode format.")

    if shortcode in db:
        raise HTTPException(status_code=409, detail="Shortcode already exists.")

    expiry_time = datetime.utcnow() + timedelta(minutes=data.validity)
    db[shortcode] = {
        "original_url": str(data.url),
        "created_at": datetime.utcnow(),
        "expires_at": expiry_time,
        "clicks": 0
    }

    return {
        "shortLink": f"http://localhost:8000/{shortcode}",
        "expiry": expiry_time.isoformat() + "Z"
    }


@app.get("/{shortcode}")
async def redirect_to_url(request: Request, shortcode: str):
    entry = db.get(shortcode)
    if not entry:
        raise HTTPException(status_code=404, detail="Shortcode not found.")
    if datetime.utcnow() > entry["expires_at"]:
        raise HTTPException(status_code=410, detail="Link expired.")

    entry["clicks"] += 1
    click_stats.setdefault(shortcode, []).append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "referrer": request.headers.get("referer", "unknown"),
        "geo": "IN"
    })

    return RedirectResponse(url=entry["original_url"])


@app.get("/shorturls/{shortcode}")
async def get_stats(shortcode: str):
    entry = db.get(shortcode)
    if not entry:
        raise HTTPException(status_code=404, detail="Shortcode not found.")

    return {
        "original_url": entry["original_url"],
        "created_at": entry["created_at"].isoformat() + "Z",
        "expiry": entry["expires_at"].isoformat() + "Z",
        "clicks": entry["clicks"],
        "click_data": click_stats.get(shortcode, [])
    }


def generate_shortcode(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
