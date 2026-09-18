from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ingest import router as ingest_router
from app.api.patients import router as patients_router
from app.api.relatives import router as relatives_router
from app.api.tasks import router as tasks_router
from auth.deps import auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nazorat")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NAZORAT FastAPI application starting up...")
    yield
    logger.info("NAZORAT FastAPI application shutting down...")


app = FastAPI(
    title="NAZORAT API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for Web Doctor (5173) and Web Relative (5174)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", tags=["ops"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Mount all routers
app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(patients_router)
app.include_router(tasks_router)
app.include_router(relatives_router)
