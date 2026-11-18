/**
 * Hospital Metropolitano - Dashboard de Atendimento de Pacientes
 * Baseado no modelo Clara.care com integração aos dados reais do sistema.
 */

(function () {
  'use strict';

  // Estado da aplicação
  let currentFilter = 'all';
  let patientsData = [];
  let isFetching = false;

  // Utilitários de escape e formatação
  const escapeHtml = (str) => {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, (char) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[char]));
  };

  const getCsrfToken = () => {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  };

  // Elementos do DOM
  const elements = {
    currentDate: document.getElementById('current-date'),
    waitingCount: document.getElementById('waiting-count'),
    serviceCount: document.getElementById('service-count'),
    averageWait: document.getElementById('average-wait'),
    nextPatient: document.getElementById('next-patient'),
    nextArrival: document.getElementById('next-arrival'),
    patientSearch: document.getElementById('patient-search'),
    queueBody: document.getElementById('queue-body'),
    resultCount: document.getElementById('result-count'),
    updatedAt: document.getElementById('updated-at'),
    refreshButton: document.getElementById('refresh-button'),
    filterButtons: document.querySelectorAll('[data-filter]'),
    toastContainer: document.getElementById('toast-container')
  };

  /**
   * Exibe notificação temporária (Toast)
   */
  function showToast(message, type = 'success') {
    if (!elements.toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <i data-lucide="${type === 'success' ? 'check-circle' : 'alert-circle'}"></i>
      <span>${escapeHtml(message)}</span>
    `;
    elements.toastContainer.appendChild(toast);
    if (window.lucide) window.lucide.createIcons();

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  /**
   * Atualiza a data atual no cabeçalho
   */
  function updateHeaderDate() {
    if (elements.currentDate) {
      const now = new Date();
      elements.currentDate.textContent = now.toLocaleDateString('pt-BR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      });
    }
  }

  /**
   * Renderiza os dados da fila e as métricas na tela
   */
  function render() {
    const now = new Date();
    const sorted = [...patientsData].sort((a, b) => {
      // Prioridade por status: waiting primeiro, depois service, depois done
      const statusOrder = { waiting: 0, service: 1, done: 2 };
      const statusDiff = (statusOrder[a.status] ?? 3) - (statusOrder[b.status] ?? 3);
      if (statusDiff !== 0) return statusDiff;
      // Depois por data de agendamento (chegada)
      return new Date(a.chegada_iso || 0) - new Date(b.chegada_iso || 0);
    });

    const waiting = sorted.filter((p) => p.status === 'waiting');
    const inService = sorted.filter((p) => p.status === 'service');

    // Métricas
    if (elements.waitingCount) elements.waitingCount.textContent = waiting.length;
    if (elements.serviceCount) elements.serviceCount.textContent = inService.length;

    // Tempo médio de espera
    if (elements.averageWait) {
      if (waiting.length > 0) {
        const totalMinutes = waiting.reduce((sum, p) => sum + (Number(p.espera_minutos) || 0), 0);
        elements.averageWait.textContent = Math.round(totalMinutes / waiting.length) + ' min';
      } else {
        elements.averageWait.textContent = '0 min';
      }
    }

    // Próximo na fila
    if (elements.nextPatient) {
      elements.nextPatient.textContent = waiting[0]?.nome || '—';
    }
    if (elements.nextArrival) {
      elements.nextArrival.textContent = waiting[0]
        ? 'Chegada às ' + waiting[0].chegada_hora
        : 'Nenhum paciente aguardando';
    }

    // Busca e Filtros
    const searchTerm = elements.patientSearch
      ? elements.patientSearch.value.trim().toLocaleLowerCase('pt-BR')
      : '';

    const visible = sorted
      .map((p, index) => ({ ...p, position: index + 1 }))
      .filter((p) => {
        const matchesFilter = currentFilter === 'all' || p.status === currentFilter;
        const matchesSearch =
          !searchTerm ||
          p.nome.toLocaleLowerCase('pt-BR').includes(searchTerm) ||
          p.codigo.toLocaleLowerCase('pt-BR').includes(searchTerm);
        return matchesFilter && matchesSearch;
      });

    // Renderização dos cards de pacientes
    if (elements.queueBody) {
      if (visible.length > 0) {
        elements.queueBody.innerHTML = visible
          .map((p) => {
            const statusLabelMap = {
              waiting: 'Aguardando',
              service: 'Em atendimento',
              done: 'Concluído'
            };
            const statusLabel = statusLabelMap[p.status] || p.status;

            const waitTimeDisplay =
              p.status === 'done'
                ? '—'
                : `${p.espera_minutos || 0} min`;

            // Mapeamento de cor da prioridade/risco
            const riscoLower = (p.risco || 'normal').toLowerCase();
            const priorityClass = `priority-${riscoLower}`;

            // Botões de ação para Médico/Enfermeiro
            let actionsHtml = '';
            if (p.status === 'waiting') {
              actionsHtml = `
                <div class="card-actions">
                  <button type="button" class="btn-action btn-action-start" data-action="service" data-id="${p.id}">
                    <i data-lucide="stethoscope"></i> Iniciar Atendimento
                  </button>
                  <button type="button" class="btn-action-link" data-ficha="${p.id}">
                    <i data-lucide="file-text"></i> Ver Ficha
                  </button>
                </div>
              `;
            } else if (p.status === 'service') {
              actionsHtml = `
                <div class="card-actions">
                  <button type="button" class="btn-action btn-action-finish" data-action="done" data-id="${p.id}">
                    <i data-lucide="check-circle-2"></i> Concluir Atendimento
                  </button>
                  <button type="button" class="btn-action btn-action-reopen" data-action="waiting" data-id="${p.id}" title="Devolver à fila de espera">
                    <i data-lucide="rotate-ccw"></i> Devolver à Fila
                  </button>
                  <button type="button" class="btn-action-link" data-ficha="${p.id}">
                    <i data-lucide="file-text"></i> Ver Ficha
                  </button>
                </div>
              `;
            } else if (p.status === 'done') {
              actionsHtml = `
                <div class="card-actions">
                  <button type="button" class="btn-action btn-action-reopen" data-action="service" data-id="${p.id}">
                    <i data-lucide="rotate-ccw"></i> Reabrir Atendimento
                  </button>
                  <button type="button" class="btn-action-link" data-ficha="${p.id}">
                    <i data-lucide="file-text"></i> Ver Ficha
                  </button>
                </div>
              `;
            }

            return `
              <article class="queue-card" aria-label="${p.position}º na ordem de chegada: ${escapeHtml(p.nome)}">
                <div class="card-top">
                  <div class="card-identity">
                    <span class="position" aria-label="Ordem ${p.position}">
                      ${p.position.toString().padStart(2, '0')}
                    </span>
                    <div>
                      <div class="patient">${escapeHtml(p.nome)}</div>
                      <div class="patient-id">RH: ${escapeHtml(p.codigo)}</div>
                    </div>
                  </div>
                  <span class="pill status-${p.status}">${statusLabel}</span>
                </div>
                <div class="card-details">
                  <div class="card-detail">
                    <span class="card-detail-label">Chegada</span>
                    <span>${escapeHtml(p.chegada_hora)}</span>
                  </div>
                  <div class="card-detail">
                    <span class="card-detail-label">Tempo de espera</span>
                    <span class="wait">${waitTimeDisplay}</span>
                  </div>
                  <div class="card-detail">
                    <span class="card-detail-label">Classificação / Risco</span>
                    <span class="pill ${priorityClass}">${escapeHtml(p.risco)}</span>
                  </div>
                  <div class="card-detail">
                    <span class="card-detail-label">Especialidade FAU</span>
                    <span>${escapeHtml(p.especialidade || '—')}</span>
                  </div>
                </div>
                ${actionsHtml}
              </article>
            `;
          })
          .join('');
      } else {
        elements.queueBody.innerHTML = `
          <div class="empty">Nenhum paciente encontrado para este filtro.</div>
        `;
      }
    }

    // Rodapé informativo
    if (elements.resultCount) {
      elements.resultCount.textContent = `${visible.length} ${
        visible.length === 1 ? 'paciente exibido' : 'pacientes exibidos'
      }`;
    }

    if (elements.updatedAt) {
      elements.updatedAt.textContent =
        'Horários atualizados às ' +
        now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    // Atualiza ícones do Lucide
    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  /**
   * Busca os pacientes da API do Django
   */
  async function carregarPacientes(silencioso = false) {
    if (isFetching) return;
    isFetching = true;

    if (!silencioso && elements.refreshButton) {
      elements.refreshButton.classList.add('loading');
    }

    try {
      const url = window.APP_CONFIG?.apiPacientesUrl || '/api/dashboard/pacientes/';
      const response = await fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });

      if (!response.ok) {
        if (response.status === 403) {
          showToast('Sessão expirada ou sem permissão.', 'error');
          setTimeout(() => window.location.reload(), 2000);
          return;
        }
        throw new Error('Falha ao obter dados dos pacientes');
      }

      const data = await response.json();
      patientsData = data.pacientes || [];
      render();
    } catch (err) {
      console.error(err);
      if (!silencioso) {
        showToast('Erro ao atualizar fila de atendimento.', 'error');
      }
    } finally {
      isFetching = false;
      if (elements.refreshButton) {
        elements.refreshButton.classList.remove('loading');
      }
    }
  }

  /**
   * Altera o status do paciente via API
   */
  async function alterarStatus(pacienteId, novoStatus) {
    try {
      const baseUrl = window.APP_CONFIG?.apiStatusBaseUrl || '/api/dashboard/paciente/';
      const url = `${baseUrl}${pacienteId}/status/`;

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ status: novoStatus })
      });

      const resData = await response.json();

      if (!response.ok) {
        showToast(resData.erro || 'Não foi possível alterar status.', 'error');
        return;
      }

      const statusMsg = {
        service: 'Atendimento iniciado com sucesso!',
        done: 'Atendimento concluído com sucesso!',
        waiting: 'Paciente retornado à fila de espera.'
      }[novoStatus] || 'Status atualizado!';

      showToast(statusMsg, 'success');
      await carregarPacientes(true);
    } catch (err) {
      console.error(err);
      showToast('Erro na conexão ao alterar status.', 'error');
    }
  }

  // Delegação de eventos para botões de ação nos cards
  if (elements.queueBody) {
    elements.queueBody.addEventListener('click', (e) => {
      const fichaBtn = e.target.closest('[data-ficha]');
      if (fichaBtn) {
        abrirFicha(fichaBtn.getAttribute('data-ficha'));
        return;
      }
      const btn = e.target.closest('.btn-action[data-action]');
      if (!btn) return;
      const pacienteId = btn.getAttribute('data-id');
      const action = btn.getAttribute('data-action');
      if (pacienteId && action) {
        alterarStatus(pacienteId, action);
      }
    });
  }

  /* ------------------------------------------------------------------
   * Modal "Ver Ficha"
   * ------------------------------------------------------------------ */
  const modal = {
    overlay: document.getElementById('ficha-modal'),
    dialog: document.querySelector('#ficha-modal .modal'),
    avatar: document.getElementById('ficha-avatar'),
    nome: document.getElementById('ficha-nome'),
    codigo: document.getElementById('ficha-codigo'),
    body: document.getElementById('ficha-body'),
    foot: document.getElementById('ficha-foot')
  };
  let fichaAbertaId = null;
  let ultimoFoco = null;

  const STATUS_LABEL = { waiting: 'Aguardando', service: 'Em atendimento', done: 'Concluído' };

  function formatarEspera(minutos) {
    const m = Math.max(0, Math.floor(Number(minutos) || 0));
    if (m < 60) return `${m} min`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ${m % 60}min`;
    return `${Math.floor(h / 24)}d ${h % 24}h`;
  }

  function iniciais(nome) {
    const partes = String(nome || '').trim().split(/\s+/).filter(Boolean);
    if (!partes.length) return '--';
    const primeira = partes[0][0] || '';
    const ultima = partes.length > 1 ? partes[partes.length - 1][0] : '';
    return (primeira + ultima).toUpperCase();
  }

  function infoItem(rotulo, valor) {
    return `
      <div class="ficha-info">
        <span class="card-detail-label">${rotulo}</span>
        <span class="ficha-info-value">${valor}</span>
      </div>`;
  }

  function renderGrupo(grupo) {
    const total = grupo.itens.length;
    const feitos = grupo.itens.filter((i) => i.concluido).length;
    const conteudo = total
      ? `<ul class="ficha-list">${grupo.itens.map((i) => `
          <li class="ficha-item ${i.concluido ? 'is-done' : 'is-pending'}">
            <span class="ficha-item-icon"><i data-lucide="${i.concluido ? 'check' : 'clock-3'}"></i></span>
            <span class="ficha-item-label">${escapeHtml(i.rotulo)}</span>
            <span class="ficha-item-state">${i.concluido ? 'Concluído' : 'Pendente'}</span>
          </li>`).join('')}</ul>`
      : '<p class="ficha-empty">Nenhuma solicitação registrada.</p>';

    return `
      <section class="ficha-group">
        <div class="ficha-group-head">
          <h3>${escapeHtml(grupo.titulo)}</h3>
          ${total ? `<span class="ficha-count">${feitos}/${total} concluídos</span>` : ''}
        </div>
        ${conteudo}
      </section>`;
  }

  function renderFicha(p) {
    const riscoClasse = `priority-${String(p.risco || 'normal').toLowerCase()}`;

    modal.avatar.textContent = iniciais(p.nome);
    modal.nome.textContent = p.nome;
    modal.codigo.textContent = `RH: ${p.codigo}`;

    modal.body.innerHTML = `
      <div class="ficha-badges">
        <span class="pill status-${p.status}">${STATUS_LABEL[p.status] || escapeHtml(p.status_label)}</span>
        <span class="pill ${riscoClasse}">Risco: ${escapeHtml(p.risco || '—')}</span>
      </div>

      <div class="ficha-info-grid">
        ${infoItem('Data de entrada', escapeHtml(p.entrada_data))}
        ${infoItem('Hora de entrada', escapeHtml(p.entrada_hora))}
        ${infoItem('Tempo desde a entrada', p.status === 'done' ? '—' : formatarEspera(p.espera_minutos))}
        ${infoItem('Especialidade FAU', escapeHtml(p.especialidade || '—'))}
        ${infoItem('Hora do 1º atendimento', escapeHtml(p.hora_primeiro_atendimento || '—'))}
        ${infoItem('Classificação de risco', escapeHtml(p.risco || '—'))}
      </div>

      <div class="ficha-groups">
        ${p.grupos.map(renderGrupo).join('')}
      </div>
    `;

    let acoes = '';
    if (p.status === 'waiting') {
      acoes = `<button type="button" class="btn-action btn-action-start" data-modal-action="service">
                 <i data-lucide="stethoscope"></i> Iniciar Atendimento</button>`;
    } else if (p.status === 'service') {
      acoes = `<button type="button" class="btn-action btn-action-finish" data-modal-action="done">
                 <i data-lucide="check-circle-2"></i> Concluir Atendimento</button>
               <button type="button" class="btn-action btn-action-reopen" data-modal-action="waiting">
                 <i data-lucide="rotate-ccw"></i> Devolver à Fila</button>`;
    } else {
      acoes = `<button type="button" class="btn-action btn-action-reopen" data-modal-action="service">
                 <i data-lucide="rotate-ccw"></i> Reabrir Atendimento</button>`;
    }

    modal.foot.innerHTML = `
      <a href="${p.url_admin}" target="_blank" class="btn-action-link">
        <i data-lucide="pencil"></i> Editar cadastro
      </a>
      <div class="modal-foot-actions">${acoes}</div>
    `;

    if (window.lucide) window.lucide.createIcons();
  }

  async function carregarFicha(id) {
    const base = window.APP_CONFIG?.apiDetalheBaseUrl || '/api/dashboard/paciente/';
    const response = await fetch(`${base}${id}/`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!response.ok) throw new Error('Falha ao carregar a ficha');
    return response.json();
  }

  async function abrirFicha(id) {
    if (!modal.overlay) return;
    fichaAbertaId = id;
    ultimoFoco = document.activeElement;

    modal.nome.textContent = 'Carregando...';
    modal.codigo.textContent = '';
    modal.avatar.textContent = '--';
    modal.body.innerHTML = '<div class="modal-loading">Carregando ficha...</div>';
    modal.foot.innerHTML = '';

    modal.overlay.classList.add('is-open');
    modal.overlay.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    modal.dialog.focus();

    try {
      const dados = await carregarFicha(id);
      if (fichaAbertaId === id) renderFicha(dados);
    } catch (err) {
      console.error(err);
      modal.body.innerHTML = '<div class="modal-loading">Não foi possível carregar a ficha do paciente.</div>';
    }
  }

  function fecharFicha() {
    if (!modal.overlay || !modal.overlay.classList.contains('is-open')) return;
    modal.overlay.classList.remove('is-open');
    modal.overlay.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    fichaAbertaId = null;
    if (ultimoFoco && ultimoFoco.focus) ultimoFoco.focus();
  }

  if (modal.overlay) {
    // Fecha ao clicar fora da ficha (no fundo desfocado) ou no botão X
    modal.overlay.addEventListener('click', (e) => {
      if (e.target === modal.overlay || e.target.closest('[data-close-modal]')) {
        fecharFicha();
      }
    });

    // Ações de status dentro da ficha
    modal.foot.addEventListener('click', async (e) => {
      const btn = e.target.closest('[data-modal-action]');
      if (!btn || !fichaAbertaId) return;
      const id = fichaAbertaId;
      btn.disabled = true;
      await alterarStatus(id, btn.getAttribute('data-modal-action'));
      try {
        const dados = await carregarFicha(id);
        if (fichaAbertaId === id) renderFicha(dados);
      } catch (err) {
        console.error(err);
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') fecharFicha();
  });

  // Busca e Filtros
  if (elements.patientSearch) {
    elements.patientSearch.addEventListener('input', render);
  }

  elements.filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      currentFilter = button.dataset.filter;
      elements.filterButtons.forEach((btn) => {
        const isActive = btn === button;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-pressed', String(isActive));
      });
      render();
    });
  });

  if (elements.refreshButton) {
    elements.refreshButton.addEventListener('click', () => {
      carregarPacientes(false);
      showToast('Fila de atendimento atualizada!', 'success');
    });
  }

  // Inicialização
  document.addEventListener('DOMContentLoaded', () => {
    updateHeaderDate();
    carregarPacientes(false);

    // Auto-atualização periódica a cada 30 segundos
    setInterval(() => {
      carregarPacientes(true);
    }, 30000);
  });
})();
