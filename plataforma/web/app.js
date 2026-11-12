// Pantalla del juez de turno (T04). Habla solo con /api/* (coordinacion/contratos.md §5).
"use strict";

const REFRESCO_MS = 2000;
const TIEMPO_MAX_MS = 10000;
const CLAVE_PIN = "juez-pin";
const PROVEEDORES = { aurora: "Aurora", andina: "Andina", valle: "FibraValle", cumbre: "Cumbre" };
const ESTADOS_ORDEN = {
  enviando: "Enviando", recibida: "Recibida, aplicando", aplicada: "Bloqueado", fallida: "Falló, se reintenta",
  rechazada: "Rechazada", vencida: "Venció", levantada: "Levantada",
};

const $ = (id) => document.getElementById(id);
const estado = { pin: leerPin(), juez: null, minuto: 0, pendientes: [], vistos: new Set(), primeraCarga: true, licenciatarios: [], nombres: {} };
let audio = null;

// ---------------------------------------------------------------------- utilidades

// sessionStorage: el PIN no sobrevive al cierre de la pestaña (localStorage lo dejaba guardado en la máquina).
function leerPin() { try { return sessionStorage.getItem(CLAVE_PIN); } catch { return null; } }
function guardarPin(pin) { try { pin ? sessionStorage.setItem(CLAVE_PIN, pin) : sessionStorage.removeItem(CLAVE_PIN); } catch { /* sin storage */ } }

