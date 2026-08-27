"""Train the recommendation ranker from impression outcomes.

Usage inside the API container:
    python -m src.train.train_ranker
"""

import json
import os

from src.core.database import get_db, release_db
from src.ml.learning_ranker import LearningRanker


TRAINING_QUERY = """
SELECT
    i.features,
    CASE
        WHEN BOOL_OR(e.event_type IN ('save', 'apply')) THEN 1
        WHEN BOOL_OR(e.event_type = 'dismiss') THEN 0
        ELSE NULL
    END AS label
FROM recommendation_impressions i
LEFT JOIN user_job_events e
    ON e.user_email = i.user_email
   AND e.job_id = i.job_id
   AND e.created_at >= i.created_at
   AND e.created_at < i.created_at + INTERVAL '7 days'
WHERE i.user_email IS NOT NULL
GROUP BY i.impression_id, i.features
HAVING BOOL_OR(e.event_type IN ('save', 'apply'))
    OR BOOL_OR(e.event_type = 'dismiss')
"""


def load_training_rows():
    conn = None
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(TRAINING_QUERY)
            return [{"features": row[0] or {}, "label": row[1]} for row in cur.fetchall()]
    finally:
        if conn:
            release_db(conn)


def train():
    rows = load_training_rows()
    ranker = LearningRanker()
    weights = ranker.train_pairwise(rows)
    output = ranker.save(model_version=os.getenv("RECOMMENDATION_MODEL_VERSION", "learned-ranker-v1"))
    print(json.dumps({"rows": len(rows), "weights": weights, "output": str(output)}, indent=2))


if __name__ == "__main__":
    train()
