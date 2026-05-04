"""Retrieval debug endpoint — used by the frontend Retrieval Debug page in Phase 2.

Phase 4 layers the agent on top of this; the endpoint stays as a useful dev tool.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from changetools.api.deps import get_retrieval_service
from changetools.api.schemas import RetrievedHit, RetrieveIn, RetrieveOut
from changetools.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/projects", tags=["retrieval"])


@router.post(
    "/{project_id}/retrieve",
    response_model=RetrieveOut,
)
async def retrieve(
    project_id: uuid.UUID,
    body: RetrieveIn,
    service: RetrievalService = Depends(get_retrieval_service),
) -> RetrieveOut:
    hits = await service.retrieve(project_id=project_id, query=body.query, top_k=body.top_k)
    return RetrieveOut(
        query=body.query,
        hits=[
            RetrievedHit(
                chunk_id=hit.chunk.id,
                document_id=hit.chunk.document_id,
                document_filename=hit.document_filename,
                document_kind=hit.document_kind,
                score=hit.score,
                text=hit.chunk.text,
                meta=hit.chunk.meta,
            )
            for hit in hits
        ],
    )
