import os
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.core.settings import settings


@lru_cache
def get_vector_store() -> Chroma:
    # 한국어 일상어 질문("살 빼는 주사", "선크림 피부암")의 의미 매칭 품질을 위해 large 를 기본으로 쓴다.
    # ⚠️ 모델을 바꾸면 벡터 차원이 달라지므로 data/chroma(또는 ai_chroma_data 볼륨)를 비우고 다시 인제스트해야 한다.
    embeddings = OpenAIEmbeddings(
        model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-large"),
        api_key=settings.openai_api_key,
    )
    return Chroma(
        collection_name="archive_items",
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )
