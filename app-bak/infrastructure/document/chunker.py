from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.config import config


def split_text(text: str) -> list[str]:
    configure = config()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=configure.rag.chunk_size,
        chunk_overlap=configure.rag.chunk_overlap,
        length_function=len,
    )
    chunks = splitter.split_text(text.strip())
    return [chunk for chunk in chunks if chunk.strip()]
