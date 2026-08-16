from app.judgment.rag.vector_store import get_vector_store

# TODO: category_id 기반 메타데이터 필터링 추가 (지금은 미구현)


def search_archive(query: str, category_id: int | None = None, k: int = 5) -> list[dict]:
    store = get_vector_store()
    results = store.similarity_search(query, k=k)
    return [{"content": doc.page_content, "metadata": doc.metadata} for doc in results]
