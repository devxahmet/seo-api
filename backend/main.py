from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid

app = FastAPI(title="SeoX API")

# --------------------
# MODELLER
# --------------------
class RegisterModel(BaseModel):
    email: str
    password: str

class LoginModel(BaseModel):
    email: str
    password: str

# --------------------
# SAHTE DB (ŞİMDİLİK)
# --------------------
users = {}
tokens = {}

# --------------------
# API ENDPOINTS
# --------------------
@app.post("/register")
def register(data: RegisterModel):
    if data.email in users:
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı")

    users[data.email] = {
        "password": data.password,
        "api_key": None,
        "is_admin": False
    }
    return {"message": "Kayıt başarılı"}

@app.post("/login")
def login(data: LoginModel):
    user = users.get(data.email)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Hatalı bilgiler")

    token = str(uuid.uuid4())
    tokens[token] = data.email

    return {"token": token}

@app.post("/create-api-key")
def create_api_key(token: str):
    email = tokens.get(token)
    if not email:
        raise HTTPException(status_code=401, detail="Geçersiz token")

    if users[email]["api_key"]:
        raise HTTPException(status_code=400, detail="Zaten API key var")

    api_key = str(uuid.uuid4())
    users[email]["api_key"] = api_key

    return {"api_key": api_key}

@app.get("/health")
def health():
    return {"status": "ok"}

# --------------------
# FRONTEND SAYFALARI
# --------------------
@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.get("/dashboard")
def dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/admin")
def admin():
    return FileResponse("static/admin.html")

# --------------------
# STATIC FILES (EN ALT)
# --------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
