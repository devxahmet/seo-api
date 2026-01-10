from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="SEO Ürün Açıklaması API",
    description="E-ticaret için SEO uyumlu ürün açıklaması üretir",
    version="1.0.0"
)

# Basit API key (şimdilik)
API_KEY = "localhostxdevmainn"

class ProductRequest(BaseModel):
    urun_adi: str
    kategori: str
    ozellikler: List[str]
    platform: Optional[str] = "Genel"

@app.post("/generate")
def generate_description(
    data: ProductRequest,
    x_api_key: str = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Geçersiz API Key")

    features_text = "\n".join([f"- {o}" for o in data.ozellikler])

    description = f"""
{data.urun_adi} ürünü, {data.kategori} kategorisinde yer almakta olup {data.platform} platformu için
özel olarak hazırlanmıştır.

Öne Çıkan Özellikler:
{features_text}

Kaliteli malzeme yapısı ve kullanıcı dostu tasarımı sayesinde günlük kullanım için idealdir.
SEO uyumlu ve satış odaklı bu açıklama, platform kurallarına uygundur.
"""

    return {
        "urun_adi": data.urun_adi,
        "platform": data.platform,
        "seo_aciklama": description.strip()
    }

@app.get("/")
def root():
    return {"status": "API çalışıyor"}
