"""Shared plumbing for the report route modules — the injectable service and
the two helpers every PDF route needs."""

from typing import Annotated

from fastapi import Depends, Response
from sqlalchemy import select

from ovejitas.core.deps import DBSession
from ovejitas.core.errors import NotFoundError
from ovejitas.features.farm.models import Farm
from ovejitas.features.report.service import ReportService


def get_report_service(db: DBSession) -> ReportService:
    return ReportService(db)


ReportSvc = Annotated[ReportService, Depends(get_report_service)]


async def farm_name(db: DBSession, farm_id: int) -> str:
    name = (await db.execute(select(Farm.name).where(Farm.id == farm_id))).scalar_one_or_none()
    if name is None:
        raise NotFoundError("Farm not found")
    return name


def pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
