from fastapi import APIRouter, Depends

from app.application.rag.service import RagService
from app.interfaces.http.deps.rag import get_rag_service
from app.interfaces.http.presenters.knowledge import to_document_response
from app.interfaces.http.schemas.responses.knowledge import DocumentResponse
from app.interfaces.http.support.response.json import JsonResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", summary="文档详情")
async def get_document(
    document_id: str,
    service: RagService = Depends(get_rag_service),
) -> JsonResponse[DocumentResponse]:
    document = await service.get_document(document_id)
    return JsonResponse.success(data=to_document_response(document))
