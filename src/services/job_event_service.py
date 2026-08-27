from typing import Any, Dict, List, Sequence


ALLOWED_EVENTS = {"view", "save", "apply", "dismiss"}


class JobEventService:
    def __init__(self, repo):
        self.repo = repo

    def record_event(
        self,
        user_email: str,
        job_id: int,
        event_type: str,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        if event_type not in ALLOWED_EVENTS:
            raise ValueError(f"Unsupported event type: {event_type}")
        self.repo.record(user_email, job_id, event_type, metadata)

    def get_events(self, user_email: str, limit: int = 200) -> List[Dict[str, Any]]:
        return self.repo.get_by_user(user_email, limit)

    def record_impressions(
        self,
        request_id: str,
        user_email: str | None,
        query_text: str,
        jobs: Sequence[Dict[str, Any]],
        model_version: str = "hybrid-v1",
    ) -> None:
        self.repo.record_impressions(request_id, user_email, query_text, jobs, model_version)
