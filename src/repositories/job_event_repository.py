import json
from typing import Any, Dict, List, Sequence


class JobEventRepository:
    def __init__(self, conn):
        self.conn = conn

    def record(self, user_email: str, job_id: int, event_type: str, metadata: Dict[str, Any] | None = None):
        sql = """
        INSERT INTO user_job_events(user_email, job_id, event_type, metadata)
        VALUES (%s, %s, %s, %s)
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (user_email, job_id, event_type, json.dumps(metadata or {})))
            self.conn.commit()

    def get_by_user(self, user_email: str, limit: int = 200) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            e.event_type,
            e.job_id,
            e.metadata,
            e.created_at,
            j.job_title,
            j.industry,
            j.job_function,
            j.job_level,
            j.city,
            STRING_AGG(s.skill_name, ', ') AS skills
        FROM user_job_events e
        LEFT JOIN jobs j ON j.job_id = e.job_id
        LEFT JOIN job_skills js ON js.job_id = e.job_id
        LEFT JOIN skills s ON s.skill_id = js.skill_id
        WHERE e.user_email = %s
        GROUP BY e.event_id, j.job_title, j.industry, j.job_function, j.job_level, j.city
        ORDER BY e.created_at DESC
        LIMIT %s
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (user_email, limit))
            rows = cur.fetchall()

        return [
            {
                "event_type": row[0],
                "job_id": row[1],
                "metadata": row[2],
                "created_at": row[3],
                "job_title": row[4],
                "industry": row[5],
                "job_function": row[6],
                "job_level": row[7],
                "city": row[8],
                "skills": row[9],
            }
            for row in rows
        ]

    def record_impressions(
        self,
        request_id: str,
        user_email: str | None,
        query_text: str,
        jobs: Sequence[Dict[str, Any]],
        model_version: str,
    ) -> None:
        sql = """
        INSERT INTO recommendation_impressions
            (request_id, user_email, query_text, job_id, rank_position, recommendation_score, features, model_version)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        rows = [
            (
                request_id,
                user_email,
                query_text,
                job.get("job_id"),
                position,
                job.get("recommendation_score"),
                json.dumps(job.get("recommendation_features", {})),
                model_version,
            )
            for position, job in enumerate(jobs, start=1)
            if job.get("job_id") is not None
        ]
        if not rows:
            return
        with self.conn.cursor() as cur:
            cur.executemany(sql, rows)
            self.conn.commit()
