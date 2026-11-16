"""아카이브 인제스트 배치 스크립트.

실시간 요청 경로와 분리된 오프라인 작업이라 MySQL을 직접 읽는 게 허용된다
(docs/AI_SERVICE_CONTRACT.md 5번 참고). 관리자가 archive_items를 SQL로
직접 추가/수정한 뒤 이 스크립트를 수동 실행해서 벡터스토어를 갱신한다.

실행: python -m app.judgment.rag.ingest
"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

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
            """SELECT id, target, effect, evidence_summary, category_id, trust_level,
                      evidence_source_type, evidence_sources_json
               FROM archive_items"""
        )
        return cursor.fetchall()
    finally:
        conn.close()


def _sources_json(raw) -> str:
    if isinstance(raw, (list, dict)):
        return json.dumps(raw, ensure_ascii=False)
    return raw or "[]"


def run() -> None:
    items = fetch_archive_items()
    store = get_vector_store()

    # 대상·효과(사람들이 검색에 쓰는 이름)를 요약보다 앞서 두 번 넣어, 긴 요약 본문에 묻혀
    # 짧은 일상어 질문("위고비 살 빠지나요")이 못 찾는 일을 줄인다.
    texts = [
        f"{item['target']} {item['effect']}\n{item['target']}: {item['effect']}\n{item['evidence_summary']}"
        for item in items
    ]
    metadatas = [
        {
            "archive_item_id": item["id"],
            "target": item["target"],
            "effect": item["effect"],
            "category_id": item["category_id"],
            "trust_level": item["trust_level"],
            "evidence_source_type": item.get("evidence_source_type") or "",
            "sources_json": _sources_json(item.get("evidence_sources_json")),
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
