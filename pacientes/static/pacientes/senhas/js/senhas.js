/**
 * Utilitários compartilhados do Painel de Senhas (Hospital Metropolitano).
 * Substitui o app.js + Socket.io do projeto original: o estado agora vem da
 * API do Django (banco de dados) e as telas se atualizam por polling.
 */
const Senhas = (() => {
  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
    return match ? decodeURIComponent(match[2]) : null;
  }

  async function request(url, options = {}) {
    const resp = await fetch(url, {
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken") || "",
        ...(options.headers || {}),
      },
      ...options,
    });
    let data = {};
    try {
      data = await resp.json();
    } catch (e) {
      /* resposta sem JSON (ex.: redirecionamento de login) */
    }
    if (!resp.ok) {
      const err = new Error(data.erro || `Erro ${resp.status}`);
      err.status = resp.status;
      throw err;
    }
    return data;
  }

  const get = (url) => request(url, { method: "GET" });
  const post = (url, body = {}) =>
    request(url, { method: "POST", body: JSON.stringify(body) });

  /** Executa `fn` agora e a cada `ms` milissegundos, pausando automaticamente em abas em segundo plano. */
  function poll(fn, ms) {
    let running = false;
    const tick = async () => {
      if (running) return;
      if (document.hidden) return; // pausa requisições quando a aba não está visível
      running = true;
      try {
        await fn();
      } catch (e) {
        console.warn("Falha ao atualizar:", e);
      } finally {
        running = false;
      }
    };
    tick();
    const intervalId = setInterval(tick, ms);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) tick();
    });
    return intervalId;
  }

  function startClock(clockId = "clock", dayId = "day-of-week") {
    const update = () => {
      const now = new Date();
      const clockEl = document.getElementById(clockId);
      const dayEl = document.getElementById(dayId);
      if (clockEl) clockEl.textContent = now.toLocaleTimeString("pt-BR");
      if (dayEl) dayEl.textContent = now.toLocaleDateString("pt-BR", { weekday: "long" });
    };
    update();
    setInterval(update, 1000);
  }

  function badgeClass(prioridade) {
    if (prioridade === "SUPER") return "badge-super";
    if (prioridade === "PREFERENCIAL") return "badge-priority";
    return "badge-normal";
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);
  }

  return { get, post, poll, startClock, badgeClass, escapeHtml };
})();

