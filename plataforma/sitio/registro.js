/* Registro público legible sobre /api/publico. */
"use strict";
const $ = (id) => document.getElementById(id);
const filtro = { texto: "", estado: "", tipo: "" };
let entradas = [];
let partido = null;

function coincide(e) {
  if (filtro.estado === "fin" ? !["vencido", "levantado"].includes(e.estado) : filtro.estado && e.estado !== filtro.estado) return false;
  if (filtro.tipo && e.tipo !== filtro.tipo) return false;
  if (!filtro.texto) return true;
  const t = filtro.texto.toLowerCase();
  return [e.objetivo, e.juez_nombre, e.juzgado_nombre, e.expediente_id, e.motivo].some((v) => (v || "").toLowerCase().includes(t));
}

function tarjeta(e) {
  const fin = e.estado === "vencido" || e.estado === "levantado"
    ? `finalizó ${minuto(e.finalizado_min, 1)} · ${e.motivo_fin || ""}` : `vence ${minuto(e.vence_min)} (fin del partido)`;
  return h("article", { class: "panel entrada" },
    h("div", {},
      h("p", { class: "entrada__objetivo" }, e.objetivo),
      h("p", { class: "tenue", style: "font-size:13px;margin-top:2px" }, e.tipo === "ip" ? "Bloqueo por dirección IP" : "Bloqueo por nombre de dominio")),
    h("div", {}, chipDe(ESTADO_PUBLICO, e.estado)),
    h("p", { class: "entrada__motivo" }, e.motivo),
    h("div", { class: "entrada__datos" },
      h("span", {}, "Ordenó ", h("b", {}, e.juez_nombre || e.juez_id)),
      h("span", {}, h("b", {}, e.juzgado_nombre || e.juzgado_id)),
      h("span", {}, "Firmado ", h("b", {}, minuto(e.ordenado_min, 1))),
      h("span", {}, fin),
      h("span", {}, "Expediente ", h("b", { class: "mono" }, e.expediente_id))),
    h("div", { class: "entrada__proveedores proveedores" }, (e.proveedores || []).map((p) => {
      const [txt, color] = ESTADO_ORDEN[p.estado] || [p.estado, ""];
      const cuando = p.aplicada_min !== null && p.aplicada_min !== undefined ? ` desde ${minuto(p.aplicada_min, 1)}` : "";
      return chip(`${proveedor(p.proveedor_id)}: ${txt}${cuando}`, color);
    })));
}

function pintar() {
  const visibles = entradas.filter(coincide);
  reemplazar($("entradas"), visibles.map(tarjeta));
  $("vacio").hidden = visibles.length > 0;
  $("vacio").textContent = entradas.length ? "Ningún bloqueo coincide con la búsqueda." : "Todavía no hay bloqueos registrados.";
  $("resumen").textContent = entradas.length ? `Mostrando ${visibles.length} de ${entradas.length} bloqueos` : "";
}

function pintarResumen() {
  $("r-total").textContent = entradas.length;
  $("r-partido").textContent = partido ? `partido ${partido}` : "—";
  $("r-vigentes").textContent = entradas.filter((e) => e.estado === "vigente").length;
  $("r-finalizados").textContent = entradas.filter((e) => ["vencido", "levantado"].includes(e.estado)).length;
  $("r-levantados").textContent = `${entradas.filter((e) => e.estado === "levantado").length} levantados por reclamo`;
  $("r-juzgados").textContent = new Set(entradas.map((e) => e.juzgado_id)).size;
}

for (const [grupo, clave] of [["f-estado", "estado"], ["f-tipo", "tipo"]]) {
  $(grupo).addEventListener("click", (ev) => {
    const b = ev.target.closest("button");
    if (!b) return;
    for (const otro of $(grupo).querySelectorAll("button")) otro.setAttribute("aria-pressed", String(otro === b));
    filtro[clave] = b.dataset.v;
    pintar();
  });
}
$("buscar").addEventListener("input", (ev) => { filtro.texto = ev.target.value.trim(); pintar(); });

cadaTanto(async () => {
  const datos = await api("/api/publico");
  entradas = (datos.entradas || []).slice().sort((a, b) => (b.ordenado_min || 0) - (a.ordenado_min || 0));
  partido = entradas[0]?.partido_id || null;
  pintarResumen();
  pintar();
}, 5000);
