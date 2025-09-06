import os
from pydantic import BaseModel


class Settings(BaseModel):
    jwt_secret: str = os.getenv("JWT_SECRET", "changeme")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


settings = Settings()
