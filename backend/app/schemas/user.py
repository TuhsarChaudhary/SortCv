from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import date, datetime
import re


class UserBase(BaseModel):
    fname: str
    lname: str
    email: EmailStr
    phone: str
    dateofbirth: date
    gender: str
    country: str
    nationality: str
    cv_access: Optional[bool] = False  # Optional on create/update, default False
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number."""
        if not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError('Phone number must be a valid international format')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """Validate gender."""
        valid_genders = ['male', 'female', 'other']
        if v.lower() not in valid_genders:
            raise ValueError(f'Gender must be one of: {", ".join(valid_genders)}')
        return v.lower()


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    fname: Optional[str] = None
    lname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    dateofbirth: Optional[date] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    nationality: Optional[str] = None
    cv_access: Optional[bool] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number."""
        if v is not None and not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError('Phone number must be a valid international format')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """Validate gender."""
        if v is not None:
            valid_genders = ['male', 'female', 'other']
            if v.lower() not in valid_genders:
                raise ValueError(f'Gender must be one of: {", ".join(valid_genders)}')
            return v.lower()
        return v


class UserInDB(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    cv_access: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class User(UserInDB):
    pass  # retains all fields

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=8)
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain at least one special character')
        return v
