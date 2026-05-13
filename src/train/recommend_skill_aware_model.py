import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

index = faiss.read_index("skill_aware_job_index.faiss")

with open("skill_aware_metadata.pkl", "rb") as f:
    df = pickle.load(f)

model = SentenceTransformer("embedding_model")

def recommend_jobs(query, top_k=5):

    vector = model.encode([query], convert_to_numpy=True)

    faiss.normalize_L2(vector)

    scores, indices = index.search(vector, top_k)

    results = df.iloc[indices[0]].copy()

    results["score"] = scores[0]

    return results[
        ["job_id","job_title","industry","skills","score"]
    ]


query = "python data analyst sql"

print(recommend_jobs(query))