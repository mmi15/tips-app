from pydantic import BaseModel, EmailStr, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class RegisterInput(BaseModel):
    email: EmailStr
    password: str


class MeRead(BaseModel):
    id: int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)
