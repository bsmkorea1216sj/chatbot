(function () {
  const CONFIG = {
    WEB_APP_URL:
      (window.PRE_ORDER_CONFIG && window.PRE_ORDER_CONFIG.webAppUrl) ||
      "REPLACE_WITH_DEPLOYED_WEB_APP_URL",
    PRODUCT_ID: (window.PRE_ORDER_CONFIG && window.PRE_ORDER_CONFIG.productId) || "",
  };

  const state = {
    product: null,
    quantity: 1,
  };

  const el = (id) => document.getElementById(id);
  const numberFormat = (n) => Number(n || 0).toLocaleString("ko-KR");

  function apiUrl(params) {
    const url = new URL(CONFIG.WEB_APP_URL);
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    return url.toString();
  }

  async function loadProduct() {
    try {
      const params = { action: "getProduct" };
      if (CONFIG.PRODUCT_ID) params.productId = CONFIG.PRODUCT_ID;
      const res = await fetch(apiUrl(params));
      const data = await res.json();
      if (!data.success) throw new Error(data.message || "상품 정보를 불러오지 못했습니다.");
      state.product = data.product;
      renderProduct(data.product);
      startCountdown(data.product.reservationEnd);
    } catch (err) {
      showFormError(err.message);
    }
  }

  function renderProduct(product) {
    el("heroProductImage").src = product.imageUrl || "";
    el("heroProductImage").alt = product.name || "";
    el("productImage").src = product.imageUrl || "";
    el("productImage").alt = product.name || "";
    el("productBadge").textContent = product.badge || "NEW";
    el("productName").textContent = product.name || "";
    el("productDesc").textContent = product.description || "";
    el("priceOriginal").textContent = numberFormat(product.price) + "원";
    el("priceSale").textContent = numberFormat(product.preorderPrice) + "원";
    el("discountBadge").textContent = product.discountRate ? `${product.discountRate}%` : "";
    el("reservationRange").textContent = `${product.reservationStart} ~ ${product.reservationEnd}`;
    el("releaseDate").textContent = product.releaseDate || "-";
    updateTotal();
  }

  function updateTotal() {
    if (!state.product) return;
    const total = state.product.preorderPrice * state.quantity;
    el("totalAmount").textContent = numberFormat(total) + "원";
  }

  function setQuantity(qty) {
    state.quantity = Math.max(1, qty || 1);
    el("qtyInput").value = state.quantity;
    updateTotal();
  }

  let countdownTimer = null;
  function startCountdown(endDateStr) {
    if (!endDateStr) return;
    const end = new Date(endDateStr + "T23:59:59");
    if (countdownTimer) clearInterval(countdownTimer);

    function tick() {
      const diff = end.getTime() - Date.now();
      if (diff <= 0) {
        ["cdDays", "cdHours", "cdMinutes", "cdSeconds"].forEach((id) => (el(id).textContent = "00"));
        clearInterval(countdownTimer);
        return;
      }
      const days = Math.floor(diff / 86400000);
      const hours = Math.floor((diff % 86400000) / 3600000);
      const minutes = Math.floor((diff % 3600000) / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      el("cdDays").textContent = String(days).padStart(2, "0");
      el("cdHours").textContent = String(hours).padStart(2, "0");
      el("cdMinutes").textContent = String(minutes).padStart(2, "0");
      el("cdSeconds").textContent = String(seconds).padStart(2, "0");
    }
    tick();
    countdownTimer = setInterval(tick, 1000);
  }

  function showFormError(message) {
    const errorEl = el("formError");
    errorEl.textContent = message || "";
    errorEl.hidden = !message;
  }

  function validateForm(values) {
    if (!values.name.trim()) return "이름을 입력해 주세요.";
    const phoneDigits = values.phone.replace(/[^0-9]/g, "");
    if (!/^0\d{8,10}$/.test(phoneDigits)) return "연락처를 정확히 입력해 주세요. (- 없이 숫자만)";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) return "이메일 형식을 확인해 주세요.";
    if (!values.agree) return "개인정보 수집·이용에 동의해 주세요.";
    return null;
  }

  async function submitApplication(values) {
    const res = await fetch(CONFIG.WEB_APP_URL, {
      method: "POST",
      // text/plain avoids a CORS preflight against the Apps Script Web App;
      // the backend still parses the body as JSON regardless of content-type.
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({
        action: "submitApplication",
        name: values.name,
        phone: values.phone,
        email: values.email,
        quantity: state.quantity,
        productId: state.product ? state.product.productId : CONFIG.PRODUCT_ID,
        agree: values.agree,
      }),
    });
    return res.json();
  }

  function openModal(message) {
    el("successMessage").textContent = message;
    el("successModal").hidden = false;
  }

  function closeModal() {
    el("successModal").hidden = true;
  }

  function bindEvents() {
    el("qtyMinus").addEventListener("click", () => setQuantity(state.quantity - 1));
    el("qtyPlus").addEventListener("click", () => setQuantity(state.quantity + 1));
    el("qtyInput").addEventListener("change", (e) => setQuantity(parseInt(e.target.value, 10)));

    el("agreeDetailBtn").addEventListener("click", () => {
      const detail = el("agreeDetail");
      detail.hidden = !detail.hidden;
    });

    el("closeModalBtn").addEventListener("click", closeModal);

    el("applicationForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      showFormError(null);
      const values = {
        name: el("name").value,
        phone: el("phone").value,
        email: el("email").value,
        agree: el("agree").checked,
      };
      const error = validateForm(values);
      if (error) {
        showFormError(error);
        return;
      }
      const submitBtn = el("submitBtn");
      submitBtn.disabled = true;
      submitBtn.textContent = "신청 처리 중...";
      try {
        const result = await submitApplication(values);
        if (result.success) {
          openModal(`신청번호 ${result.applicationId}\n확인 후 안내 이메일을 보내드릴게요.`);
          el("applicationForm").reset();
          setQuantity(1);
        } else {
          showFormError(result.message || "신청 처리 중 오류가 발생했습니다.");
        }
      } catch (err) {
        showFormError("네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "사전 구매신청하기";
      }
    });

    el("notifyBtn").addEventListener("click", () => {
      el("notifyBtn").textContent = "알림 신청 완료";
      el("notifyBtn").disabled = true;
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    loadProduct();
  });
})();
