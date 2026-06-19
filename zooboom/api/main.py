import os
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api.auth import verify_init_data
from api.routers import user, animals, shop, farm

app = FastAPI(title="ZooBoom API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MINIAPP_PATH = Path(__file__).parent.parent / "MiniApp" / "index.html"

EXCLUDED_PATHS = {"/", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def telegram_auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path in EXCLUDED_PATHS or not path.startswith("/api/"):
        return await call_next(request)

    init_data = request.headers.get("X-Telegram-Init-Data", "")
    user_data = verify_init_data(init_data)
    if user_data is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=401,
            content={"detail": "احراز هویت ناموفق بود. لطفاً دوباره تلاش کنید."},
        )

    request.state.user = user_data
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
async def serve_miniapp():
    if not MINIAPP_PATH.exists():
        raise HTTPException(status_code=404, detail="فایل Mini App یافت نشد.")
    return HTMLResponse(content=MINIAPP_PATH.read_text(encoding="utf-8"))


app.include_router(user.router, prefix="/api/zoo")
app.include_router(animals.router, prefix="/api/zoo")
app.include_router(shop.router, prefix="/api/zoo")
app.include_router(farm.router, prefix="/api/zoo")
