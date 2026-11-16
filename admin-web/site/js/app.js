import { NOMBRE_APP } from './config.js';
import { api, sesion } from './api.js';
import { esc } from './util.js';
import { vistaInicio } from './vistas/inicio.js';
import { vistaAvisos } from './vistas/avisos.js';

const RUTAS = {
  inicio: { vista: vistaInicio },
  avisos: { vista: vistaAvisos }, 
};

const MENU = [
  ['inicio', 'Inicio'],
  ['apartamentos', 'Apartamentos'],
  ['cuotas', 'Cuotas'],
  ['pagos', 'Pagos'],
  ['deudas', 'Deudas'],
  ['avisos', 'Avisos'],
];

const app = document.getElementById('app');
document.title = NOMBRE_APP;
let conjunto = null;

function pantallaLogin(mensaje = '') {
  app.innerHTML = `
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-sm-8 col-md-5 col-lg-4">
          <div class="text-center mt-5 mb-4">
            <h3 class="fw-bold text-primary">${esc(NOMBRE_APP)}</h3>
            <p class="text-muted">Acceso para administradores</p>
          </div>
          <div class="card shadow-sm">
            <div class="card-body p-4">
              <form id="form-login">
                <div class="mb-3">
                  <label class="form-label">Usuario</label>
                  <input class="form-control" name="usuario" autocomplete="username" required autofocus>
                </div>
                <div class="mb-3">
                  <label class="form-label">Contraseña</label>
                  <div class="input-group">
                    <input class="form-control" type="password" name="password" id="campo-password" autocomplete="current-password" required>
                    <button class="btn btn-outline-secondary" type="button" id="ver-password" aria-label="Mostrar contraseña">Mostrar</button>
                  </div>
                </div>
                <div id="error-login" class="text-danger small mb-2">${esc(mensaje)}</div>
                <button class="btn btn-primary w-100" type="submit">Ingresar</button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>`;

  const campo = document.getElementById('campo-password');
  const ver = document.getElementById('ver-password');
  ver.addEventListener('click', () => {
    const oculta = campo.type === 'password';
    campo.type = oculta ? 'text' : 'password';
    ver.textContent = oculta ? 'Ocultar' : 'Mostrar';
    ver.setAttribute('aria-label', oculta ? 'Ocultar contraseña' : 'Mostrar contraseña');
  });

  document.getElementById('form-login').addEventListener('submit', async (e) => {
    e.preventDefault();
    const boton = e.target.querySelector('button[type="submit"]');
    const datos = new FormData(e.target);
    boton.disabled = true;
    try {
      const r = await api.login(datos.get('usuario').trim().toLowerCase(), datos.get('password'));
      sesion.guardar({ token: r.token, administrador: r.administrador });
      iniciar();
    } catch (err) {
      document.getElementById('error-login').textContent = err.message;
      boton.disabled = false;
    }
  });
}

function pintarMarco(admin) {
  const enlaces = MENU.filter(([clave]) => RUTAS[clave])
    .map(
      ([clave, titulo]) =>
        `<li class="nav-item"><a class="nav-link" data-ruta="${clave}" href="#/${clave}">${esc(titulo)}</a></li>`
    )
    .join('');

  app.innerHTML = `
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container">
        <a class="navbar-brand fw-bold" href="#/inicio">${esc(NOMBRE_APP)}</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#menu">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="menu">
          <ul class="navbar-nav me-auto">${enlaces}</ul>
          <span class="navbar-text me-3">${esc(admin.nombre || admin.usuario)}</span>
          <button class="btn btn-outline-light btn-sm" id="salir">Salir</button>
        </div>
      </div>
    </nav>
    <div class="container mt-4" id="contenido"></div>
    <footer class="text-center text-muted py-4 mt-5 border-top">
      <small>${esc(NOMBRE_APP)} &copy; ${new Date().getFullYear()} — ${esc(conjunto?.nombre ?? '')}</small>
    </footer>`;

  document.getElementById('salir').addEventListener('click', () => {
    sesion.cerrar();
    pantallaLogin();
  });
}

async function navegar() {
  if (!sesion.leer()) return;
  const clave = location.hash.replace(/^#\//, '').split('?')[0] || 'inicio';
  const ruta = RUTAS[clave] ?? RUTAS.inicio;

  document
    .querySelectorAll('[data-ruta]')
    .forEach((a) => a.classList.toggle('active', a.dataset.ruta === clave));

  const contenido = document.getElementById('contenido');
  if (!contenido) return;
  contenido.innerHTML = '<div class="text-center text-muted py-5">Cargando…</div>';

  try {
    await ruta.vista(contenido, { conjunto, recargar: navegar });
  } catch (err) {
    if (err.codigo === 401) return; // ya se mostró el login
    contenido.innerHTML = `<div class="alert alert-danger">${esc(err.message)}</div>`;
  }
}

async function iniciar() {
  const s = sesion.leer();
  if (!s) return pantallaLogin();
  try {
    conjunto = await api.conjunto();
  } catch (err) {
    if (err.codigo === 401) return;
    conjunto = null; // sin el nombre del conjunto igual se puede trabajar
  }
  pintarMarco(s.administrador);
  navegar();
}

window.addEventListener('hashchange', navegar);
window.addEventListener('sesion-expirada', () =>
  pantallaLogin('Tu sesión expiró. Inicia sesión de nuevo.')
);
iniciar();