# faiss_service.py
import faiss
import pickle
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

FAISS_PATH = os.path.join(BASE_DIR, "data/models/skill_aware_job_index.faiss")
META_PATH = os.path.join(BASE_DIR, "data/models/skill_aware_metadata.pkl")


class FaissService:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaissService, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.index = faiss.read_index(FAISS_PATH)

        with open(META_PATH, "rb") as f:
            self.metadata = pickle.load(f)

        self.job_ids = self.metadata["job_id"].tolist()

        self.job_id_to_index = {
            job_id: idx for idx, job_id in enumerate(self.job_ids)
        }

    # =========================================
    # SEARCH
    # =========================================
    def search(self, vector, top_k=10):
        vector = np.array([vector]).astype("float32")
        scores, indices = self.index.search(vector, top_k)
        return scores[0], indices[0]

    # =========================================
    # GET JOB IDS
    # =========================================
    def get_job_ids(self, indices):
        return [
            self.job_ids[i]
            for i in indices
            if 0 <= i < len(self.job_ids)
        ]

    # =========================================
    # GET VECTOR BY JOB ID
    # =========================================
    def get_vector_by_job_id(self, job_id: int):
        idx = self.job_id_to_index.get(job_id)

        if idx is None:
            return None

        return self.index.reconstruct(idx)