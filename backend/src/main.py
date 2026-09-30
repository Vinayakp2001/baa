"""FastAPI application entry point."""

import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .core.logging import configure_logging, bind_pipeline_context, clear_pipeline_context, get_logger
from .api.businesses import router as businesses_router
from .api.misc import router as misc_router
from .enrichment.routes import router as enrichment_router
from .events.routes import router as events_router
from .ingestion.routes import router as ingestion_router
from .normalisation.routes import router as normalisation_router
from .quality.routes import router as quality_router
from .resolution.routes import router as resolution_router

# Configure structlog before the app processes any requests
configure_logging()

logger = get_logger(__name__)

app = FastAPI(
    title="Canada B2B Pipeline API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened per-env in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next) -> Response:
    """Bind a unique request_id to structlog context for every request."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    bind_pipeline_context(request_id=request_id)
    try:
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        clear_pipeline_context()


app.include_router(ingestion_router)
app.include_router(normalisation_router)
app.include_router(resolution_router)
app.include_router(events_router)
app.include_router(enrichment_router)
app.include_router(quality_router)
app.include_router(businesses_router)
app.include_router(misc_router)


@app.get("/healthz")
async def health() -> dict:
    logger.info("health_check")
    return {"status": "ok"}
