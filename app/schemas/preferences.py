# User preferences (locale + IANA timezone)

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.timezones import validate_iana_timezone


_LOCALE_RE = re.compile(r"^[a-z]{2}(-[A-Za-z0-9]{2,8})?$")


class UserPreferencesRead(BaseModel):
    locale: str
    iana_timezone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesUpdate(BaseModel):
    locale: Optional[str] = Field(None, min_length=2, max_length=16)
    iana_timezone: Optional[str] = Field(None, max_length=64)

    @field_validator("locale")
    @classmethod
    def check_locale(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        s = v.strip()
        if not _LOCALE_RE.fullmatch(s):
            raise ValueError(
                "locale debe ser tipo BCP47 corto, ej. es, en, es-ES")
        return s

    @field_validator("iana_timezone")
    @classmethod
    def check_tz(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_iana_timezone(v)
