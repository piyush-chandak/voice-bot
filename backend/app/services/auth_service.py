from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.user import User
from app.core import security
from app.core.exceptions import AuthenticationException


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, username: str, password: str) -> User:
        result = await self.db.execute(select(User).filter(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            raise AuthenticationException("Invalid username or password")
        if not security.verify_password(password, user.hashed_password):
            raise AuthenticationException("Invalid username or password")
        if not user.is_active:
            raise AuthenticationException("User account is disabled")
        return user

    async def register_user(
        self, username: str, email: str, password: str, role: str = "Technician"
    ) -> User:
        # Check if user already exists
        exist_check = await self.db.execute(
            select(User).filter((User.username == username) | (User.email == email))
        )
        if exist_check.scalar_one_or_none():
            raise AuthenticationException("Username or email already registered")

        hashed_pwd = security.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_pwd,
            role=role,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        return user
