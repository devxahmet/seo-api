const themeBtn = document.getElementById("themeToggle");
const langBtn = document.getElementById("langToggle");

themeBtn.onclick = () => {
  document.body.classList.toggle("light");
  themeBtn.textContent =
    document.body.classList.contains("light") ? "☀️" : "🌙";
};

langBtn.onclick = () => {
  alert("İngilizce versiyon yakında aktif!");
};
