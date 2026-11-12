/* Utilidades compartidas de portada, monitoreo y registro. Los datos se insertan siempre como texto. */
"use strict";

const PROVEEDORES = {
  aurora: "Aurora",
  andina: "Andina",
  valle: "FibraValle",
  cumbre: "Cumbre",
};

const ESTADO_ORDEN = {
  enviada: ["Enviada", "azul"],
  recibida: ["Recibida", "ambar"],
  aplicada: ["Aplicada", "verde"],
  vencida: ["Vencida", ""],
  levantada: ["Levantada", "azul"],
  fallida: ["Fallida", "rojo"],
  rechazada: ["Rechazada", "rojo"],
};

const ESTADO_PUBLICO = {
  vigente: ["Vigente", "verde"],
  en_curso: ["En curso", "ambar"],
  levantado: ["Levantado", "azul"],
  vencido: ["Vencido", ""],
};

const ESTADO_PEDIDO = {
  pendiente: ["Espera firma", "ambar"],
  aprobado: ["Firmado", "verde"],
  rechazado: ["Rechazado", "rojo"],
};

function h(tag, attrs, ...hijos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const hijo of hijos.flat()) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    el.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
  return el;
}

function chip(texto, color, extra) {
  return h("span", { class: `chip${color ? " chip--" + color : ""}${extra ? " " + extra : ""}` }, texto);
}

function chipDe(mapa, estado) {
  const [texto, color] = mapa[estado] || [estado || "—", ""];
  return chip(texto, color);
}

function proveedor(id) {
  return PROVEEDORES[id] || (id ? id[0].toUpperCase() + id.slice(1) : "—");
}

function minuto(m, decimales = 0) {
  if (m === null || m === undefined || Number.isNaN(Number(m))) return "—";
  return `${Math.max(0, Number(m)).toFixed(decimales).replace(".", ",")}'`;
}

function numero(n, decimales = 1) {
  return Number(n).toFixed(decimales).replace(".", ",");
}

async function api(ruta) {
  const r = await fetch(ruta, { headers: { Accept: "application/json" }, cache: "no-store" });
  if (!r.ok) throw new Error(`${ruta}: ${r.status}`);
  return r.json();
}

function nombreJuez(estado, juezId) {
  for (const jz of estado?.juzgados?.juzgados || []) {
    for (const j of jz.jueces || []) if (j.id === juezId) return j.nombre;
  }
  return juezId || "—";
}

function estadoPartido(est) {
  if (!est || est.minuto_actual === null || est.minuto_actual === undefined) return ["Sin partido", ""];
  if (est.finalizado) return ["Finalizado", ""];
  if (!est.simulador_ok) return ["Sin conexión con el motor", "rojo"];
  return ["En vivo", "rojo"];
}

/* Repite fn cada `ms`, sin solaparse, y pausa si la pestaña no está visible. */
function cadaTanto(fn, ms) {
  let timer = null;
  const tick = async () => {
    try { await fn(); } catch (e) { console.warn(e); }
    timer = setTimeout(tick, document.hidden ? ms * 4 : ms);
  };
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) { clearTimeout(timer); tick(); }
  });
  tick();
}

function reemplazar(contenedor, ...hijos) {
  contenedor.replaceChildren(...hijos.flat().filter(Boolean));
}
