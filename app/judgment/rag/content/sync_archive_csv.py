"""아카이브 콘텐츠 CSV를 MySQL archive_items에 그대로 동기화한다.

내용 채우는 사람은 SQL을 몰라도 되게, 이 폴더의 archive_seed.csv(엑셀/구글시트로
다뤄도 됨)에 행만 추가/수정하면 이 스크립트가 DB에 직접 반영해준다.
R-TUSYUO 원칙(관리자 API 없이 SQL 직접 관리)은 그대로 지킨다 — 이건 "SQL 작성 +
실행을 대신 해주는 도구"지 API가 아니다. 그리고 mysql_user는 반드시
archive_items만 다룰 수 있는 최소권한 계정을 써야 한다(task #12 참고, 지금은
settings.mysql_user가 임시로 앱 계정과 같음 — 분리되면 여기 값만 바꾸면 됨).

동작: target+effect가 이미 있으면 UPDATE(내용 갱신), 없으면 INSERT.
      몇 번을 다시 실행해도 중복이 안 생긴다(idempotent).

사용법:
    python -m app.judgment.rag.content.sync_archive_csv
"""

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import mysql.connector

from app.core.settings import settings

CSV_PATH = Path(__file__).parent / "archive_seed.csv"


def collect_sources(row: dict) -> list[dict]:
    sources = []
    n = 1
    while f"source{n}_title" in row:
        title = row.get(f"source{n}_title", "").strip()
        if title:
            sources.append({
                "title": title,
                "url": row.get(f"source{n}_url", "").strip(),
                "publisher": row.get(f"source{n}_publisher", "").strip(),
                "type": row.get(f"source{n}_type", "").strip(),
            })
        n += 1
    return sources


def load_rows() -> list[dict]:
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        return [row for row in csv.DictReader(f) if row.get("target", "").strip()]


def sync() -> None:
    conn = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
    )
    created = updated = 0
    try:
        cursor = conn.cursor()
        for row in load_rows():
            import json as _json
            target = row["target"].strip()
            effect = row["effect"].strip()
            condition_scope = row.get("condition_scope", "").strip() or None
            sources_json = _json.dumps(collect_sources(row), ensure_ascii=False)

            cursor.execute(
                "SELECT id FROM archive_items WHERE target = %s AND effect = %s",
                (target, effect),
            )
            existing = cursor.fetchone()

            params = (
                condition_scope,
                int(row["category_id"]),
                row["trust_level"].strip(),
                row.get("evidence_source_type", "").strip() or None,
                sources_json,
                row["evidence_summary"].strip(),
            )

            if existing:
                cursor.execute(
                    """UPDATE archive_items SET
                        condition_scope = %s, category_id = %s, trust_level = %s,
                        evidence_source_type = %s, evidence_sources_json = %s, evidence_summary = %s
                       WHERE id = %s""",
                    params + (existing[0],),
                )
                updated += 1
            else:
                cursor.execute(
                    """INSERT INTO archive_items
                        (target, effect, condition_scope, category_id, trust_level,
                         evidence_source_type, evidence_sources_json, evidence_summary, version, managed_by)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'v1', 'csv-sync')""",
                    (target, effect) + params,
                )
                created += 1

        conn.commit()
        print(f"완료: 신규 {created}건, 갱신 {updated}건")
    finally:
        conn.close()


if __name__ == "__main__":
    sync()
