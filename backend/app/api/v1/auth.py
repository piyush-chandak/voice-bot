from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from app.core import security

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user / technician."""
    auth_service = AuthService(db)
    user = await auth_service.register_user(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
        role=user_in.role,
    )
    return user


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate technician credentials and return JWT token."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(user_in.username, user_in.password)
    access_token = security.create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}
