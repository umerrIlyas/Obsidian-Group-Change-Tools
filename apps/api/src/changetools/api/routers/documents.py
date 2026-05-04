"""Document upload + listing endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from changetools.api.deps import (
    get_db,
    get_document_service,
    get_ingestion_service,
)
from changetools.api.schemas import DocumentOut, DocumentSummaryOut
from changetools.services.document_service import DocumentService
from changetools.services.ingestion_service import IngestionService

RAW_TEXT_EXCERPT_LEN = 1500

router = APIRouter(tags=["documents"])


@router.post(
    "/projects/{project_id}/documents",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DocumentSummaryOut,
)
async def upload_document(
    project_id: uuid.UUID,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
    ingestion: IngestionService = Depends(get_ingestion_service),
    session: AsyncSession = Depends(get_db),
) -> DocumentSummaryOut:
    data = await file.read()
    document = await service.upload(
        project_id=project_id,
        filename=file.filename or "upload.bin",
        content_type=file.content_type,
        data=data,
    )
    # FastAPI runs background tasks BEFORE the request-scoped session is committed
    # via the get_db generator's cleanup. Commit explicitly so the ingestion task
    # — which opens its own fresh session — can see the new row.
    await session.commit()
    background.add_task(ingestion.process, document.id)
    return DocumentSummaryOut.model_validate(document)


@router.get(
    "/projects/{project_id}/documents",
    response_model=list[DocumentSummaryOut],
)
async def list_documents(
    project_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentSummaryOut]:
    docs = await service.list_by_project(project_id)
    return [DocumentSummaryOut.model_validate(d) for d in docs]


@router.get(
    "/documents/{document_id}",
    response_model=DocumentOut,
)
async def get_document(
    document_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
) -> DocumentOut:
    doc = await service.get(document_id)
    return DocumentOut(
        **DocumentSummaryOut.model_validate(doc).model_dump(),
        raw_text_excerpt=(doc.raw_text or "")[:RAW_TEXT_EXCERPT_LEN] or None,
        meta=doc.meta,
    )
