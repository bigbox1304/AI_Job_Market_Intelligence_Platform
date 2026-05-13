from fastapi import APIRouter, Request
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
import os
from src.core.security import create_access_token

router = APIRouter()

oauth = OAuth()

oauth.register(
    name="google",
    client_id= os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request):

    token = await oauth.google.authorize_access_token(request)
    user = token["userinfo"]

    email = user["email"]
    name = user["name"]

    # tạo JWT nội bộ
    jwt_token = create_access_token({
        "sub": email,
        "name": name
    })

    return RedirectResponse(
    url=f"http://localhost:8501/?token={jwt_token}&name={name}"
    )