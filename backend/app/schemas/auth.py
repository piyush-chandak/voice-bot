from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])
    token_type: str = Field("bearer", examples=["bearer"])


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None
    user_id: int | None = None


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["tech_john"])
    password: str = Field(..., min_length=6, examples=["supersecretpwd"])


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["tech_john"])
    email: EmailStr = Field(..., examples=["john.doe@enterprise.com"])
    password: str = Field(..., min_length=6, examples=["supersecretpwd"])
    role: str = Field("Technician", examples=["Technician", "Supervisor", "Admin"])


class UserResponse(BaseModel):
    id: int = Field(..., examples=[1])
    username: str = Field(..., examples=["tech_john"])
    email: EmailStr = Field(..., examples=["john.doe@enterprise.com"])
    role: str = Field(..., examples=["Technician"])
    is_active: bool = Field(..., examples=[True])

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "tech_john",
                "email": "john.doe@enterprise.com",
                "role": "Technician",
                "is_active": True
            }
        }
