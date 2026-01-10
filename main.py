from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import json
import os
from openai import OpenAI

app = FastAPI(title="SEO Description API")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SEORequest(BaseModel):
    title: str
    keywords: str

def load_keys():
    with open("keys.json", "r") as f:
        return json.load(f)

@app.post("/generate-seo")
def generate_seo(data: SEORequest, x_api_key: str = Header(None)):
    keys = load_keys()

    if x_api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    if keys[x_api_key]["used"] >= keys[x_api_key]["limit"]:
        raise HTTPException(status_code=429, detail="API limit exceeded")

    prompt = f"""
    Ürün adı: {data.title}
    Anahtar kelimeler: {data.keywords}

    E-ticaret için SEO uyumlu, özgün, satış odaklı bir ürün açıklaması yaz.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=250
    )

    keys[x_api_key]["used"] += 1
    with open("keys.json", "w") as f:
        json.dump(keys, f, indent=2)

    return {
        "seo_description": response.choices[0].message.content
    }
