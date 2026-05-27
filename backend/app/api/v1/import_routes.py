"""Rotas de import CSV bulk e download de templates (D-23–D-26)."""
from __future__ import annotations

from enum import Enum
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.services import import_service

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "import_templates"


class ImportEntity(str, Enum):
    COST_CENTERS = "cost-centers"
    DEPARTMENTS = "departments"
    USERS = "users"
    PRINTERS = "printers"


_TEMPLATE_FILES: dict[ImportEntity, str] = {
    ImportEntity.COST_CENTERS: "cost_centers.csv",
    ImportEntity.DEPARTMENTS: "departments.csv",
    ImportEntity.USERS: "users.csv",
    ImportEntity.PRINTERS: "printers.csv",
}


class ImportLineErrorRead(BaseModel):
    line: int
    message: str


class ImportResultRead(BaseModel):
    total: int
    created: int
    updated: int
    skipped: int
    errors: list[ImportLineErrorRead]


@router.get("/templates/{entity}")
def download_template(entity: ImportEntity) -> FileResponse:
    filename = _TEMPLATE_FILES[entity]
    path = TEMPLATES_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="template not found")
    return FileResponse(
        path,
        media_type="text/csv",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{entity}", response_model=ImportResultRead)
async def import_csv_endpoint(
    entity: ImportEntity,
    file: UploadFile = File(...),
    strict: bool = Query(False, description="All-or-nothing; rollback on any error"),
    db: Session = Depends(get_db_dep),
) -> ImportResultRead:
    content = await file.read()
    if len(content) > import_service.MAX_IMPORT_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede limite de {import_service.MAX_IMPORT_BYTES // (1024 * 1024)}MB",
        )
    result = import_service.import_csv(db, entity.value, content, strict=strict)
    return ImportResultRead(
        total=result.total,
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        errors=[ImportLineErrorRead(line=e.line, message=e.message) for e in result.errors],
    )
