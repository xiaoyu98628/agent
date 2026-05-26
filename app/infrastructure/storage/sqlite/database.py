import aiosqlite

_connection: aiosqlite.Connection | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    title TEXT,
    model_provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    temperature REAL,
    max_tokens INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conversations_workspace ON conversations(workspace_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at ASC);

CREATE TABLE IF NOT EXISTS knowledge_bases (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kb_workspace ON knowledge_bases(workspace_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    knowledge_base_id TEXT NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    workspace_id TEXT NOT NULL,
    title TEXT NOT NULL,
    source TEXT,
    status TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_kb ON documents(knowledge_base_id, created_at DESC);

CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    knowledge_base_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_kb ON document_chunks(knowledge_base_id, workspace_id);

CREATE TABLE IF NOT EXISTS memory_entries (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    target TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_workspace_target ON memory_entries(workspace_id, target, updated_at DESC);

CREATE TABLE IF NOT EXISTS gateway_bindings (
    platform TEXT NOT NULL,
    external_chat_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    conversation_id TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (platform, external_chat_id, workspace_id)
);
"""


async def init_db(sqlite_path: str) -> None:
    global _connection
    if _connection is not None:
        return
    _connection = await aiosqlite.connect(sqlite_path)
    _connection.row_factory = aiosqlite.Row
    await _connection.executescript(_SCHEMA)
    await _connection.commit()


async def close_db() -> None:
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None


async def get_connection() -> aiosqlite.Connection:
    if _connection is None:
        raise RuntimeError("数据库未初始化，请在应用 lifespan 中调用 init_db")
    return _connection
