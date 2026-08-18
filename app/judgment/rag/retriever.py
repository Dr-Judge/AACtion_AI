from app.judgment.rag.vector_store import get_vector_store


def search_archive(query: str, category_id: int | None = None, k: int = 5) -> list[dict]:
    store = get_vector_store()
    filter_ = {"category_id": category_id} if category_id is not None else None
    results = store.similarity_search(query, k=k, filter=filter_)
    return [{"content": doc.page_content, "metadata": doc.metadata} for doc in results]
