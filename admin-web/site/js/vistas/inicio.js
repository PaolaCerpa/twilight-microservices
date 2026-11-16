import { api } from '../api.js';
import { badgeGestion, esc, fechaHora, pesos } from '../util.js';

export async function vistaInicio(contenido, { conjunto, recargar }) {
  const [resumen, deudas, apartamentos, avisos] = await Promise.all([
    api.resumen(),
    api.deudas(),
    api.apartamentos(),
    api.notificaciones(true),
  ]);

  const porId = new Map(apartamentos.map((a) => [a.id, a]));
  const activos = apartamentos.filter((a) => a.activo).length;
  const deudores = deudas
    .filter((d) => Number(d.saldo) > 0)
    .sort((a, b) => Number(b.saldo) - Number(a.saldo));
  const direccion = [conjunto?.direccion, conjunto?.ciudad].filter(Boolean).join(' — ');

  const tarjeta = (valor, texto, clase = '') => `
    <div class="col-sm-6 col-lg-3">
      <div class="card text-center shadow-sm border-0">
        <div class="card-body">
          <div class="fs-4 fw-bold ${clase}">${esc(valor)}</div>
          <div class="text-muted small">${esc(texto)}</div>
        </div>
      </div>
    </div>`;

  const bloqueAvisos = avisos.length
    ? `
    <div class="card shadow-sm mb-4 border-0">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <span>
          <span class="fw-semibold">Avisos de pagos</span>
          <span class="badge text-bg-light ms-2">${avisos.length}</span>
        </span>
        <a href="#/avisos" class="btn btn-sm btn-light">Ver historial</a>
      </div>
      <ul class="list-group list-group-flush">
        ${avisos
          .map(
            (n) => `
          <li class="list-group-item d-flex justify-content-between align-items-center">
            <div>
              <div>${esc(n.mensaje)}</div>
              <small class="text-muted">${esc(fechaHora(n.creado_en))}</small>
            </div>
            <button class="btn btn-sm btn-outline-secondary ms-3" data-leida="${esc(n.id)}">
              Marcar leída
            </button>
          </li>`
          )
          .join('')}
      </ul>
    </div>`
    : '<div class="text-muted small mb-4">No tienes avisos nuevos. <a href="#/avisos>Ver historial</a></div>';

  const filas = deudores
    .slice(0, 10)
    .map((d) => {
      const a = porId.get(d.apartamento_id);
      return `
        <tr>
          <td>${esc(a?.bloque ?? '—')}</td>
          <td><strong>${esc(a?.apto ?? '—')}</strong></td>
          <td>${esc(a?.propietario || '—')}</td>
          <td>${badgeGestion(d.estado_gestion)}</td>
          <td class="text-end text-danger fw-bold">${esc(pesos(d.saldo))}</td>
        </tr>`;
    })
    .join('');

  contenido.innerHTML = `
    <div class="mb-4">
      <h4 class="mb-0">Panel Principal</h4>
      <p class="text-muted small">${esc(conjunto?.nombre ?? '')}${direccion ? ' — ' + esc(direccion) : ''}</p>
    </div>

    <div class="row g-3 mb-4">
      ${tarjeta(activos, 'Apartamentos')}
      ${tarjeta(pesos(resumen.total_deuda), 'Total en deuda', 'text-danger')}
      ${tarjeta(pesos(resumen.total_recaudado), 'Total recaudado', 'text-success')}
      ${tarjeta(resumen.juridicos, 'Procesos jurídicos', 'text-warning')}
    </div>

    ${bloqueAvisos}

    <div class="card shadow-sm">
      <div class="card-header bg-white d-flex justify-content-between align-items-center">
        <span class="fw-semibold">Apartamentos con deuda</span>
        <a href="#/deudas" class="btn btn-sm btn-outline-primary">Ver reporte completo</a>
      </div>
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead class="table-light">
            <tr>
              <th>Bloque</th><th>Apto</th><th>Propietario</th><th>Estado</th>
              <th class="text-end">Deuda</th>
            </tr>
          </thead>
          <tbody>
            ${filas || '<tr><td colspan="5" class="text-center text-muted py-4">Sin deudas registradas</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>`;

  contenido.querySelectorAll('[data-leida]').forEach((boton) =>
    boton.addEventListener('click', async () => {
      boton.disabled = true;
      try {
        await api.marcarLeida(boton.dataset.leida);
        recargar();
      } catch (err) {
        alert(err.message);
        boton.disabled = false;
      }
    })
  );
}