export function esc(valor) {
    return String(valor ?? '') 
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

const formatoPesos = new Intl.NumberFormat('es-CO', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

export function pesos(valor) {
  const n = Number(valor);
  return '$ ' + formatoPesos.format(Number.isFinite(n) ? n : 0);
}

export function fecha(iso) {
  if (!iso) return '';
  const [a, m, d] = String(iso).slice(0, 10).split('-');
  return `${d}/${m}/${a}`;
}

export function fechaHora(iso) {
  if (!iso) return '';
  const texto = String(iso);
  const fecha = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(texto) ? texto : texto + 'Z');
  return fecha.toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' });
}

const COLOR_GESTION = {
  'Normal': 'success',
  'Pre-Juridico': 'warning',
  'Juridico': 'danger',
  'Acuerdo': 'info',
};
const NOMBRE_GESTION = { 'Pre-Juridico': 'Pre-jurídico', 'Juridico': 'Jurídico' };

export function badgeGestion(estado) {
  const color = COLOR_GESTION[estado] ?? 'secondary';
  const nombre = NOMBRE_GESTION[estado] ?? estado;
  return `<span class="badge text-bg-${color}">${esc(nombre)}</span>`;
}

const COLOR_PAGO = {
  pendiente: 'warning',
  confirmado: 'success',
  fallido: 'danger',
  anulado: 'secondary',
};

export function badgePago(estado) {
  const color = COLOR_PAGO[estado] ?? 'secondary';
  return `<span class="badge text-bg-${color}">${esc(estado)}</span>`;
}