from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt
from src.core.security import SECRET_KEY, ALGORITHM


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        auth = request.headers.get("Authorization")

        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]

            try:
                payload = jwt.decode(
                    token,
                    SECRET_KEY,
                    algorithms=[ALGORITHM]
                )
                request.state.user = payload

            except Exception:
                request.state.user = None
        else:
            request.state.user = None

        response = await call_next(request)
        return response