const CLAVE = 'sesion_admin';

export const sesion = {
  leer() {
    try {
      return JSON.parse(sessionStorage.getItem(CLAVE));
    } catch {
      return null;
    }
  },
  guardar(datos) {
    sessionStorage.setItem(CLAVE, JSON.stringify(datos));
  },
  cerrar() {
    sessionStorage.removeItem(CLAVE);
  },
};

export class ErrorApi extends Error {
  constructor(mensaje, codigo) {
    super(mensaje);
    this.codigo = codigo;
  }
}

function mensajeDe(datos, codigo) {
  if (datos && typeof datos === 'object') {
    if (typeof datos.error === 'string') return datos.error;
    if (typeof datos.detail === 'string') return datos.detail;
    if (Array.isArray(datos.detail)) return datos.detail.map((d) => d.msg).join('. ');
    const campos = Object.entries(datos).filter(([, v]) => Array.isArray(v));
    if (campos.length) return campos.map(([c, v]) => `${c}: ${v.join(', ')}`).join('. ');
  }
  return `Error del servidor (${codigo}).`;
}

async function pedir(metodo, ruta, cuerpo) {
  const s = sesion.leer();
  const headers = {};
  if (cuerpo !== undefined) headers['Content-Type'] = 'application/json';
  if (s?.token) headers['Authorization'] = `Bearer ${s.token}`;

  let respuesta;
  try {
    respuesta = await fetch(`/api${ruta}`, {
      method: metodo,
      headers,
      body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    throw new ErrorApi('No se pudo conectar con el servidor.', 0);
  }

  let datos = null;
  try {
    datos = await respuesta.json();
  } catch {
  }

  if (respuesta.status === 401 && s) {
    sesion.cerrar();
    window.dispatchEvent(new Event('sesion-expirada'));
    throw new ErrorApi('Tu sesión expiró. Inicia sesión de nuevo.', 401);
  }
  if (!respuesta.ok) throw new ErrorApi(mensajeDe(datos, respuesta.status), respuesta.status);
  return datos;
}

export const api = {
  login: (usuario, password) => pedir('POST', '/admin/login', { usuario, password }),
  conjunto: () => pedir('GET', '/admin/conjunto'),

  apartamentos: () => pedir('GET', '/admin/apartamentos'),
  crearApartamento: (datos) => pedir('POST', '/admin/apartamentos', datos),
  editarApartamento: (id, datos) => pedir('PATCH', `/admin/apartamentos/${id}`, datos),
  gestion: (id, datos) => pedir('PUT', `/admin/apartamentos/${id}/gestion`, datos),

  resumen: () => pedir('GET', '/admin/resumen'),
  deudas: () => pedir('GET', '/admin/deudas'),

  cuotas: () => pedir('GET', '/admin/cuotas'),
  crearCuota: (datos) => pedir('POST', '/admin/cuotas', datos),
  cuotasMasivo: (datos) => pedir('POST', '/admin/cuotas/masivo', datos),
  eliminarCuota: (id) => pedir('DELETE', `/admin/cuotas/${id}`),

  pagos: (estado) =>
    pedir('GET', `/admin/pagos${estado ? `?estado=${encodeURIComponent(estado)}` : ''}`),
  registrarPago: (datos) => pedir('POST', '/admin/pagos', datos),
  anularPago: (id) => pedir('POST', `/admin/pagos/${id}/anular`),

  notificaciones: (soloNoLeidas = false) =>
    pedir('GET', `/admin/notificaciones?solo_no_leidas=${soloNoLeidas}`),
  marcarLeida: (id) => pedir('PATCH', `/admin/notificaciones/${id}/leida`),
};