from typing import List, Dict, Optional
import json
class SearchHistoryRepository:
    def __init__(self, conn):
        self.conn = conn

    def save(self, user_email: str, query: str, filters: dict):
        sql = """
        INSERT INTO search_history(user_email, query, filters)
        VALUES (%s, %s, %s)
        """

        with self.conn.cursor() as cur:
            cur.execute(sql, (user_email, query, json.dumps(filters)))
            self.conn.commit()

    def get_by_user(self, user_email: str, limit=10):

        sql = """
        SELECT query, filters, created_at
        FROM search_history
        WHERE user_email = %s
        ORDER BY created_at DESC
        LIMIT %s
        """

        with self.conn.cursor() as cur:
            cur.execute(sql, (user_email, limit))
            rows = cur.fetchall()

        return [
            {
                "query": r[0],
                "filters": r[1],
                "created_at": r[2]
            }
            for r in rows
        ]