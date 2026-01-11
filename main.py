from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os
import secrets
from openai import OpenAI

# --------------------
# DATABASE
# --------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./seo_api.db")  # Render'da env variable ile değiştir

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# --------------------
# MODEL
# --------------------
class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String, unique=True, index=True)
    plan = Column(String)
    limit = Column(Integer)
    used = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

# --------------------
# APP
# --------------------
app = FastAPI(title="SEO Description API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # test için tüm frontendler
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --------------------
# SCHEMAS
# --------------------
class SEORequest(BaseModel):
    title: str
    keywords: str

class CreateKeyRequest(BaseModel):
    plan: str

# --------------------
# DB DEP
# --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------
# CREATE API KEY
# --------------------
@app.post("/create-api-key")
def create_api_key(data: CreateKeyRequest, db: Session = Depends(get_db)):
    plans = {
        "basic": 1000,
        "pro": 10000,
        "agency": -1
    }

    if data.plan not in plans:
        raise HTTPException(status_code=400, detail="Invalid plan")

    api_key = f"{data.plan}_{secrets.token_hex(8)}"

    new_key = APIKey(
        api_key=api_key,
        plan=data.plan,
        limit=plans[data.plan],
        used=0
    )

    db.add(new_key)
    db.commit()

    return {
        "api_key": api_key,
        "plan": data.plan,
        "limit": plans[data.plan]
    }

# --------------------
# GENERATE SEO
# --------------------
@app.post("/generate-seo")
def generate_seo(
    data: SEORequest,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    key = db.query(APIKey).filter(APIKey.api_key == x_api_key).first()

    if not key:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    if key.limit != -1 and key.used >= key.limit:
        raise HTTPException(status_code=429, detail="API limit exceeded")

    prompt = f"""
    Ürün adı: {data.title}
    Anahtar kelimeler: {data.keywords}

    Türkçe, SEO uyumlu, özgün ve satış odaklı
    e-ticaret ürün açıklaması yaz.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250
    )

    key.used += 1
    db.commit()

    return {
        "plan": key.plan,
        "used": key.used,
        "limit": key.limit,
        "seo_description": response.choices[0].message.content
    }

# --------------------
# ROOT
# --------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "SQL-backed SEO API running"}
