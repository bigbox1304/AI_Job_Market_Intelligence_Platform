import os
import pickle
from datetime import datetime
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.core.database import get_db, release_db

MODEL_DIR = "data/models"
os.makedirs(MODEL_DIR, exist_ok=True)

def train_embeddings():
    # ==============================
    # 1. LOAD DATA FROM DATABASE
    # ==============================
    query = """
    SELECT
        j.job_id,
        j.job_title,
        j.industry,
        j.job_function,
        j.job_group,
        j.job_level,
        j.city,
        j.job_description,
        j.job_requirement,
        j.years_of_experience,
        j.created_on,
        j.expired_on,
        STRING_AGG(s.skill_name, ' ') AS skills
    FROM jobs j
    LEFT JOIN job_skills js ON j.job_id = js.job_id
    LEFT JOIN skills s ON js.skill_id = s.skill_id
    GROUP BY j.job_id
    """

    conn = None
    try:
        conn = get_db()
        df = pd.read_sql(query, conn)
        print("Jobs loaded:", len(df))
    finally:
        if conn:
            release_db(conn)

    # ==============================
    # 2. CLEAN DATA
    # ==============================
    df = df.fillna("")
    df["skills"] = df["skills"].astype(str)
    df["job_group"] = df["job_group"].astype(str)
    df["city"] = df["city"].astype(str)
    df["created_on"] = pd.to_datetime(df["created_on"], errors="coerce")

    # ==============================
    # 3. BUILD TEXT + SKILL FEATURES
    # ==============================
    df["text_feature"] = (
        df["job_title"] + " " +
        df["industry"] + " " +
        df["job_function"] + " " +
        df["job_level"] + " " +
        df["job_requirement"] + " " +
        df["job_description"] + " " +
        df["city"] + " " +
        df["job_group"]
    )
    df["skill_feature"] = df["skills"]

    text_list = df["text_feature"].tolist()
    skill_list = df["skill_feature"].tolist()

    # ==============================
    # 4. LOAD EMBEDDING MODEL
    # ==============================
    print("Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # ==============================
    # 5. CREATE TEXT EMBEDDING
    # ==============================
    print("Encoding text features...")
    text_embeddings = model.encode(
        text_list,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # ==============================
    # 6. CREATE SKILL EMBEDDING
    # ==============================
    print("Encoding skill features...")
    skill_embeddings = model.encode(
        skill_list,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # ==============================
    # 7. APPLY TIME WEIGHTING (CREATED_ON)
    # ==============================
    print("Applying time weighting...")
    now_ts = datetime.utcnow().timestamp()
    created_ts = df["created_on"].apply(lambda x: x.timestamp() if pd.notnull(x) else now_ts)
    # weight = exp(-alpha * age_days)
    alpha = 0.00001  # small decay
    age_seconds = now_ts - created_ts
    time_weights = np.exp(-alpha * age_seconds).values
    time_weights = time_weights[:, np.newaxis]  # reshape to broadcast

    # ==============================
    # 8. COMBINE EMBEDDINGS
    # ==============================
    print("Combining embeddings (text + skills + time)...")
    final_embeddings = 0.7 * text_embeddings + 0.3 * skill_embeddings

    # FAISS requires float32 contiguous array
    final_embeddings = np.ascontiguousarray(final_embeddings.astype("float32"))

    faiss.normalize_L2(final_embeddings)
    print("Final embedding shape:", final_embeddings.shape)

    # ==============================
    # 9. BUILD FAISS INDEX
    # ==============================
    dimension = final_embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(final_embeddings)
    print("FAISS index size:", index.ntotal)

    # ==============================
    # 10. SAVE MODEL
    # ==============================
    print("Saving models...")
    faiss.write_index(
        index,
        os.path.join(MODEL_DIR, "skill_aware_job_index.faiss")
    )

    with open(os.path.join(MODEL_DIR, "skill_aware_metadata.pkl"), "wb") as f:
        pickle.dump(df, f)

    model.save(os.path.join(MODEL_DIR, "embedding_model"))
    print("Training finished.")

# ==============================
# ENTRYPOINT (for Airflow)
# ==============================
if __name__ == "__main__":
    train_embeddings()