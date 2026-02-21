from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, Field

from app.core.utils.validators import (
    normalize_email_for_auth,
    validate_password_strength,
    validate_phone_number,
)
from app.core.exceptions.auth import PasswordTooWeakError
from app.core.exceptions.validation import InvalidEmailError, InvalidPhoneError


class UserBaseSchema(BaseModel):
    """
    סכימת בסיס עם וולידציות משותפות – משתמש ב-core.utils.validators (מקור אמת יחיד).
    """
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    new_password: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]):
        if v is None:
            return v
        try:
            return normalize_email_for_auth(v)
        except ValueError as e:
            raise InvalidEmailError(email=v) from e

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]):
        if v is None:
            return v
        try:
            return validate_phone_number(v)
        except ValueError as e:
            raise InvalidPhoneError(phone=v) from e

    @field_validator("password", "new_password", check_fields=False)
    @classmethod
    def validate_password_strength(cls, v: Optional[str]):
        if v is None:
            return v
        try:
            return validate_password_strength(v)
        except ValueError:
            raise PasswordTooWeakError()