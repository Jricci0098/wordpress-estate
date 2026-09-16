from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_agent_auth
from app.db import get_db
from app.models import Agent
from app.schemas.inventory import InventoryPayload
from app.services.inventory import ingest_inventory

router = APIRouter(prefix="/api/v1")


@router.post("/heartbeat")
def heartbeat(agent: Agent = Depends(require_agent_auth("heartbeat"))) -> dict:
    return {"status": "ok", "agent_id": agent.id}


@router.post("/inventory", status_code=201)
def post_inventory(
    payload: InventoryPayload,
    x_request_id: str = Header(...),
    agent: Agent = Depends(require_agent_auth("inventory")),
    db: Session = Depends(get_db),
) -> dict:
    if payload.agent_id != agent.id:
        raise HTTPException(status_code=403, detail="agent_id does not match authenticated agent")

    if payload.request_id != x_request_id:
        raise HTTPException(
            status_code=400,
            detail="request_id in payload does not match X-Request-Id header",
        )

    sites = ingest_inventory(db, agent.id, payload)
    return {"sites_processed": len(sites)}
