from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class AccountOut(BaseModel):
    account_number: str
    balance_paise: int
    currency: str
    model_config = ConfigDict(from_attributes=True)

class TransferIn(BaseModel):
    recipient_account: str = Field(min_length=8, max_length=20)
    amount_paise: int = Field(gt=0, le=50000000)
    description: str = Field(default="Transfer", min_length=1, max_length=240)
