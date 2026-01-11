from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os, secrets, bcrypt, datetime
from openai import OpenAI

# Env vars
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./seo_api.db")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# DB setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    api_key = Column(String, unique=True)
    plan = Column(String)
    limit = Column(Integer)
    used = Column(Integer, default=0)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    amount = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# FastAPI
app = FastAPI(title="SEO WebApp API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Static mount
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# OpenAI
client = OpenAI(api_key=OPENAI_KEY)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schemas
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class SEORequest(BaseModel):
    title: str
    keywords: str

class PlanRequest(BaseModel):
    plan: str

# Auth
@app.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username==data.username).first()
    if existing: raise HTTPException(400, "Kullanıcı zaten var")
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    api_key = secrets.token_hex(8)
    user = User(username=data.username, password=hashed, api_key=api_key, plan="basic", limit=1000, used=0)
    db.add(user)
    db.commit()
    return {"message":"Kayıt başarılı", "api_key":api_key}

@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username==data.username).first()
    if not user or not bcrypt.checkpw(data.password.encode(), user.password.encode()):
        raise HTTPException(401, "Kullanıcı adı veya şifre yanlış")
    return {"message":"Giriş başarılı", "api_key":user.api_key}

# SEO API
@app.post("/generate-seo")
def generate_seo(data: SEORequest, x_api_key: str = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.api_key==x_api_key).first()
    if not user: raise HTTPException(401, "Geçersiz API Key")
    if user.limit != -1 and user.used >= user.limit: raise HTTPException(429, "API limiti doldu")
    prompt = f"Ürün adı: {data.title}\nAnahtar kelimeler: {data.keywords}\nTürkçe, SEO uyumlu, satış odaklı e-ticaret açıklaması yaz."
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], max_tokens=250)
    user.used += 1
    db.commit()
    return {"plan":user.plan,"used":user.used,"limit":user.limit,"seo_description":response.choices[0].message.content}

# API Key / Plan
@app.post("/create-api-key")
def create_key(data: PlanRequest, x_api_key: str = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.api_key==x_api_key).first()
    if not user: raise HTTPException(401, "Geçersiz API Key")

    if user.used < user.limit or user.limit == -1:
        return {"message": "Zaten aktif bir API Key'in var, plan bitene kadar yeni oluşturamazsın.", 
                "api_key": user.api_key, 
                "plan": user.plan, 
                "used": user.used, 
                "limit": user.limit}

    plans = {"basic":1000, "pro":10000, "agency":-1}
    if data.plan not in plans: raise HTTPException(400, "Geçersiz plan")

    new_api_key = secrets.token_hex(8)
    user.api_key = new_api_key
    user.plan = data.plan
    user.limit = plans[data.plan]
    user.used = 0
    db.commit()
    return {"message":"Yeni API Key oluşturuldu", "api_key":new_api_key, "plan":user.plan, "limit":user.limit}

# Ödeme webhook
@app.post("/payment-webhook")
def payment_webhook(user_id: int, amount: int, status: str, db: Session = Depends(get_db)):
    payment = Payment(user_id=user_id, amount=amount, status=status)
    db.add(payment)
    db.commit()
    return {"message":"Webhook kaydedildi"}

@app.get("/health")
def health():
    return {"status":"ok","message":"SEO WebApp API çalışıyor"}
