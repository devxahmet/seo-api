from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from passlib.context import CryptContext
import sqlite3, uuid, datetime, os
from openai import OpenAI

# ================= CONFIG =================
SECRET_KEY = "SEOX_SECRET_KEY"
ALGORITHM = "HS256"
ADMIN_TOKEN = "localhostxdevmainn@"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ================= APP =================
app = FastAPI(title="SeoX API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd = CryptContext(schemes=["bcrypt"])

# ================= DATABASE =================
db = sqlite3.connect("database.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    api_key TEXT,
    expires_at TEXT,
    used_requests INTEGER DEFAULT 0,
    monthly_limit INTEGER DEFAULT 1000,
    last_request TEXT
)
""")
db.commit()

# ================= HELPERS =================
def create_token(email):
    return jwt.encode(
        {"sub": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_user_by_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        cur.execute("SELECT * FROM users WHERE email=?", (payload["sub"],))
        user = cur.fetchone()
        if not user:
            raise HTTPException(401, "Kullanıcı yok")
        return user
    except JWTError:
        raise HTTPException(401, "Token geçersiz")

def check_limits(user):
    now = datetime.datetime.now()

    if user[4] == "DISABLED":
        raise HTTPException(403, "Hesap kapalı")

    if user[4]:
        try:
            if datetime.datetime.fromisoformat(user[4]) < now:
                raise HTTPException(403, "Abonelik süresi doldu")
        except:
            pass

    if user[5] >= user[6]:
        raise HTTPException(429, "Aylık kullanım limiti doldu")

    if user[7]:
        last = datetime.datetime.fromisoformat(user[7])
        if (now - last).seconds < 2:
            raise HTTPException(429, "Çok hızlı istek")

# ================= AUTH =================
@app.post("/register")
def register(email: str, password: str):
    try:
        cur.execute(
            "INSERT INTO users (email,password) VALUES (?,?)",
            (email, pwd.hash(password))
        )
        db.commit()
        return {"ok": True}
    except:
        raise HTTPException(400, "Kullanıcı var")

@app.post("/login")
def login(email: str, password: str):
    cur.execute("SELECT password FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    if not row or not pwd.verify(password, row[0]):
        raise HTTPException(401, "Hatalı giriş")
    return {"token": create_token(email)}

# ================= API KEY =================
@app.post("/create-api-key")
def create_api_key(token: str):
    user = get_user_by_token(token)

    if user[3]:
        raise HTTPException(400, "API key zaten var")

    key = "sk-" + uuid.uuid4().hex
    expires = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()

    cur.execute("""
        UPDATE users SET api_key=?, expires_at=? WHERE id=?
    """, (key, expires, user[0]))
    db.commit()

    return {"api_key": key, "expires_at": expires}

# ================= SEO (OPENAI) =================
@app.post("/seo")
def seo(api_key: str, title: str, keywords: str):
    cur.execute("SELECT * FROM users WHERE api_key=?", (api_key,))
    user = cur.fetchone()
    if not user:
        raise HTTPException(401, "Geçersiz API key")

    check_limits(user)

    prompt = f"""
Ürün adı: {title}
Anahtar kelimeler: {keywords}

SEO uyumlu, özgün, satış odaklı bir ürün açıklaması yaz.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        content = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(500, str(e))

    cur.execute("""
        UPDATE users
        SET used_requests = used_requests + 1,
            last_request = ?
        WHERE id=?
    """, (datetime.datetime.now().isoformat(), user[0]))
    db.commit()

    return {"content": content}

# ================= ADMIN =================
def admin_auth(token):
    if token != ADMIN_TOKEN:
        raise HTTPException(403, "Admin yetkisi yok")

@app.get("/admin/users")
def admin_users(token: str):
    admin_auth(token)
    cur.execute("""
        SELECT id,email,api_key,used_requests,monthly_limit,expires_at
        FROM users
    """)
    rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "email": r[1],
            "api_key": r[2],
            "usage": f"{r[3]}/{r[4]}",
            "expires": r[5]
        } for r in rows
    ]

@app.post("/admin/disable-user")
def disable_user(user_id: int, token: str):
    admin_auth(token)
    cur.execute("UPDATE users SET expires_at='DISABLED' WHERE id=?", (user_id,))
    db.commit()
    return {"ok": True}

@app.get("/admin/stats")
def admin_stats(token: str):
    admin_auth(token)
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE api_key IS NOT NULL")
    active = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE expires_at='DISABLED'")
    disabled = cur.fetchone()[0]
    return {
        "total_users": total,
        "active_keys": active,
        "disabled_users": disabled
    }
