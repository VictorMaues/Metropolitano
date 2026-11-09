/* Totem de autoatendimento: emite a senha via API do Django. */
(() => {
  const { urlEmitir } = window.TOTEM_CONFIG;
  const RESET_MS = 8000; // volta à tela inicial após 8s (como no original)

  let servicoSelecionado = "";
  let timeoutId = null;
  let emitindo = false;

  function showStep(stepId) {
    document.querySelectorAll(".step-section").forEach((s) => s.classList.remove("active"));
    document.getElementById(stepId).classList.add("active");
  }

  function setErro(msg) {
    document.getElementById("totem-error").textContent = msg || "";
  }

  function resetTotem() {
    if (timeoutId) clearTimeout(timeoutId);
    servicoSelecionado = "";
    setErro("");
    showStep("step-service");
  }

  async function emitir(prioridade) {
    if (emitindo) return; // evita senha duplicada por duplo clique
    emitindo = true;
    setErro("");
    const botoes = document.querySelectorAll("[data-prioridade]");
    botoes.forEach((b) => (b.disabled = true));

    try {
      const senha = await Senhas.post(urlEmitir, {
        servico: servicoSelecionado,
        prioridade,
      });

      document.getElementById("print-service-title").textContent = senha.servico_label;
      document.getElementById("print-type-badge").textContent =
        prioridade === "NORMAL" ? "Atendimento Comum" : senha.prioridade_label;
      document.getElementById("print-code").textContent = senha.codigo;
      document.getElementById("print-time").textContent = senha.criado_em;

      // QR Code gerado por serviço externo (requer internet no totem).
      const qr = document.getElementById("print-qrcode");
      const qrBox = document.getElementById("print-qrcode-container");
      qrBox.style.display = "flex";
      qr.onerror = () => (qrBox.style.display = "none");
      qr.src =
        "https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=" +
        encodeURIComponent(senha.url_acompanhar);

      showStep("step-success");
      timeoutId = setTimeout(resetTotem, RESET_MS);
    } catch (e) {
      setErro("Não foi possível emitir a senha. Tente novamente ou procure a recepção.");
      console.error(e);
    } finally {
      emitindo = false;
      botoes.forEach((b) => (b.disabled = false));
    }
  }

  document.querySelectorAll("[data-servico]").forEach((btn) =>
    btn.addEventListener("click", () => {
      servicoSelecionado = btn.dataset.servico;
      showStep("step-priority");
    })
  );
  document.querySelectorAll("[data-prioridade]").forEach((btn) =>
    btn.addEventListener("click", () => emitir(btn.dataset.prioridade))
  );
  document.getElementById("btn-voltar").addEventListener("click", resetTotem);
  document.getElementById("btn-finalizar").addEventListener("click", resetTotem);

  Senhas.startClock();
})();

