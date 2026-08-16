"""아카이브 인제스트 배치 스크립트.

실시간 요청 경로와 분리된 오프라인 작업이라 MySQL을 직접 읽는 게 허용된다
(docs/AI_SERVICE_CONTRACT.md 5번 참고). 관리자가 archive_items를 SQL로
직접 추가/수정한 뒤 이 스크립트를 수동 실행해서 벡터스토어를 갱신한다.

실행: python -m app.judgment.rag.ingest
"""

import mysql.connector

from app.core.settings import settings
from app.judgment.rag.vector_store import get_vector_store


def fetch_archive_items() -> list[dict]:
    conn = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
    )
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, target, effect, evidence_summary, category_id, trust_level FROM archive_items"
        )
        return cursor.fetchall()
    finally:
        conn.close()


def run() -> None:
    items = fetch_archive_items()
    store = get_vector_store()

    texts = [f"{item['target']} {item['effect']} {item['evidence_summary']}" for item in items]
    metadatas = [
        {
            "archive_item_id": item["id"],
            "category_id": item["category_id"],
            "trust_level": item["trust_level"],
        }
        for item in items
    ]
    ids = [str(item["id"]) for item in items]

    if not items:
        print("인제스트할 아카이브 항목이 없습니다.")
        return

    store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    print(f"인제스트 완료: {len(items)}건")


if __name__ == "__main__":
    run()
