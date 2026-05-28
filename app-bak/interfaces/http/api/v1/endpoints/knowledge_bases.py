from fastapi import APIRouter, Depends

from app.application.rag.service import RagService
from app.interfaces.http.deps.rag import get_rag_service
from app.interfaces.http.presenters.knowledge import (
    to_document_response,
    to_knowledge_base_response,
    to_search_hit_response,
)
from app.interfaces.http.schemas.requests.knowledge import (
    CreateKnowledgeBaseRequest,
    IngestDocumentRequest,
    KnowledgeBaseListQuery,
    SearchKnowledgeRequest,
)
from app.interfaces.http.schemas.responses.knowledge import (
    DocumentResponse,
    KnowledgeBaseResponse,
    SearchKnowledgeResponse,
)
from app.interfaces.http.support.response.code.success_code import SuccessCode
from app.interfaces.http.support.response.json import JsonResponse

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post("", summary="创建知识库")
async def create_knowledge_base(
    body: CreateKnowledgeBaseRequest,
    service: RagService = Depends(get_rag_service),
) -> JsonResponse[KnowledgeBaseResponse]:
    kb = await service.create_knowledge_base(name=body.name, description=body.description)
    return JsonResponse.success(data=to_knowledge_base_response(kb), code=SuccessCode.SUCCESS_CREATED)


@router.get("", summary="知识库列表")
async def list_knowledge_bases(
    query: KnowledgeBaseListQuery = Depends(),
    service: RagService = Depends(get_rag_service),
) -> JsonResponse[list[KnowledgeBaseResponse]]:
    items = await service.list_knowledge_bases(limit=query.limit, offset=query.offset)
    return JsonResponse.success(data=[to_knowledge_base_response(item) for item in items])


@router.get("/{knowledge_base_id}", summary="知识库详情")
async def get_knowledge_base(
    knowledge_base_id: str,
    service: RagService = Depends(get_rag_service),
) -> JsonResponse[KnowledgeBaseResponse]:
    kb = await service.get_knowledge_base(knowledge_base_id)
    return JsonResponse.success(data=to_knowledge_base_response(kb))


@router.delete("/{knowledge_base_id}", summary="删除知识库")
async def delete_knowledge_base(
    knowledge_base_id: str,
    service: RagService = Depends(get_rag_service),
) -> JsonResponse[None]:
    await service.delete_knowledge_base(knowledge_base_id)
    return JsonResponse.success(data=None, message="deleted")


@router.post("/{knowledge_base_id}/documents", summary="入库文档")
async def ingest_document(
    knowledge_base_id: str,
    body: IngestDocumentRequest,
    service: RagService = Depends(get_rag_service),
) -> JsonResponse[DocumentResponse]:
    document = await service.ingest_document(
        knowledge_base_id=knowledge_base_id,
        title=body.title,
        content=body.content,
        file_path=body.file_path,
    )
    return JsonResponse.success(data=to_document_response(document), code=SuccessCode.SUCCESS_CREATED)


@router.post("/{knowledge_base_id}/search", summary="检索知识库")
async def search_knowledge_base(
    knowledge_base_id: str,
    body: SearchKnowledgeRequest,
    service: RagService = Depends(get_rag_service),
) -> JsonResponse[SearchKnowledgeResponse]:
    hits = await service.search(query=body.query, knowledge_base_id=knowledge_base_id, top_k=body.top_k)
    data = SearchKnowledgeResponse(
        query=body.query,
        hits=[to_search_hit_response(hit) for hit in hits],
    )
    return JsonResponse.success(data=data)
