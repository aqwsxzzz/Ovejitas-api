from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from ovejitas.core.deps import DBSession
from ovejitas.core.errors import UnauthorizedError
from ovejitas.core.security import decode_token
from ovejitas.features.user.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: DBSession,
) -> User:
    if not token:
        raise UnauthorizedError()
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise UnauthorizedError("Invalid token") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    user = await db.get(User, int(payload["sub"]))
    if user is None:
        raise UnauthorizedError("User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
