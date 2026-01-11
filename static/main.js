const container = document.getElementById("container");

document.getElementById("signUp").onclick = () =>
  container.classList.add("right-panel-active");

document.getElementById("signIn").onclick = () =>
  container.classList.remove("right-panel-active");

async function register(e) {
  e.preventDefault();

  const email = regEmail.value;
  const password = regPassword.value;

  const res = await fetch("/register", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ email, password })
  });

  if (res.ok) {
    alert("Kayıt başarılı!");
    container.classList.remove("right-panel-active");
  } else {
    alert("Hata oluştu");
  }
}

async function login(e) {
  e.preventDefault();

  const email = loginEmail.value;
  const password = loginPassword.value;

  const res = await fetch("/login", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();

  if (res.ok) {
    localStorage.setItem("token", data.token);
    window.location.href = "/dashboard";
  } else {
    alert("Giriş başarısız");
  }
}
