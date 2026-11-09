/* Painel do Operador: chama/rechama senhas e acompanha a fila em tempo real. */
(() => {
  const cfg = window.OPERADOR_CONFIG;
  const POLL_MS = 2000;
  const e = Senhas.escapeHtml;

  let activeTab = "all";
  let selectedDesk = sessionStorage.getItem("operator_desk") || "1";
  let estado = null;

  const deskSelect = document.getElementById("desk-select");
  deskSelect.value = selectedDesk;
  if (deskSelect.value !== selectedDesk) selectedDesk = deskSelect.value;

  const urlChamarSenha = (id) => cfg.urlChamarSenha.replace("/0/", `/${id}/`);

  function setMensagem(msg) {
    document.getElementById("operator-message").textContent = msg || "";
  }

  function tratarErro(err) {
    if (err.status === 401 || err.status === 403) {
      window.location.href = cfg.urlLogin; // sessão expirada
      return;
    }
    setMensagem(err.message);
  }

  async function carregar() {
    try {
      estado = await Senhas.get(`${cfg.urlEstado}?guiche=${encodeURIComponent(selectedDesk)}`);
    } catch (err) {
      tratarErro(err);
      throw err;
    }
    render();
  }

  async function acao(fn, botao) {
    setMensagem("");
    if (botao) botao.disabled = true;
    try {
      await fn();
      await carregar();
    } catch (err) {
      tratarErro(err);
    } finally {
      if (botao) botao.disabled = false;
    }
  }

  const chamarProxima = (escopo, botao) =>
    acao(() => Senhas.post(cfg.urlChamarProxima, { guiche: selectedDesk, escopo }), botao);

  const chamarSenha = (id, botao) =>
    acao(() => Senhas.post(urlChamarSenha(id), { guiche: selectedDesk }), botao);

  function itemHtml(s, botaoLabel, botaoClasse, detalheHora) {
    return `
      <div class="queue-item">
        <div>
          <div class="queue-code">${e(s.codigo)}</div>
          <div class="queue-details">
            <span class="badge ${Senhas.badgeClass(s.prioridade)}">${e(s.prioridade_label)}</span>
            <span>${e(s.servico_label)}</span>
            <span style="color: var(--text-muted)">${e(detalheHora)}</span>
          </div>
        </div>
        <button type="button" class="btn ${botaoClasse}" data-chamar-id="${s.id}">${botaoLabel}</button>
      </div>`;
  }

  function render() {
    if (!estado) return;

    // Contadores por fila
    Object.entries(estado.contadores).forEach(([chave, total]) => {
      const el = document.getElementById(`count-${chave}`);
      if (el) el.textContent = total;
    });

    // Senha em atendimento neste guichê
    const minha = estado.minha_senha;
    document.getElementById("active-code").textContent = minha ? minha.codigo : "---";
    document.getElementById("active-info").textContent = minha
      ? `${minha.servico_label} - ${minha.prioridade_label} (Chamada às ${minha.chamado_em})`
      : "Nenhuma senha em atendimento";
    document.getElementById("btn-recall").style.display = minha ? "inline-flex" : "none";

    // Lista conforme a aba
    const container = document.getElementById("queue-list-container");
    const titulo = document.getElementById("queue-title");

    if (activeTab === "history") {
      titulo.textContent = "Histórico de Chamadas (hoje)";
      container.innerHTML = estado.historico.length
        ? estado.historico
            .map((s) =>
              itemHtml(s, "Rechamar", "btn-secondary", `Guichê ${s.guiche} · Chamada às ${s.chamado_em}`)
            )
            .join("")
        : '<div class="empty-state">Histórico de chamadas vazio.</div>';
      return;
    }

    titulo.textContent = "Fila de Espera";
    const lista =
      activeTab === "all" ? estado.fila : estado.fila.filter((s) => s.servico === activeTab);
    container.innerHTML = lista.length
      ? lista.map((s) => itemHtml(s, "Chamar", "btn-primary", `Emitida às ${s.criado_em}`)).join("")
      : '<div class="empty-state">Fila vazia.</div>';
  }

  // Eventos
  deskSelect.addEventListener("change", () => {
    selectedDesk = deskSelect.value;
    sessionStorage.setItem("operator_desk", selectedDesk);
    carregar().catch(() => {});
  });

  document.querySelectorAll("[data-tab]").forEach((btn) =>
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeTab = btn.dataset.tab;
      render();
    })
  );

  document.querySelectorAll("[data-chamar-proxima]").forEach((btn) =>
    btn.addEventListener("click", () => chamarProxima(btn.dataset.chamarProxima, btn))
  );

  document.getElementById("queue-list-container").addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-chamar-id]");
    if (btn) chamarSenha(btn.dataset.chamarId, btn);
  });

  document.getElementById("btn-recall").addEventListener("click", (ev) => {
    if (estado && estado.minha_senha) chamarSenha(estado.minha_senha.id, ev.currentTarget);
  });

  document.getElementById("btn-encerrar").addEventListener("click", (ev) => {
    const ok = confirm(
      "Encerrar o expediente?\n\nTodas as senhas aguardando serão CANCELADAS e os atendimentos em andamento serão finalizados."
    );
    if (ok) acao(() => Senhas.post(cfg.urlEncerrar), ev.currentTarget);
  });

  Senhas.poll(carregar, POLL_MS);
})();

