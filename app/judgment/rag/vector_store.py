from functools import lru_cache

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.settings import settings


@lru_cache
def get_vector_store() -> Chroma:
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.gemini_api_key,
    )
    return Chroma(
        collection_name="archive_items",
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )
