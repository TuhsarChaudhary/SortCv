from pydantic import BaseModel, EmailStr


class UserSummary(BaseModel):
    """Minimal user information returned by the list users (GET /) endpoint."""

    id: int
    name: str
    email: EmailStr
    phone: str
    cv_access: bool

    class Config:
        orm_mode = True
