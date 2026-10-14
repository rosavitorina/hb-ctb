from pydantic import BaseModel, Field, field_validator


class AccountResponse(BaseModel):
    id: str
    email: str
    role: str = "user"


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20, max_length=20000)