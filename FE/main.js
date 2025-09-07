const API = "http://localhost:8000"; // BE FastAPI

async function signin() {
  const username = document.getElementById("signin-username").value;
  const password = document.getElementById("signin-password").value;

  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const res = await fetch("http://localhost:8000/signin", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData
  });

  const data = await res.json();
  if (res.ok) {
    localStorage.setItem("token", data.access_token);
    window.location.href = "home.html";
  } else {
    document.getElementById("signin-msg").innerText = data.detail;
  }
}

async function signup() {
  const username = document.getElementById("signup-username").value;
  const password = document.getElementById("signup-password").value;

  const res = await fetch("http://localhost:8000/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  const data = await res.json();
  document.getElementById("signup-msg").innerText = data.msg || data.detail;
}


async function createProduct() {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("Vui lòng đăng nhập trước");
    return;
  }

  const name = document.getElementById("prod-name").value;
  const description = document.getElementById("prod-desc").value;
  const price = document.getElementById("prod-price").value;
  const location = document.getElementById("prod-location").value;

  const res = await fetch(`${API}/products`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({ name, description, price, location }),
  });
  const data = await res.json();
  document.getElementById("product-msg").innerText = data.msg || data.detail;
}

async function searchProducts() {
  const q = document.getElementById("search-q").value;
  const location = document.getElementById("search-loc").value;

  const res = await fetch(`${API}/products/search?q=${q}&location=${location}`);
  const products = await res.json();

  const list = document.getElementById("product-list");
  list.innerHTML = "";
  products.forEach(p => {
    const li = document.createElement("li");
    li.textContent = `${p.name} - ${p.price} - ${p.location}`;
    li.onclick = () => addToCart(p.id);
    list.appendChild(li);
  });
}

async function addToCart(product_id) {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("Đăng nhập trước khi thêm vào giỏ");
    return;
  }
  await fetch(`${API}/cart/add`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({ product_id }),
  });
  alert("Đã thêm vào giỏ!");
}

async function viewCart() {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("Đăng nhập trước khi xem giỏ");
    return;
  }
  const res = await fetch(`${API}/cart`, {
    headers: { "Authorization": `Bearer ${token}` },
  });
  const items = await res.json();
  const list = document.getElementById("cart-list");
  list.innerHTML = "";
  items.forEach(p => {
    const li = document.createElement("li");
    li.textContent = `${p.name} - ${p.price}`;
    list.appendChild(li);
  });
}

async function checkout() {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("Đăng nhập trước khi thanh toán");
    return;
  }
  const res = await fetch(`${API}/cart/checkout`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}` },
  });
  const data = await res.json();
  alert(data.msg);
  viewCart();
}

// Giải mã JWT để lấy user id
function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "signin.html";
}

async function searchProducts() {
  const q = document.getElementById("search-q").value;
  const location = document.getElementById("location-select").value;

  const res = await fetch(`${API}/products/search?q=${q}&location=${location}`);
  const products = await res.json();

  const list = document.getElementById("product-list");
  list.innerHTML = "";
  products.forEach(p => {
    const li = document.createElement("li");
    li.textContent = `${p.name} - ${p.price}₫ - ${p.location}`;
    li.onclick = () => addToCart(p.id);
    list.appendChild(li);
  });
}
