# encoding: utf-8
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .connection import connection
from .routes import catalog, market, misc, stock


@asynccontextmanager
async def lifespan(app):
    yield
    connection.close()


app = FastAPI(title="THSDK API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router)
app.include_router(stock.router)
app.include_router(catalog.router)
app.include_router(misc.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
