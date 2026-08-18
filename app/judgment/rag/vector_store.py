from functools import lru_cache

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.core.settings import settings


@lru_cache
def get_vector_store() -> Chroma:
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.openai_api_key,
    )
    return Chroma(
        collection_name="archive_items",
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )
