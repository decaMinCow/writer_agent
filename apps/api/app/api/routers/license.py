from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import get_db_session
from app.schemas.license import LicenseActivateRequest, LicenseStatusResponse
from app.services.license_store import (
    clear_license_record,
    get_machine_code,
    license_status,
    store_license_record,
    validate_license_code,
)

router = APIRouter(prefix="/api/license", tags=["license"])


def _settings_from_request(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        raise HTTPException(status_code=500, detail="settings_not_initialized")
    return settings


@router.get("/machine-code", response_model=LicenseStatusResponse)
async def get_machine_code_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> LicenseStatusResponse:
    settings = _settings_from_request(request)
    status = await license_status(session=session, settings=settings)
    return LicenseStatusResponse(**status)


@router.get("/status", response_model=LicenseStatusResponse)
async def get_license_status_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> LicenseStatusResponse:
    settings = _settings_from_request(request)
    status = await license_status(session=session, settings=settings)
    return LicenseStatusResponse(**status)


@router.post("/activate", response_model=LicenseStatusResponse)
async def activate_license_endpoint(
    payload: LicenseActivateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> LicenseStatusResponse:
    settings = _settings_from_request(request)
    machine_code = get_machine_code(settings=settings)
    try:
        payload_data = validate_license_code(
            license_code=payload.license_code,
            machine_code=machine_code,
            settings=settings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await store_license_record(
        session=session,
        record={
            "license_code": payload.license_code,
            "payload": payload_data,
        },
    )
    status = await license_status(session=session, settings=settings)
    return LicenseStatusResponse(**status)


@router.post("/clear", response_model=LicenseStatusResponse)
async def clear_license_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> LicenseStatusResponse:
    settings = _settings_from_request(request)
    await clear_license_record(session=session)
    status = await license_status(session=session, settings=settings)
    return LicenseStatusResponse(**status)
