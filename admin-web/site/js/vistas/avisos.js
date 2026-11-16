import { api } from '../api.js';
import { esc, fechaHora } from '../util.js';

const TIPOS = {
  pago_confirmado: ['Pago confirmado', 'success'],
  pago_reportado: ['Pago reportado', 'primary'],
  pago_fallido: ['Pago fallido', 'danger'],
  pago_anulado: ['Pago anulado', 'secondary'],
};

function etiqueta(tipo) {
  const [texto, color] = TIPOS[tipo] ?? [tipo, 'secondary'];
  return `<span class="badge text-bg-${color}">${esc(texto)}</span>`;
}

export async function vistaAvisos(contenido) {
  const avisos = await api.notificaciones(false);
  let filtro = 'no-leidas';

  const fila = (n) => `
    <li class="list-group-item d-flex justify-content-between align-items-center ${n.leida ? 'text-muted' : ''}">
      <div>
        <div>${etiqueta(n.tipo)} <span class="ms-1">${esc(n.mensaje)}</span></div>
        <small class="text-muted">${esc(fechaHora(n.creado_en))}</small>
      </div>
      ${
        n.leida
          ? '<span class="badge text-bg-light border">Leída</span>'
          : `<button class="btn btn-sm btn-outline-secondary ms-3" data-leida="${esc(n.id)}">Marcar leída</button>`
      }
    </li>`;

  function pintar() {
    const noLeidas = avisos.filter((n) => !n.leida);
    const leidas = avisos.filter((n) => n.leida);
    const visibles = filtro === 'no-leidas' ? noLeidas : filtro === 'leidas' ? leidas : avisos;

    const boton = (clave, texto, cantidad) => `
      <button type="button" class="btn btn-sm ${filtro === clave ? 'btn-primary' : 'btn-outline-primary'}" data-filtro="${clave}">
        ${esc(texto)} (${cantidad})
      </button>`;

    contenido.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">Avisos</h5>
        <div class="btn-group">
          ${boton('no-leidas', 'No leídas', noLeidas.length)}
          ${boton('leidas', 'Leídas', leidas.length)}
          ${boton('todas', 'Todas', avisos.length)}
        </div>
      </div>
      <div class="card shadow-sm">
        <ul class="list-group list-group-flush">
          ${
            visibles.map(fila).join('') ||
            '<li class="list-group-item text-center text-muted py-4">No hay avisos en esta lista</li>'
          }
        </ul>
      </div>`;

    contenido.querySelectorAll('[data-filtro]').forEach((b) =>
      b.addEventListener('click', () => {
        filtro = b.dataset.filtro;
        pintar();
      })
    );

    contenido.querySelectorAll('[data-leida]').forEach((b) =>
      b.addEventListener('click', async () => {
        b.disabled = true;
        try {
          await api.marcarLeida(b.dataset.leida);
          const aviso = avisos.find((n) => String(n.id) === b.dataset.leida);
          if (aviso) aviso.leida = true;
          pintar(); 
        } catch (err) {
          alert(err.message);
          b.disabled = false;
        }
      })
    );
  }

  pintar();
}