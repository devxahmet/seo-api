const API_BASE = "https://seo-api-8qsy.onrender.com";

// Dark / Light tema toggle
document.getElementById("themeToggle").addEventListener("click", () => {
  document.body.classList.toggle("dark-theme");
  document.body.classList.toggle("light-theme");
  const icon = document.body.classList.contains("dark-theme") ? "🌙" : "☀️";
  document.getElementById("themeToggle").textContent = icon;
});

// Dil toggle
const translations = {
  "tr": { title: "SEO Açıklama Oluştur", planLabel:"Plan Seçiniz", apiKeyBtn:"API Key Oluştur", productName:"Ürün Adı", keywords:"Anahtar Kelimeler", generateBtn:"SEO Açıklama Oluştur" },
  "en": { title: "Generate SEO Description", planLabel:"Select Plan", apiKeyBtn:"Create API Key", productName:"Product Name", keywords:"Keywords", generateBtn:"Generate SEO Description" }
};
let currentLang = "tr";
document.getElementById("langToggle").addEventListener("click", () => {
  currentLang = currentLang==="tr"?"en":"tr";
  document.getElementById("pageTitle").textContent = translations[currentLang].title;
  document.getElementById("planLabel").textContent = translations[currentLang].planLabel;
  document.getElementById("createKeyBtn").textContent = translations[currentLang].apiKeyBtn;
  document.getElementById("productNameLabel").textContent = translations[currentLang].productName;
  document.getElementById("keywordsLabel").textContent = translations[currentLang].keywords;
  document.getElementById("generateBtn").textContent = translations[currentLang].generateBtn;
  document.getElementById("langToggle").textContent = currentLang==="tr"?"EN":"TR";
});

// Toast mesaj
function showToast(message) {
  let toast = document.createElement("div");
  toast.className = "toast";
  toast.innerText = message;
  document.body.appendChild(toast);
  setTimeout(() => { toast.classList.add("show"); }, 50);
  setTimeout(() => { toast.classList.remove("show"); setTimeout(()=>toast.remove(),300); }, 4000);
}

// Auth (dummy, backend ile bağlanacak)
document.getElementById("registerBtn").addEventListener("click", ()=>alert("Kayıt işlevi backend ile bağlanmalı"));
document.getElementById("loginBtn").addEventListener("click", ()=>alert("Giriş işlevi backend ile bağlanmalı"));

// API Key oluşturma
document.getElementById("createKeyBtn").addEventListener("click", async () => {
  const plan = document.getElementById("planSelect").value;
  try {
    const res = await fetch(API_BASE + "/create-api-key", {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-api-key": localStorage.getItem("apiKey") || "" },
      body: JSON.stringify({ plan })
    });
    const data = await res.json();

    // Toast mesaj göster
    showToast(data.message);

    // Yeni key varsa kaydet
    if (data.api_key) {
      localStorage.setItem("apiKey", data.api_key);
      document.getElementById("keyResult").innerText = "API Key:\n" + data.api_key;
    }
  } catch (err) {
    console.error(err);
    showToast("API Key oluşturulamadı!");
  }
});

// SEO Oluştur
document.getElementById("generateBtn").addEventListener("click", async () => {
  const apiKey = document.getElementById("keyResult").innerText.split("\n")[1];
  const title = document.getElementById("title").value;
  const keywords = document.getElementById("keywords").value;
  if(!apiKey){showToast("Önce API Key oluştur!"); return;}
  try{
    const res = await fetch(API_BASE+"/generate-seo", {
      method:"POST",
      headers:{"Content-Type":"application/json","x-api-key":apiKey},
      body:JSON.stringify({title,keywords})
    });
    const data = await res.json();
    document.getElementById("seoResult").innerText = data.seo_description || "Hata oluştu!";
  }catch(err){console.error(err); document.getElementById("seoResult").innerText="Hata oluştu!";}
});

// Ödeme button
document.getElementById("payBtn").addEventListener("click", ()=>showToast("Ödeme sayfası PayTR / Shopier entegrasyonu ile açılacak"));
