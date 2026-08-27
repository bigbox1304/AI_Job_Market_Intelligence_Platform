import json
from datetime import datetime, timezone
from typing import Any, Dict

from src.core.database import get_db, release_db


def record_pipeline_task(
    run_id: str,
    dag_id: str,
    task_id: str,
    status: str,
    metrics: Dict[str, Any] | None = None,
) -> None:
    """Persist lightweight task lineage without requiring a separate tracking service."""
    conn = None
    try:
        conn = get_db()
        with conn.cursor() as cur:
            if status == "running":
                cur.execute(
                    """
                    INSERT INTO pipeline_runs(run_id, dag_id, task_id, status, metrics, started_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET status = EXCLUDED.status, metrics = EXCLUDED.metrics
                    """,
                    (run_id, dag_id, task_id, status, json.dumps(metrics or {}), datetime.now(timezone.utc)),
                )
            else:
                cur.execute(
                    """
                    UPDATE pipeline_runs
                    SET status = %s, metrics = %s, finished_at = %s
                    WHERE run_id = %s
                    """,
                    (status, json.dumps(metrics or {}), datetime.now(timezone.utc), run_id),
                )
            conn.commit()
    finally:
        if conn:
            release_db(conn)
