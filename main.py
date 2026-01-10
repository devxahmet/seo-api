from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI(
    title="SEO Ürün Açıklaması API",
    version="1.1.0"
)

class ProductRequest(BaseModel):
    urun_adi: str
    kategori: str
    ozellikler: List[str]
    platform: Optional[str] = "Genel"

def load_keys():
    with open("keys.json", "r") as f:
        return json.load(f)

def save_keys(data):
    with open("keys.json", "w") as f:
        json.dump(data, f, indent=2)

@app.post("/generate")
def generate(
    data: ProductRequest,
    x_api_key: str = Header(None)
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key gerekli")

    keys = load_keys()

    if x_api_key not in keys:
        raise HTTPException(status_code=403, detail="Geçersiz API key")

    user = keys[x_api_key]

    if user["used"] >= user["limit"]:
        raise HTTPException(status_code=429, detail="Aylık limit doldu")

    user["used"] += 1
    save_keys(keys)

    features = "\n".join([f"- {o}" for o in data.ozellikler])

    description = f"""
{data.urun_adi} ürünü {data.kategori} kategorisinde yer alır.
{data.platform} platformu için SEO uyumlu olarak hazırlanmıştır.

Öne Çıkan Özellikler:
{features}

Satış odaklı, özgün ve platform kurallarına uygundur.
"""

    return {
        "kalan_hak": user["limit"] - user["used"],
        "seo_aciklama": description.strip()
    }

@app.get("/")
def root():
    return {"status": "API çalışıyor"}
