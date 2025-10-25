import os
from pydantic import BaseModel


# Application configuration settings (loaded from environment variables)
class Settings(BaseModel):
    # Secret key used to sign JWT tokens
    jwt_secret: str = os.getenv("JWT_SECRET", "changeme")

    # Algorithm used for JWT encoding/decoding (default: HS256)
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Access token expiration time in minutes (default: 60)
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )


# Global settings instance to be imported throughout the app
settings = Settings()
