from pydantic import BaseModel, EmailStr, Field , ConfigDict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut


class AccessTokenOut(BaseModel):
    access_token: str