function nombreJuez(id) {
  if (!id) return "nadie";
  if (estado.nombres[id]) return estado.nombres[id];
  const [cargo, nombre] = id.split("-");
  const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : "");
  return `${cap(cargo)} ${cap(nombre)}`;
}
const proveedor = (id) => PROVEEDORES[id] || id;
const min = (m) => (m == null ? "—" : `${Math.floor(m)}'`);
function listaHumana(items) {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} y ${items[items.length - 1]}`;
}

async function api(ruta, cuerpo) {
  const opciones = { headers: { "Content-Type": "application/json" } };
  if (estado.pin) opciones.headers["X-Juez-Pin"] = estado.pin;
  if (cuerpo !== undefined) { opciones.method = "POST"; opciones.body = JSON.stringify(cuerpo); }
  const corte = new AbortController();
  const reloj = setTimeout(() => corte.abort(), TIEMPO_MAX_MS);
  opciones.signal = corte.signal;
  let r;
  try { r = await fetch(ruta, opciones); }
  catch (err) { throw new Error(err.name === "AbortError" ? "la plataforma no respondió a tiempo" : "sin conexión con la plataforma"); }
  finally { clearTimeout(reloj); }
  let datos = null;
  try { datos = await r.json(); } catch { /* sin cuerpo */ }
  if (r.status === 401) { pedirPin("El PIN no es correcto. Volvé a ingresarlo."); throw new Error("401"); }
  if (!r.ok) throw new Error((datos && datos.error) || `La plataforma respondió ${r.status}`);
  if (r.status === 202) return { ...(datos || {}), pendiente: true };
  return datos;
}

function aviso(texto, tipo = "info", { titulo = null, boton = null, id = null, duracion = 0 } = {}) {
  if (id) { const viejo = document.querySelector(`[data-aviso="${id}"]`); if (viejo) viejo.remove(); }
  const div = document.createElement("div");
  div.className = `aviso${tipo === "error" ? " aviso--error" : tipo === "ok" ? " aviso--ok" : ""}`;
  if (id) div.dataset.aviso = id;
  if (titulo) { const s = document.createElement("strong"); s.textContent = titulo; div.append(s); }
  const p = document.createElement("p"); p.textContent = texto; div.append(p);
  if (boton) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "boton boton--firmar boton--ancho"; b.textContent = boton.texto;
    b.addEventListener("click", boton.accion); div.append(b);
  }
  $("avisos").append(div);
  if (duracion) setTimeout(() => div.remove(), duracion);
  return div;
}
const quitarAviso = (id) => { const a = document.querySelector(`[data-aviso="${id}"]`); if (a) a.remove(); };

// ---------------------------------------------------------------------- avisos de pedido nuevo

function prepararAvisos() {
  estado.interactuo = true;   // el navegador solo deja vibrar o sonar después de un toque del usuario
  try { audio = audio || new (window.AudioContext || window.webkitAudioContext)(); } catch { audio = null; }
  if ("Notification" in window && Notification.permission === "default") Notification.requestPermission().catch(() => {});
}

function avisarNuevos(n) {
  if (estado.interactuo && navigator.vibrate) navigator.vibrate([120, 80, 120]);
  if (audio) {
    const o = audio.createOscillator(), g = audio.createGain();
    o.frequency.value = 880; g.gain.setValueAtTime(0.15, audio.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + 0.35);
    o.connect(g).connect(audio.destination); o.start(); o.stop(audio.currentTime + 0.35);
  }
  if (document.hidden && "Notification" in window && Notification.permission === "granted") {
    new Notification(n === 1 ? "Llegó un pedido de bloqueo" : `Llegaron ${n} pedidos de bloqueo`,
      { body: "Abrí la pantalla del juez para revisar la evidencia y firmar." });
  }
}

// ---------------------------------------------------------------------- textos del pedido

function textoBloqueo(p) {
  const r = p.resumen;
  const porIp = p.objetivos.filter((o) => o.tipo === "ip").map((o) => proveedor(o.proveedor_id));
  const porNombre = p.objetivos.filter((o) => o.tipo === "dominio").map((o) => proveedor(o.proveedor_id));
  if (r.tipo_recomendado === "ip") {
    let t = `La IP ${r.ip} en ${listaHumana(porIp)}.`;
    if (porNombre.length) t += ` En ${listaHumana(porNombre)}, el nombre ${r.host}, porque solo bloquea por nombre.`;
    return t;
  }
  // El cerebro ya explica por qué no se toca la IP (cuántos sitios ajenos o falta de datos): no se recalcula acá.
  const span = document.createElement("span");
  span.append(`Solo el nombre ${r.host}, en los ${p.objetivos.length} proveedores. `);
  const c = document.createElement("span");
  c.className = "compartida";
  c.textContent = `${r.motivo_tipo}.`;
  span.append(c);
  return span;
}

function textoPorque(r) {
  const span = document.createElement("span");
  span.append(r.motivo_clasificacion + ". ");
  const m = document.createElement("span"); m.className = "marca"; m.textContent = `Marca de agua ${r.marca}`;
  span.append(m);
  return span;
}

// ---------------------------------------------------------------------- render

function renderEstado(e) {
  estado.minuto = e.minuto_actual;
  estado.juez = (e.jueces_de_turno || [])[0] || null;
  if (e.licenciatarios) estado.licenciatarios = e.licenciatarios;
  for (const jz of (e.juzgados && e.juzgados.juzgados) || []) for (const j of jz.jueces) estado.nombres[j.id] = j.nombre;
  $("minuto").textContent = Math.floor(e.minuto_actual);
  $("partido").textContent = e.finalizado ? `Partido ${e.partido_id} terminado` : `Partido ${e.partido_id} en juego`;
  $("juez").textContent = nombreJuez(estado.juez);
  $("avance").style.width = `${Math.min(100, (100 * e.minuto_actual) / e.fin_min)}%`;
  const marca = $("marca-turno");
  if (e.proximo_cambio_turno_min != null && e.proximo_cambio_turno_min < e.fin_min) {
    marca.hidden = false;
    marca.style.left = `${(100 * e.proximo_cambio_turno_min) / e.fin_min}%`;
    $("nota-turno").textContent = `Cambio de turno en el minuto ${Math.floor(e.proximo_cambio_turno_min)}`;
  } else { marca.hidden = true; $("nota-turno").textContent = ""; }

  if (!estado.juez && !e.finalizado) {
    aviso("En este minuto no figura ningún juez de turno. Los pedidos quedan esperando hasta que entre uno.", "error",
      { id: "sin-juez", titulo: "Sin juez de turno" });
  } else quitarAviso("sin-juez");

  if (!e.simulador_ok) {
    aviso("La plataforma no recibe datos del partido hace unos segundos. Los pedidos nuevos pueden demorar.", "error",
      { id: "desconectado", titulo: "Motor desconectado" });
  } else quitarAviso("desconectado");

  if (estado.juez && e.turno_ratificado === false) {
    if (!document.querySelector('[data-aviso="traspaso"]')) {
      aviso(`${nombreJuez(estado.juez)}: las órdenes que firmó el turno anterior siguen vigentes. Asumí el turno para ratificarlas; hasta entonces sus reintentos quedan en espera.`,
        "info", { id: "traspaso", titulo: "Cambió el turno", boton: { texto: "Asumir turno y ratificar órdenes", accion: asumirTurno } });
    }
  } else quitarAviso("traspaso");
}

function renderPedidos(pedidos) {
  estado.pendientes = pedidos;
  const lista = $("pedidos");
  const nuevos = pedidos.filter((p) => !estado.vistos.has(p.pedido_id));
  const ids = new Set(pedidos.map((p) => p.pedido_id));
  for (const li of [...lista.children]) if (!ids.has(li.dataset.id)) li.remove();
  for (const p of pedidos) {
    if (lista.querySelector(`[data-id="${p.pedido_id}"]`)) continue;
    lista.append(crearTarjeta(p, !estado.primeraCarga));
  }
  pedidos.forEach((p) => estado.vistos.add(p.pedido_id));
  if (nuevos.length && !estado.primeraCarga) avisarNuevos(nuevos.length);
  estado.primeraCarga = false;

  const n = pedidos.length;
  $("cuenta").textContent = n;
  $("vacio").hidden = n > 0;
  document.title = n ? `(${n}) Juez de turno` : "Juez de turno";
  const boton = $("firmar-todos");
  boton.disabled = n === 0 || !estado.juez;
  const como = estado.juez ? ` como ${nombreJuez(estado.juez)}` : "";
  boton.textContent = n === 0 ? "No hay pedidos para firmar" : n === 1 ? `Firmar el pedido${como}` : `Firmar los ${n} pedidos${como}`;
}

function crearTarjeta(p, esNuevo) {
  const r = p.resumen;
  const li = $("tpl-pedido").content.firstElementChild.cloneNode(true);
  li.dataset.id = p.pedido_id;
  if (esNuevo) li.classList.add("pedido--nuevo");
  li.querySelector(".pedido__sitio").textContent = r.host;
  li.querySelector(".pedido__cuando").textContent = `detectado ${min(r.primer_minuto)}`;
  li.querySelector(".d-porque").append(textoPorque(r));
  li.querySelector(".d-servidor").textContent =
    `Servidor ${r.ip}${r.organizacion ? `, de ${r.organizacion}` : ""}.`;
  li.querySelector(".d-bloqueo").append(textoBloqueo(p));
  li.querySelector(".d-hasta").textContent = `Minuto ${p.vence_min}, fin del partido. Después se levanta sola.`;

  // Se pide apenas se crea la tarjeta; al abrir se reintenta si todavía no llegó o falló.
  const exp = li.querySelector(".expediente"), cuerpo = exp.querySelector(".expediente__cuerpo");
  cargarExpediente(p, cuerpo);
  exp.addEventListener("toggle", () => { if (exp.open && cuerpo.dataset.cargado !== "si") cargarExpediente(p, cuerpo); });

  const rechazo = li.querySelector(".rechazo"), acciones = li.querySelector(".b-acciones");
  li.querySelector(".b-firmar").addEventListener("click", () => firmar([p.pedido_id]));
  li.querySelector(".b-rechazar").addEventListener("click", () => {
    rechazo.hidden = false; acciones.hidden = true; rechazo.querySelector("textarea").focus();
  });
  li.querySelector(".b-cancelar").addEventListener("click", () => { rechazo.hidden = true; acciones.hidden = false; });
  li.querySelector(".b-confirmar-rechazo").addEventListener("click", () => {
    const motivo = rechazo.querySelector("textarea").value.trim();
    if (!motivo) { rechazo.querySelector("textarea").focus(); return; }
    rechazar([p.pedido_id], motivo);
  });
  return li;
}

async function cargarExpediente(p, cuerpo) {
  if (cuerpo.dataset.cargado === "cargando") return;
  cuerpo.dataset.cargado = "cargando";
  cuerpo.textContent = "Cargando…";
  try {
    const e = await api(`/api/expedientes/${encodeURIComponent(p.expediente_id)}`);
    const c = e.caso;
    cuerpo.replaceChildren();
    const fila = (titulo, valor, clase) => {
      const f = document.createElement("p"); const b = document.createElement("b");
      b.textContent = `${titulo}: `; f.append(b);
      const s = document.createElement("span"); if (clase) s.className = clase; s.textContent = valor; f.append(s);
      cuerpo.append(f);
    };
    fila("Expediente", e.expediente_id);
    fila("Dominio", c.host);
    if (c.pagina) fila("Página", c.pagina);
    fila("IP", c.ip);
    fila("Hosting", c.organizacion ? `${c.organizacion}${c.asn ? ` (ASN ${c.asn})` : ""}` : "sin datos del ASN");
    fila("Marca de agua", `${c.marca || "sin marca"}${c.marca_origen ? `, ${c.marca_origen}` : ""}`, "marca");
    fila("Por qué es el partido", c.motivo_clasificacion);
    const lics = estado.licenciatarios.map((l) => `${l.nombre}: ${l.dominios_autorizados.join(", ")}`);
    fila("Licenciatarios autorizados", lics.length ? `${lics.join("  |  ")}. ${c.host} no es ninguno de ellos.` : "el partido no declara licenciatarios");
    fila("Sitios en la misma IP", c.dominios_en_ip.length ? c.dominios_en_ip.join(", ") : "sin datos");
    fila("Por qué IP o nombre", c.motivo_tipo);
    fila("Qué recibe cada proveedor", p.objetivos.map((o) => `${proveedor(o.proveedor_id)}: ${o.tipo === "ip" ? "IP" : "dominio"} ${o.objetivo}`).join("  |  "));
    for (const k of e.capturas) fila(`Captura ${k.deteccion_id}, minuto ${Math.floor(k.capturada_min)}`, k.sha256, "hash");
    if (e.promocion && e.promocion.length) {
      fila("Dónde se promocionó", e.promocion.map((x) => `${x.red}: ${x.url}`).join("  |  "));
    }
    fila("Huella del expediente (SHA-256)", e.hash, "hash");
    cuerpo.dataset.cargado = "si";
  } catch (err) {
    cuerpo.dataset.cargado = "error";
    cuerpo.textContent = `No se pudo abrir el expediente: ${err.message}. `;
    const b = document.createElement("button");
    b.type = "button"; b.className = "boton boton--suave"; b.textContent = "Reintentar";
    b.addEventListener("click", () => cargarExpediente(p, cuerpo));
    cuerpo.append(b);
  }
}

function renderOrdenes(ordenes) {
  const cont = $("ordenes");
  $("vacio-ordenes").hidden = ordenes.length > 0;
  const ultimas = new Map();   // la orden más reciente por pedido y proveedor (los reintentos reemplazan)
  for (const o of ordenes) {
    const k = `${o.pedido_id}|${o.proveedor_id}`;
    const prev = ultimas.get(k);
    if (!prev || o.intentos >= prev.intentos) ultimas.set(k, o);
  }
  const porPedido = new Map();
  for (const o of ultimas.values()) {
    if (!porPedido.has(o.pedido_id)) porPedido.set(o.pedido_id, []);
    porPedido.get(o.pedido_id).push(o);
  }
  cont.replaceChildren();
  for (const [pid, os] of [...porPedido].reverse()) {
    const fila = document.createElement("div"); fila.className = "fila-orden";
    const t = document.createElement("p"); t.className = "fila-orden__titulo";
    const porNombre = os.find((o) => o.tipo === "dominio"), porIp = os.find((o) => o.tipo === "ip");
    t.textContent = `${(porNombre || porIp).objetivo} `;
    const s = document.createElement("small");
    s.textContent = `${porIp ? `IP ${porIp.objetivo}, ` : "solo por nombre, "}firmó ${nombreJuez(os[0].juez_id)}`;
    t.append(s);
    const casillas = document.createElement("div"); casillas.className = "casillas";
    for (const o of os) {
      const c = document.createElement("div"); c.className = `casilla casilla--${o.estado}`;
      const b = document.createElement("b"); b.textContent = proveedor(o.proveedor_id); c.append(b);
      let txt = ESTADOS_ORDEN[o.estado] || o.estado;
      if (o.estado === "aplicada") txt += ` desde ${min(o.aplicada_min)}`;
      if (o.intentos > 1) txt += ` (intento ${o.intentos})`;
      c.append(txt);
      casillas.append(c);
    }
    fila.append(t, casillas);
    cont.append(fila);
  }
}

// ---------------------------------------------------------------------- acciones

function resultado(hechos, errores, verbo) {
  if (hechos.length) {
    aviso(hechos.length === 1 ? `Firmaste ${verbo} 1 pedido.` : `Firmaste ${verbo} ${hechos.length} pedidos.`, "ok",
      { duracion: 4000, titulo: verbo === "la aprobación de" ? "Órdenes en camino a los proveedores" : null });
  }
  for (const e of errores) aviso(`${e.pedido_id}: ${e.error}`, "error", { duracion: 8000, titulo: "No se pudo firmar" });
}

async function firmar(ids) {
  if (!estado.juez || !ids.length) return;
  const boton = $("firmar-todos"); boton.disabled = true;
  try {
    const r = await api("/api/pedidos/aprobar", { pedido_ids: ids, juez_id: estado.juez });
    resultado(r.aprobados, r.errores, "la aprobación de");
  } catch (err) { if (err.message !== "401") aviso(err.message, "error", { duracion: 8000, titulo: "No se pudo firmar" }); }
  await refrescar();
}

async function rechazar(ids, motivo) {
  try {
    const r = await api("/api/pedidos/rechazar", { pedido_ids: ids, juez_id: estado.juez, motivo });
    resultado(r.rechazados, r.errores, "el rechazo de");
  } catch (err) { if (err.message !== "401") aviso(err.message, "error", { duracion: 8000, titulo: "No se pudo rechazar" }); }
  await refrescar();
}

async function asumirTurno() {
  try {
    const r = await api("/api/turno/asumir", { juez_id: estado.juez });
    if (r.pendiente) {
      aviso("El motor todavía no confirmó el traspaso. Se actualiza solo.", "info", { duracion: 6000, titulo: "Turno en trámite" });
    } else {
      quitarAviso("traspaso");
      aviso(`Ratificaste ${(r.ratificadas || []).length} órdenes vigentes. Desde ahora los reintentos salen con tu firma.`, "ok",
        { duracion: 5000, titulo: `Turno asumido por ${nombreJuez(r.juez_id)}` });
    }
  } catch (err) { if (err.message !== "401") aviso(err.message, "error", { duracion: 8000, titulo: "No se pudo asumir el turno" }); }
  await refrescar();
}

// ---------------------------------------------------------------------- reclamos

const ESTADOS_RECLAMO = { pendiente: "Espera tu decisión", levantado: "Levantado", descartado: "Descartado" };

function renderReclamos(reclamos) {
  const lista = $("reclamos");
  lista.replaceChildren();
  $("vacio-reclamos").hidden = reclamos.length > 0;
  for (const r of reclamos.sort((a, b) => b.minuto - a.minuto)) {
    const li = document.createElement("li");
    li.className = `reclamo reclamo--${r.estado}`;
    const titulo = document.createElement("p");
    titulo.className = "reclamo__titulo";
    titulo.textContent = `${min(r.minuto)} · ${r.dominio} · vía ${proveedor(r.proveedor_id)} · ${ESTADOS_RECLAMO[r.estado] || r.estado}`;
    const msg = document.createElement("p");
    msg.textContent = r.mensaje;
    const ver = document.createElement("p");
    ver.className = "reclamo__verificacion";
    ver.textContent = r.verificacion;
    li.append(titulo, msg, ver);
    if (r.estado === "pendiente" && r.orden_ids && r.orden_ids.length) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "boton boton--firmar";
      b.textContent = "Levantar el bloqueo y bloquear solo el dominio pirata";
      b.addEventListener("click", () => levantarReclamo(r.reclamo_id, b));
      li.append(b);
    }
    lista.append(li);
  }
}

async function levantarReclamo(reclamoId, boton) {
  boton.disabled = true;
  try {
    const r = await api("/api/reclamos/levantar",
      { reclamo_id: reclamoId, juez_id: estado.juez, motivo: "Reclamo legítimo verificado", reemplazar: true });
    if (r.pendiente) aviso("Los proveedores todavía no confirmaron el levantamiento. Se actualiza solo.", "info",
      { duracion: 6000, titulo: "Levantamiento en curso" });
    else aviso(`Se levantaron ${r.ordenes_levantadas.length} órdenes.`, "ok", { duracion: 5000, titulo: "Reclamo resuelto" });
  } catch (err) {
    boton.disabled = false;
    if (err.message !== "401") aviso(err.message, "error", { duracion: 8000, titulo: "No se pudo levantar" });
  }
  await refrescar();
}

// ---------------------------------------------------------------------- ciclo

let refrescando = false;
async function refrescar() {
  if (refrescando || !estado.pin) return;
  refrescando = true;
  try {
    const [e, p, o, rc] = await Promise.all([api("/api/estado"), api("/api/pedidos?estado=pendiente"), api("/api/ordenes"),
      api("/api/reclamos")]);
    quitarAviso("sin-red");
    renderEstado(e);
    renderPedidos(p.pedidos.sort((a, b) => a.creado_min - b.creado_min));
    renderOrdenes(o.ordenes);
    renderReclamos(rc.reclamos);
  } catch (err) {
    if (err.message !== "401") {
      aviso("Sin conexión con la plataforma. Se reintenta solo cada 2 segundos.", "error", { id: "sin-red", titulo: "Sin conexión" });
    }
  } finally { refrescando = false; }
}

function pedirPin(error = "") {
  estado.pin = null; guardarPin(null);
  $("tablero").hidden = true; $("accion").hidden = true; $("ingreso").hidden = false;
  $("pin-error").textContent = error;
  $("pin").focus();
}

function entrar() {
  $("ingreso").hidden = true; $("tablero").hidden = false; $("accion").hidden = false;
  refrescar();
}

$("form-pin").addEventListener("submit", (ev) => {
  ev.preventDefault();
  estado.pin = $("pin").value.trim();
  guardarPin(estado.pin);
  prepararAvisos();
  entrar();
});
$("firmar-todos").addEventListener("click", () => firmar(estado.pendientes.map((p) => p.pedido_id)));
document.addEventListener("click", prepararAvisos, { once: true });

if (estado.pin) entrar(); else pedirPin();
setInterval(refrescar, REFRESCO_MS);
