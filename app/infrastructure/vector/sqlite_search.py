import json
import sqlite3

from app.application.support.text import sanitize_text
from app.infrastructure.llm.embeddings import build_embeddings
from app.infrastructure.vector.cosine import cosine_similarity
from config.config import config


def sync_search_formatted(
    *,
    query: str,
    knowledge_base_id: str | None = None,
    top_k: int | None = None,
) -> str:
    """Sync RAG search for LangChain tools (agent runs in worker thread)."""
    configure = config()
    if not configure.rag.enabled:
        return "RAG is disabled."

    conn = sqlite3.connect(configure.storage.sqlite_file)
    conn.row_factory = sqlite3.Row
    try:
        workspace_id = configure.storage.default_workspace_id
        kb_id = knowledge_base_id
        if kb_id is None:
            row = conn.execute(
                """
                SELECT id FROM knowledge_bases
                WHERE workspace_id = ? AND name = ?
                ORDER BY updated_at DESC LIMIT 1
                """,
                (workspace_id, configure.rag.default_knowledge_base_name),
            ).fetchone()
            if row is None:
                return "No knowledge base indexed yet."
            kb_id = row["id"]

        rows = conn.execute(
            """
            SELECT c.content, c.embedding_json, c.document_id, d.title AS document_title
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.knowledge_base_id = ? AND c.workspace_id = ?
            """,
            (kb_id, workspace_id),
        ).fetchall()
        if not rows:
            return "No relevant passages found."

        query_vec = build_embeddings().embed_query(query.strip())
        hits: list[tuple[float, str, str]] = []
        for row in rows:
            embedding = json.loads(row["embedding_json"])
            score = cosine_similarity(query_vec, embedding)
            hits.append((score, row["document_title"], row["content"]))
        hits.sort(key=lambda item: item[0], reverse=True)

        limit = top_k or configure.rag.top_k
        selected = hits[:limit]
        if not selected:
            return "No relevant passages found."

        lines: list[str] = []
        for index, (score, title, content) in enumerate(selected, start=1):
            snippet = sanitize_text(content).replace("\n", " ")
            lines.append(f"[{index}] score={score:.3f} doc={title}\n{snippet}")
        return "\n\n".join(lines)
    finally:
        conn.close()
