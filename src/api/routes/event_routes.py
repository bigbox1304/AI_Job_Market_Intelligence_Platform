from typing import Any, Dict, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from src.api.deps import get_job_event_service


router = APIRouter()


class JobEventRequest(BaseModel):
    job_id: int = Field(..., gt=0)
    event_type: Literal["view", "save", "apply", "dismiss"]
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/job", status_code=status.HTTP_204_NO_CONTENT)
def record_job_event(
    payload: JobEventRequest,
    request: Request,
    service=Depends(get_job_event_service),
):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")

    try:
        service.record_event(
            user_email=user.get("sub"),
            job_id=payload.job_id,
            event_type=payload.event_type,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
