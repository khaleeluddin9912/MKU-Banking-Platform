from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    account: Mapped["Account"] = relationship(back_populates="owner", uselist=False)

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    balance_paise: Mapped[int] = mapped_column(Integer, default=1000000)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    owner: Mapped[User] = relationship(back_populates="account")

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    from_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    to_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    amount_paise: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(240), default="Transfer")
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
