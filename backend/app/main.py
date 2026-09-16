from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, engine
from app.routers import agent as agent_router
from app.routers import catalog as catalog_router
from app.routers import health as health_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    _seed_agent_if_configured()
    yield


app = FastAPI(title="WordPress Estate API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router.router)
app.include_router(agent_router.router)
app.include_router(catalog_router.router)


def _seed_agent_if_configured() -> None:
    from sqlalchemy.orm import Session

    from app.auth import hash_secret
    from app.models import Agent

    if not settings.seed_agent_id or not settings.seed_agent_secret:
        return
    with Session(engine) as db:
        existing = db.get(Agent, settings.seed_agent_id)
        if existing is None:
            db.add(
                Agent(
                    id=settings.seed_agent_id,
                    secret_hash=hash_secret(settings.seed_agent_secret),
                )
            )
            db.commit()
