from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import json
import os
from openai import OpenAI

# --------------------
# Uygulama
# --------------------
app = FastAPI(title="SEO Description API")

# --------------------
# OPENAI Kullanımı
# --------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --------------------
# MODELLER
# --------------------
class SEORequest(BaseModel):
    title: str
    keywords: str

# --------------------
# YARDIMCILAR
# --------------------
def load_keys():
    if not os.path.exists("keys.json"):
        return {}
    with open("keys.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_keys(keys):
    with open("keys.json", "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2, ensure_ascii=False)

# --------------------
# ENDPOINT
# --------------------
@app.post("/generate-seo")
def generate_seo(
    data: SEORequest,
    x_api_key: str = Header(None)
):
    # API key kontrol
    keys = load_keys()

    if not x_api_key or x_api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    key_data = keys[x_api_key]
    limit = key_data.get("limit", 0)
    used = key_data.get("used", 0)

    # Limit kontrol (-1 = sınırsız)
    if limit != -1 and used >= limit:
        raise HTTPException(status_code=429, detail="API limit exceeded")

    # Prompt
    prompt = f"""
    Ürün adı: {data.title}
    Anahtar kelimeler: {data.keywords}

    Türkçe, SEO uyumlu, özgün ve satış odaklı
    e-ticaret ürün açıklaması yaz.
    """

    # OpenAI çağrısı
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=250
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Kullanım artır
    keys[x_api_key]["used"] = used + 1
    save_keys(keys)

    return {
        "plan": key_data.get("plan", "unknown"),
        "used": keys[x_api_key]["used"],
        "limit": limit,
        "seo_description": response.choices[0].message.content
    }

# --------------------
# ROOT (TEST)
# --------------------
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "SEO Description API is running"
    }
