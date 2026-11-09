/**
 * Painel de TV: consulta a API a cada 2s, detecta chamadas novas (ou
 * rechamadas), toca o sinal sonoro e anuncia a senha por voz.
 */
(() => {
  const { urlEstado } = window.PAINEL_CONFIG;
  const POLL_MS = 2000;
  const EXIBICAO_MS = 8000; // tempo de destaque de cada chamada (como no original)

  let ultimoTs = null; // carimbo da última chamada já anunciada
  let displayQueue = [];
  let isDisplaying = false;
  let audioCtx = null;
  let audioUnlocked = false;
  let systemVoices = [];
  let ultimoEstado = null;

  // 1. Vozes do navegador (carregam de forma assíncrona no Chrome)
  if ("speechSynthesis" in window) {
    const loadVoices = () => (systemVoices = window.speechSynthesis.getVoices());
    window.speechSynthesis.onvoiceschanged = loadVoices;
    loadVoices();
  }

  // 2. Destrava o áudio com o clique do usuário
  document.getElementById("btn-start-panel").addEventListener("click", () => {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (Ctx) {
      audioCtx = new Ctx();
      if (audioCtx.state === "suspended") audioCtx.resume();
    }
    if ("speechSynthesis" in window) {
      const u = new SpeechSynthesisUtterance("");
      u.volume = 0;
      window.speechSynthesis.speak(u);
    }
    audioUnlocked = true;
    document.getElementById("audio-unlocker").style.display = "none";
  });

  function mostrarAtual(senha) {
    document.getElementById("current-code").textContent = senha ? senha.codigo : "---";
    document.getElementById("current-service").textContent = senha
      ? `${senha.servico_label} - ${senha.prioridade_label}`
      : "Aguardando início...";
    document.getElementById("current-desk").textContent = `GUICHÊ ${senha ? senha.guiche : "--"}`;
  }

  function mostrarHistorico(historico) {
    const el = document.getElementById("history-list");
    if (!historico || historico.length === 0) {
      el.innerHTML = '<div class="empty-state">Sem chamadas anteriores.</div>';
      return;
    }
    const e = Senhas.escapeHtml;
    el.innerHTML = historico
      .map(
        (s) => `
        <div class="history-item">
          <div class="history-code">${e(s.codigo)}</div>
          <div class="history-info">
            <div class="history-desk">Guichê ${e(s.guiche)}</div>
            <div class="history-service">${e(s.servico_label)} - ${e(s.prioridade_label)}</div>
          </div>
        </div>`
      )
      .join("");
  }

  function animateCall() {
    const mainCall = document.querySelector(".main-call");
    mainCall.classList.add("flash");
    setTimeout(() => mainCall.classList.remove("flash"), 500);
  }

  // 3. Sinal sonoro "ding-dong" via Web Audio (idêntico ao original)
  function tocarAcorde(freqs, inicioDelay) {
    const t = audioCtx.currentTime + inicioDelay;
    const gain = audioCtx.createGain();
    gain.connect(audioCtx.destination);
    gain.gain.setValueAtTime(0, t);
    gain.gain.linearRampToValueAtTime(0.3, t + 0.1);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 1.2);
    freqs.forEach((f) => {
      const osc = audioCtx.createOscillator();
      osc.frequency.setValueAtTime(f, t);
      osc.connect(gain);
      osc.start(t);
      osc.stop(t + 1.3);
    });
  }

  function playChime() {
    if (!audioCtx) return;
    try {
      if (audioCtx.state === "suspended") audioCtx.resume();
      tocarAcorde([523.25, 659.25], 0);
      tocarAcorde([392.0, 493.88], 0.3);
    } catch (e) {
      console.error("Web Audio falhou:", e);
    }
  }

  // 4. Chamada por voz com a síntese nativa do navegador (sem chave de API)
  function announceTicket(senha) {
    if (!("speechSynthesis" in window)) return;
    setTimeout(() => {
      const soletrado = senha.codigo
        .split("")
        .map((c) => (c === "-" ? " " : c))
        .join(" ");
      const texto = `Senha, ${soletrado}. ${senha.servico_label}, ${senha.prioridade_label}. No guichê ${senha.guiche}.`;
      const utterance = new SpeechSynthesisUtterance(texto);
      utterance.lang = "pt-BR";
      utterance.rate = 0.9;
      const ptVoice = systemVoices.find((v) => v.lang.replace("_", "-") === "pt-BR");
      if (ptVoice) utterance.voice = ptVoice;
      window.speechSynthesis.speak(utterance);
    }, 1500);
  }

  function processDisplayQueue() {
    if (isDisplaying || displayQueue.length === 0) return;
    isDisplaying = true;
    const senha = displayQueue.shift();

    mostrarAtual(senha);
    animateCall();
    if (audioUnlocked && document.getElementById("enable-sound").checked) {
      playChime();
      announceTicket(senha);
    }

    setTimeout(() => {
      isDisplaying = false;
      if (displayQueue.length === 0 && ultimoEstado) mostrarAtual(ultimoEstado.atual);
      processDisplayQueue();
    }, EXIBICAO_MS);
  }

  async function atualizar() {
    const statusEl = document.getElementById("connection-status");
    let estado;
    try {
      estado = await Senhas.get(urlEstado);
      statusEl.style.display = "none";
    } catch (e) {
      statusEl.style.display = "block";
      throw e;
    }
    ultimoEstado = estado;

    const chamadas = [estado.atual, ...estado.historico].filter(Boolean);
    const maiorTs = chamadas.reduce((m, s) => Math.max(m, s.chamada_ts || 0), 0);

    if (ultimoTs === null) {
      // Primeira carga: mostra o estado atual sem anunciar chamadas antigas.
      ultimoTs = maiorTs;
    } else {
      chamadas
        .filter((s) => s.chamada_ts > ultimoTs)
        .sort((a, b) => a.chamada_ts - b.chamada_ts)
        .forEach((s) => displayQueue.push(s));
      ultimoTs = Math.max(ultimoTs, maiorTs);
    }

    mostrarHistorico(estado.historico);
    if (!isDisplaying && displayQueue.length === 0) mostrarAtual(estado.atual);
    processDisplayQueue();
  }

  Senhas.startClock();
  Senhas.poll(atualizar, POLL_MS);
})();

