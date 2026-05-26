import asyncio
from datetime import UTC, datetime

from app.application.support.ids import new_id
from app.application.support.text import sanitize_text
from app.domain.knowledge.entity import Document, DocumentChunk, KnowledgeBase, SearchHit
from app.domain.knowledge.exceptions import DocumentNotFoundError, KnowledgeBaseNotFoundError
from app.domain.knowledge.repository import RagRepository
from app.infrastructure.document.chunker import split_text
from app.infrastructure.document.loaders import load_text_from_source
from app.infrastructure.llm.embeddings import build_embeddings
from app.infrastructure.storage.sqlite.rag_repository import SqliteRagRepository
from app.infrastructure.vector.cosine import cosine_similarity
from config.config import config


def _now() -> datetime:
    return datetime.now(UTC)


class RagService:
    def __init__(self, repository: RagRepository | None = None) -> None:
        self._repository = repository or SqliteRagRepository()

    @property
    def workspace_id(self) -> str:
        return config().storage.default_workspace_id

    async def create_knowledge_base(self, *, name: str, description: str | None = None) -> KnowledgeBase:
        now = _now()
        kb = KnowledgeBase(
            id=new_id(),
            workspace_id=self.workspace_id,
            name=name.strip(),
            description=description,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.create_knowledge_base(kb)

    async def get_knowledge_base(self, kb_id: str) -> KnowledgeBase:
        kb = await self._repository.get_knowledge_base(kb_id=kb_id, workspace_id=self.workspace_id)
        if kb is None:
            raise KnowledgeBaseNotFoundError(f"知识库不存在: {kb_id}")
        return kb

    async def list_knowledge_bases(self, *, limit: int = 50, offset: int = 0) -> list[KnowledgeBase]:
        return await self._repository.list_knowledge_bases(
            workspace_id=self.workspace_id,
            limit=limit,
            offset=offset,
        )

    async def delete_knowledge_base(self, kb_id: str) -> None:
        deleted = await self._repository.delete_knowledge_base(kb_id=kb_id, workspace_id=self.workspace_id)
        if not deleted:
            raise KnowledgeBaseNotFoundError(f"知识库不存在: {kb_id}")

    async def ensure_default_knowledge_base(self) -> KnowledgeBase:
        configure = config()
        name = configure.rag.default_knowledge_base_name
        items = await self.list_knowledge_bases(limit=100, offset=0)
        for item in items:
            if item.name == name:
                return item
        return await self.create_knowledge_base(name=name, description="Default knowledge base")

    async def ingest_document(
        self,
        *,
        knowledge_base_id: str,
        title: str,
        content: str | None = None,
        file_path: str | None = None,
    ) -> Document:
        await self.get_knowledge_base(knowledge_base_id)
        text, source = load_text_from_source(content=content, file_path=file_path)
        now = _now()
        document = Document(
            id=new_id(),
            knowledge_base_id=knowledge_base_id,
            workspace_id=self.workspace_id,
            title=title.strip() or "untitled",
            source=source,
            status="processing",
            chunk_count=0,
            created_at=now,
            updated_at=now,
        )
        await self._repository.create_document(document)

        try:
            pieces = split_text(text)
            if not pieces:
                raise ValueError("Document is empty after splitting")

            embeddings = await asyncio.to_thread(self._embed_texts, pieces)
            chunks = self._build_chunks(document=document, pieces=pieces, embeddings=embeddings)
            await self._repository.add_chunks(chunks)
            await self._repository.update_document_status(
                document_id=document.id,
                workspace_id=self.workspace_id,
                status="ready",
                chunk_count=len(chunks),
            )
            return Document(
                id=document.id,
                knowledge_base_id=document.knowledge_base_id,
                workspace_id=document.workspace_id,
                title=document.title,
                source=document.source,
                status="ready",
                chunk_count=len(chunks),
                created_at=document.created_at,
                updated_at=_now(),
            )
        except Exception:
            await self._repository.update_document_status(
                document_id=document.id,
                workspace_id=self.workspace_id,
                status="failed",
                chunk_count=0,
            )
            raise

    async def get_document(self, document_id: str) -> Document:
        document = await self._repository.get_document(document_id=document_id, workspace_id=self.workspace_id)
        if document is None:
            raise DocumentNotFoundError(f"文档不存在: {document_id}")
        return document

    async def search(
        self,
        *,
        query: str,
        knowledge_base_id: str | None = None,
        top_k: int | None = None,
    ) -> list[SearchHit]:
        configure = config()
        if not configure.rag.enabled:
            return []

        kb_id = knowledge_base_id
        if kb_id is None:
            kb = await self.ensure_default_knowledge_base()
            kb_id = kb.id
        else:
            await self.get_knowledge_base(kb_id)

        chunks = await self._repository.list_chunks_for_kb(
            knowledge_base_id=kb_id,
            workspace_id=self.workspace_id,
        )
        if not chunks:
            return []

        query_vec = (await asyncio.to_thread(self._embed_texts, [query.strip()]))[0]
        document_titles = {doc.id: doc.title for doc in await self._list_documents_for_kb(kb_id)}

        hits: list[SearchHit] = []
        for chunk in chunks:
            score = cosine_similarity(query_vec, chunk.embedding)
            hits.append(
                SearchHit(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=document_titles.get(chunk.document_id, "unknown"),
                    content=chunk.content,
                    score=score,
                )
            )
        hits.sort(key=lambda item: item.score, reverse=True)
        limit = top_k or configure.rag.top_k
        return hits[:limit]

    async def search_formatted(
        self,
        *,
        query: str,
        knowledge_base_id: str | None = None,
        top_k: int | None = None,
    ) -> str:
        hits = await self.search(query=query, knowledge_base_id=knowledge_base_id, top_k=top_k)
        if not hits:
            return "No relevant passages found."
        lines: list[str] = []
        for index, hit in enumerate(hits, start=1):
            snippet = sanitize_text(hit.content).replace("\n", " ")
            lines.append(f"[{index}] score={hit.score:.3f} doc={hit.document_title}\n{snippet}")
        return "\n\n".join(lines)

    async def _list_documents_for_kb(self, kb_id: str) -> list[Document]:
        chunks = await self._repository.list_chunks_for_kb(
            knowledge_base_id=kb_id,
            workspace_id=self.workspace_id,
        )
        seen: set[str] = set()
        documents: list[Document] = []
        for chunk in chunks:
            if chunk.document_id in seen:
                continue
            seen.add(chunk.document_id)
            document = await self._repository.get_document(
                document_id=chunk.document_id,
                workspace_id=self.workspace_id,
            )
            if document:
                documents.append(document)
        return documents

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = build_embeddings()
        return model.embed_documents(texts)

    def _build_chunks(
        self,
        *,
        document: Document,
        pieces: list[str],
        embeddings: list[list[float]],
    ) -> list[DocumentChunk]:
        now = _now()
        chunks: list[DocumentChunk] = []
        for index, (piece, embedding) in enumerate(zip(pieces, embeddings, strict=True)):
            chunks.append(
                DocumentChunk(
                    id=new_id(),
                    document_id=document.id,
                    knowledge_base_id=document.knowledge_base_id,
                    workspace_id=document.workspace_id,
                    chunk_index=index,
                    content=sanitize_text(piece),
                    embedding=embedding,
                    created_at=now,
                )
            )
        return chunks
