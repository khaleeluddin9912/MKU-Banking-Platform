from contextlib import asynccontextmanager
from uuid import uuid4
import secrets
import string

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import User, Account, Transaction
from .schemas import RegisterIn, LoginIn, UserOut, AccountOut, TransferIn
from .security import hash_password, verify_password, create_access_token, decode_access_token

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="MKU Banking API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
bearer = HTTPBearer()

def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    try:
        user_id = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def make_account_number():
    return "MKU" + "".join(secrets.choice(string.digits) for _ in range(12))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(full_name=payload.full_name.strip(), email=email,
                password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    account = Account(account_number=make_account_number(), user_id=user.id,
                      balance_paise=1000000, currency="INR")
    db.add(account)
    db.commit()
    return {"message": "Account created", "account_number": account.account_number}

@app.post("/api/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}

@app.get("/api/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user

@app.get("/api/account", response_model=AccountOut)
def account(user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = db.scalar(select(Account).where(Account.user_id == user.id))
    if not result:
        raise HTTPException(status_code=404, detail="Account not found")
    return result

@app.get("/api/transactions")
def transactions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = db.scalar(select(Account).where(Account.user_id == user.id))
    rows = db.scalars(
        select(Transaction)
        .where(or_(Transaction.from_account_id == account.id, Transaction.to_account_id == account.id))
        .order_by(Transaction.id.desc()).limit(100)
    ).all()
    return [{
        "reference": row.reference,
        "amount_paise": row.amount_paise,
        "description": row.description,
        "status": row.status,
        "direction": "CREDIT" if row.to_account_id == account.id else "DEBIT",
        "created_at": row.created_at.isoformat(),
    } for row in rows]

@app.post("/api/transfers", status_code=201)
def transfer(payload: TransferIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    sender = db.scalar(select(Account).where(Account.user_id == user.id).with_for_update())
    recipient = db.scalar(select(Account).where(Account.account_number == payload.recipient_account).with_for_update())
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Sender or recipient account not found")
    if sender.id == recipient.id:
        raise HTTPException(status_code=400, detail="You cannot transfer to your own account")
    if sender.balance_paise < payload.amount_paise:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    try:
        sender.balance_paise -= payload.amount_paise
        recipient.balance_paise += payload.amount_paise
        tx = Transaction(reference=str(uuid4()), from_account_id=sender.id,
                         to_account_id=recipient.id, amount_paise=payload.amount_paise,
                         description=payload.description.strip())
        db.add(tx)
        db.commit()
        return {"message": "Transfer completed", "reference": tx.reference}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transfer could not be completed")
