from typing import Annotated, List
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.exceptions import AuthenticationException, ForbiddenException
from app.database.models.user import User
from app.database.session import get_db

security_scheme = HTTPBearer()


async def get_current_user(
    token_credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    token = token_credentials.credentials
    payload = security.decode_access_token(token)
    if not payload:
        raise AuthenticationException("Could not validate credentials")
    
    username: str | None = payload.get("sub")
    user_id: int | None = payload.get("user_id")
    if username is None or user_id is None:
        raise AuthenticationException("Invalid token payload")

    # Fetch user from DB
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationException("User not found")
    if not user.is_active:
        raise AuthenticationException("Inactive user account")
    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenException(
                f"User role {current_user.role} does not have required permissions"
            )
        return current_user
