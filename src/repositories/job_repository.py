#job_repository.py
from typing import List, Optional, Dict

class JobRepository:
    def __init__(self, conn):
        self.conn = conn

    # =========================================
    # 1. GET JOB BY ID
    # =========================================
    def get_by_id(self, job_id: int) -> Optional[Dict]:
        query = """
        SELECT
            j.job_id,
            j.job_title,
            j.industry,
            j.job_function,
            j.job_level,
            j.city,
            j.years_of_experience,
            j.created_on,
            j.expired_on,
            j.is_active,
            j.job_description,
            j.job_requirement,
            STRING_AGG(s.skill_name, ', ') AS skills
        FROM jobs j
        LEFT JOIN job_skills js ON j.job_id = js.job_id
        LEFT JOIN skills s ON js.skill_id = s.skill_id
        WHERE j.job_id = %s
          AND j.is_active = TRUE
          AND (j.expired_on IS NULL OR j.expired_on >= CURRENT_TIMESTAMP)
        GROUP BY j.job_id
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (job_id,))
            row = cur.fetchone()

        return self._map_row(cur, row)

    # =========================================
    # 2. SEARCH JOB (ILIKE)
    # =========================================
    def search(self, query_str: str, limit: int = 20) -> List[Dict]:
        query = """
        SELECT
            j.job_id,
            j.job_title,
            j.industry,
            j.job_function,
            j.job_level,
            j.city,
            j.years_of_experience,
            j.created_on,
            j.expired_on,
            j.is_active,
            STRING_AGG(s.skill_name, ', ') AS skills
        FROM jobs j
        LEFT JOIN job_skills js ON j.job_id = js.job_id
        LEFT JOIN skills s ON js.skill_id = s.skill_id
        WHERE j.is_active = TRUE
          AND (j.expired_on IS NULL OR j.expired_on >= CURRENT_TIMESTAMP)
          AND (
            j.job_title ILIKE %s OR
            j.job_requirement ILIKE %s
          )
        GROUP BY j.job_id
        ORDER BY j.job_id DESC
        LIMIT %s
        """

        like_query = f"%{query_str}%"

        with self.conn.cursor() as cur:
            cur.execute(query, (like_query, like_query, limit))
            rows = cur.fetchall()

            return [self._map_row(cur, row) for row in rows]

    # =========================================
    # 3. FILTER JOB
    # =========================================
    def filter(
        self,
        city: Optional[str] = None,
        level: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:

        conditions = [
            "j.is_active = TRUE",
            "(j.expired_on IS NULL OR j.expired_on >= CURRENT_TIMESTAMP)",
        ]
        params = []

        if city:
            conditions.append("j.city = %s")
            params.append(city)

        if level:
            conditions.append("j.job_level = %s")
            params.append(level)

        if industry:
            conditions.append("j.industry = %s")
            params.append(industry)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
        SELECT
            j.job_id,
            j.job_title,
            j.industry,
            j.job_function,
            j.job_level,
            j.city,
            j.years_of_experience,
            j.created_on,
            j.expired_on,
            j.is_active,
            STRING_AGG(s.skill_name, ', ') AS skills
        FROM jobs j
        LEFT JOIN job_skills js ON j.job_id = js.job_id
        LEFT JOIN skills s ON js.skill_id = s.skill_id
        {where_clause}
        GROUP BY j.job_id
        ORDER BY j.job_id DESC
        LIMIT %s
        """

        params.append(limit)

        with self.conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

            return [self._map_row(cur, row) for row in rows]

    # =========================================
    # 4. GET MULTIPLE JOBS (CHO RECOMMEND)
    # =========================================
    def get_jobs_by_ids(self, job_ids: List[int]) -> List[Dict]:
        if not job_ids:
            return []

        query = """
        SELECT
            j.job_id,
            j.job_title,
            j.industry,
            j.job_function,
            j.job_level,
            j.city,
            j.years_of_experience,
            j.created_on,
            j.expired_on,
            j.is_active,
            STRING_AGG(s.skill_name, ', ') AS skills
        FROM jobs j
        LEFT JOIN job_skills js ON j.job_id = js.job_id
        LEFT JOIN skills s ON js.skill_id = s.skill_id
        WHERE j.job_id = ANY(%s)
          AND j.is_active = TRUE
          AND (j.expired_on IS NULL OR j.expired_on >= CURRENT_TIMESTAMP)
        GROUP BY j.job_id
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (job_ids,))
            rows = cur.fetchall()

            return [self._map_row(cur, row) for row in rows]

    # =========================================
    # INTERNAL: MAP ROW → DICT
    # =========================================
    def _map_row(self, cur, row) -> Optional[Dict]:
        if row is None:
            return None

        columns = [desc[0] for desc in cur.description]

        return dict(zip(columns, row))
