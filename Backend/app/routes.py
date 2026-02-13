"""
API routes for store CRUD operations.
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.k8s_client import k8s_client
from app.models import Store, StoreStatus, User
from app.orchestrator import _get_namespace, orchestrator
from app.schemas import (
    HealthResponse,
    MessageResponse,
    StoreCreateRequest,
    StoreListResponse,
    StoreResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ───────────────── Health Check ─────────────────
@router.get("/health", response_model=HealthResponse)
async def health_check():
    # Try to reconnect if disconnected
    if not k8s_client.connected:
        k8s_client.connect()

    return HealthResponse(
        status="ok",
        kubernetes_connected=k8s_client.connected,
        version="1.0.0",
    )


# ───────────────── List Stores ─────────────────
@router.get("/stores", response_model=StoreListResponse)
async def list_stores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Store)
        .where(Store.user_id == current_user.id)
        .order_by(Store.created_at.desc())
    )
    stores = result.scalars().all()
    return StoreListResponse(
        stores=[StoreResponse.model_validate(s) for s in stores],
        total=len(stores),
    )


# ───────────────── Get Single Store ─────────────────
@router.get("/stores/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Store).where(Store.id == store_id, Store.user_id == current_user.id)
    )
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return StoreResponse.model_validate(store)


# ───────────────── Create Store ─────────────────
@router.post("/stores", response_model=StoreResponse, status_code=201)
async def create_store(
    req: StoreCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Guardrail: per-user max stores
    count_result = await db.execute(
        select(func.count(Store.id)).where(Store.user_id == current_user.id)
    )
    user_store_count = count_result.scalar()
    if user_store_count >= settings.MAX_STORES_PER_USER:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum number of stores per user ({settings.MAX_STORES_PER_USER}) reached",
        )

    # Idempotency: check if name already exists
    existing = await db.execute(select(Store).where(Store.name == req.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Store with name '{req.name}' already exists",
        )

    # Create store record
    namespace = _get_namespace(req.name)
    store = Store(
        name=req.name,
        store_type=req.store_type,
        status=StoreStatus.PROVISIONING,
        namespace=namespace,
        user_id=current_user.id,
    )
    db.add(store)
    await db.commit()
    await db.refresh(store)

    # Kick off provisioning in background
    background_tasks.add_task(orchestrator.create_store, store)

    logger.info(
        "Store %s creation initiated by user %s (type=%s)",
        store.name,
        current_user.email,
        store.store_type,
    )
    return StoreResponse.model_validate(store)


# ───────────────── Delete Store ─────────────────
@router.delete("/stores/{store_id}", response_model=MessageResponse)
async def delete_store(
    store_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Store).where(Store.id == store_id, Store.user_id == current_user.id)
    )
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    if store.status == StoreStatus.DELETING:
        raise HTTPException(status_code=409, detail="Store is already being deleted")

    # Mark as deleting
    store.status = StoreStatus.DELETING
    store.updated_at = datetime.now(UTC)
    await db.commit()

    # Kick off deletion in background
    background_tasks.add_task(orchestrator.delete_store, store)

    return MessageResponse(
        message=f"Store '{store.name}' deletion initiated",
        store_id=store.id,
    )


# ───────────────── Get Store Pods ─────────────────
@router.get("/stores/{store_id}/pods")
async def get_store_pods(
    store_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Store).where(Store.id == store_id, Store.user_id == current_user.id)
    )
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    pods = k8s_client.get_namespace_pods(store.namespace)
    return {"store_id": store.id, "namespace": store.namespace, "pods": pods}
