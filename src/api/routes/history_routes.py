from fastapi import APIRouter, Depends, Request
from src.api.deps import get_history_service

router = APIRouter()

@router.get("/")
def get_history(
    request: Request,
    service = Depends(get_history_service)
):
    user = request.state.user
    return service.get_history(user.get("sub"))