/* Tablero de monitoreo: solo lectura sobre /api/estado, /api/pedidos, /api/ordenes, /api/auditoria y /api/reclamos. */
"use strict";
const $ = (id) => document.getElementById(id);

const ESTADO_RECLAMO = {
  pendiente: ["Pendiente", "ambar"],
  levantado: ["Levantado", "verde"],
  resuelto: ["Resuelto", "verde"],
  descartado: ["Descartado", ""],
  rechazado: ["Rechazado", ""],
};

const CLASIFICACION = {
  licenciatario_legal: "Licenciatario autorizado en su propio dominio",
  otra_senal: "Es otra señal, no la de este partido",
  sin_marca: "Sin marca de agua verificable",
};

function textoEvento(ev, est) {
  const d = ev.datos || {};
  const juez = (id) => nombreJuez(est, id);
  switch (ev.accion) {
    case "motor_iniciado": return [["Plataforma conectada al partido"], "", ""];
    case "caso_creado": return [["Stream pirata detectado: ", h("b", {}, d.host)], d.ip, "rojo"];
    case "caso_descartado": return [["Descartado: ", h("b", {}, d.host)], d.motivo, ""];
    case "expediente_creado": return [["Expediente ", h("b", {}, d.expediente_id), " armado"], "con hash verificable", ""];
    case "pedido_creado": return [["Pedido ", h("b", {}, d.pedido_id), " enviado al juez"], "", "ambar"];
    case "pedido_aprobado": return [[h("b", {}, juez(ev.actor.replace("juez:", ""))), " firmó ", d.pedido_id], "", "verde"];
    case "pedido_rechazado": return [[h("b", {}, juez(ev.actor.replace("juez:", ""))), " rechazó ", d.pedido_id], d.motivo, "rojo"];
    case "orden_enviada": return [["Orden a ", h("b", {}, proveedor(d.proveedor_id)), `: ${d.tipo} ${d.objetivo}`], "", ""];
    case "orden_reenviada": return [["Reintento a ", h("b", {}, proveedor(d.proveedor_id)), `: ${d.objetivo}`], "con orden nueva", "ambar"];
    case "orden_aplicada": return [[h("b", {}, proveedor(ev.actor.replace("proveedor:", ""))), ` aplicó el bloqueo de ${d.objetivo}`], "", "verde"];
    case "orden_fallida": return [[h("b", {}, proveedor(ev.actor.replace("proveedor:", ""))), ` falló con ${d.objetivo}`], d.motivo, "rojo"];
    case "orden_vencida": return [[`Venció el bloqueo de ${d.objetivo} en `, h("b", {}, proveedor(ev.actor.replace("proveedor:", "")))], "", ""];
    case "orden_levantada": return [[`Se levantó ${d.objetivo} en `, h("b", {}, proveedor(ev.actor.replace("proveedor:", "")))], d.motivo, "azul"];
    case "cambio_de_turno": return [["Cambio de turno: entra ", h("b", {}, (d.entrantes || []).map(juez).join(", "))], d.nota, "ambar"];
    case "turno_asumido": return [[h("b", {}, juez(d.juez_id)), " asumió el turno"], `ratificó ${(d.ratificadas || []).length} órdenes`, "verde"];
    case "reclamo_recibido": return [["Reclamo de ", h("b", {}, d.dominio)], "", "ambar"];
    case "partido_finalizado": return [["Partido finalizado"], `${d.ordenes} órdenes, ${d.pedidos} pedidos, ${d.reclamos} reclamos`, ""];
    default: return [[ev.accion.replaceAll("_", " ")], "", ""];
  }
}

function ultimasPorProveedor(ordenes) {
  const ultimas = {};
  for (const o of ordenes) {
    const actual = ultimas[o.proveedor_id];
    if (!actual || o.intentos > actual.intentos) ultimas[o.proveedor_id] = o;
  }
  return Object.values(ultimas).sort((a, b) => a.proveedor_id.localeCompare(b.proveedor_id));
}

function pintarCabecera(est) {
  const [texto, color] = estadoPartido(est);
  const fin = est.fin_min || 105;
  const sinPartido = est.minuto_actual === null || est.minuto_actual === undefined;
  $("minuto").textContent = sinPartido ? "VS" : minuto(Math.min(est.minuto_actual, fin));
  $("partido").textContent = sinPartido ? "Esperando partido" : `Partido ${est.partido_id}`;
  const deTurno = (est.jueces_de_turno || []).map((id) => nombreJuez(est, id)).join(", ") || "—";
  $("sub").textContent = `Juez de turno: ${deTurno}` +
    (est.proximo_cambio_turno_min ? ` · cambia en el ${minuto(est.proximo_cambio_turno_min)}` : "");
  $("avance").style.width = sinPartido ? "0" : `${Math.min(100, (est.minuto_actual / fin) * 100)}%`;
  $("leyenda-fin").textContent = minuto(fin);

  const cambio = (est.juzgados?.turnos || []).map((t) => t.desde_min).find((m) => m > 0 && m < fin);
  $("marca-turno").hidden = !cambio;
  if (cambio) $("marca-turno").style.left = `${(cambio / fin) * 100}%`;
  $("leyenda-turno").textContent = cambio ? `turno ${minuto(cambio)}` : "";

  reemplazar($("chips"),
    chip(texto, texto === "En vivo" ? "" : color, texto === "En vivo" ? "chip--vivo" : ""),
    sinPartido ? null : (est.turno_ratificado ? chip("Turno ratificado", "verde") : chip("Turno sin ratificar", "ambar")));
}

function pintarKpis(est, pedidos, ordenes, reclamos) {
  const c = est.contadores || {};
  $("k-piratas").textContent = c.casos_piratas ?? 0;
  $("k-descartados").textContent = `Streams piratas · ${c.casos_descartados ?? 0} descartados`;
  $("k-pendientes").textContent = c.pedidos_pendientes ?? 0;
  $("k-firmados").textContent = `Esperan firma · ${c.pedidos_aprobados ?? 0} firmados`;
  $("k-activas").textContent = ordenes.filter((o) => o.estado === "aplicada").length;
  $("k-ordenes").textContent = `Aplicadas ahora · ${ordenes.length} en total`;
  const tiempos = pedidos.map(tiempoPrimerBloqueo).filter((t) => t !== null);
  $("k-tiempo").textContent = tiempos.length ? numero(tiempos.reduce((a, b) => a + b, 0) / tiempos.length, 2) : "—";
  $("k-reintentos").textContent = ordenes.filter((o) => o.reemplaza_a).length;
  const fallidas = ordenes.filter((o) => o.estado === "fallida").length;
  $("k-fallidas").textContent = fallidas ? `Reintentos solos · ${fallidas} fallas` : "Reintentos · sin fallas";
  const pendientes = reclamos.filter((r) => r.estado === "pendiente").length;
  $("k-reclamos").textContent = reclamos.length;
  $("k-reclamos-nota").textContent = `Reclamos · ${pendientes} pendientes`;
  const bloqueados = pedidos.filter((p) => (ordenesPorPedido[p.pedido_id] || []).some((o) => o.aplicada_min != null)).length;
  $("m-bloqueados").textContent = bloqueados;
  $("m-sueltos").textContent = Math.max(0, (c.casos_piratas ?? 0) - bloqueados);
}

let ordenesPorPedido = {};
function tiempoPrimerBloqueo(p) {
  const aplicadas = (ordenesPorPedido[p.pedido_id] || []).map((o) => o.aplicada_min).filter((m) => m !== null && m !== undefined);
  const desde = p.resumen?.primer_minuto ?? p.creado_min;
  return aplicadas.length && desde !== undefined ? Math.max(0, Math.min(...aplicadas) - desde) : null;
}

function pintarStreams(est, pedidos) {
  const orden = pedidos.slice().sort((a, b) => (a.creado_min || 0) - (b.creado_min || 0));
  const filas = orden.map((p, i) => {
    const r = p.resumen || {};
    const tipos = [...new Set((p.objetivos || []).map((o) => o.tipo))];
    const medalla = tipos.includes("ip")
      ? h("span", { class: "medalla medalla--lima", title: "Bloqueo por IP de un solo titular" }, "IP")
      : h("span", { class: "medalla medalla--cian", title: "IP compartida o dudosa: solo el nombre" }, "Nombre");
    const t = tiempoPrimerBloqueo(p);
    const ultimas = ultimasPorProveedor(ordenesPorPedido[p.pedido_id] || []);
    return h("article", { class: "stream" },
      h("span", { class: "stream__num" }, i + 1),
      h("div", {},
        h("p", { class: "stream__host" }, r.host || p.pedido_id, medalla, chipDe(ESTADO_PEDIDO, p.estado)),
        h("p", { class: "stream__sub" }, `${minuto(r.primer_minuto ?? p.creado_min, 1)} · ${r.ip || ""} · ${r.organizacion || ""}` +
          (p.juez_id ? ` · firmó ${nombreJuez(est, p.juez_id)}` : ""))),
      h("div", { class: "stream__tiempo" }, h("b", {}, t === null ? "—" : `${numero(t, 2)}'`), h("small", {}, "al 1.er bloqueo")),
      h("div", { class: "proveedores" }, ultimas.length
        ? ultimas.map((o) => {
            const [txt, color] = ESTADO_ORDEN[o.estado] || [o.estado, ""];
            return h("span", { class: `chip${color ? " chip--" + color : ""}`, title: `${o.tipo} ${o.objetivo} · intento ${o.intentos}` },
              `${proveedor(o.proveedor_id)} · ${txt}`);
          })
        : h("span", { class: "tenue" }, p.estado === "pendiente" ? "Esperando la firma del juez" : "—")));
  });
  reemplazar($("streams"), filas.reverse());
  $("vacio-streams").hidden = filas.length > 0;
}

function pintarDescartados(eventos) {
  const filas = eventos.filter((e) => e.accion === "caso_descartado").map((e) => h("div", { class: "descartado" },
    h("div", { class: "descartado__cabeza" }, h("span", { class: "fuerte mono" }, e.datos.host), h("span", { class: "tenue" }, minuto(e.min, 1))),
    h("p", {}, CLASIFICACION[e.datos.clasificacion] || e.datos.clasificacion),
    h("p", { class: "tenue" }, e.datos.motivo)));
  reemplazar($("descartados"), filas);
  $("vacio-descartados").hidden = filas.length > 0;
}

function pintarActividad(est, eventos) {
  const items = eventos.filter((e) => e.accion !== "deteccion_repetida").slice(-40).reverse().map((e) => {
    const [texto, nota, color] = textoEvento(e, est);
    return h("li", { class: `evento${color ? " evento--" + color : ""}` },
      h("span", { class: "evento__min" }, minuto(e.min, 1)),
      h("div", {}, h("div", { class: "evento__texto" }, texto), nota ? h("div", { class: "evento__actor" }, nota) : null));
  });
  reemplazar($("actividad"), items);
  $("vacio-actividad").hidden = items.length > 0;
}

function pintarReclamos(reclamos) {
  const items = reclamos.map((r) => h("div", { class: "reclamo" },
    h("div", { class: "reclamo__cabeza" }, h("span", { class: "fuerte mono" }, r.dominio), chipDe(ESTADO_RECLAMO, r.estado)),
    h("p", { class: "tenue" }, `${minuto(r.minuto, 1)} · vía ${proveedor(r.proveedor_id)}`),
    h("p", {}, r.mensaje),
    r.verificacion ? h("p", { class: "tenue", style: "margin-top:4px" }, r.verificacion) : null));
  reemplazar($("reclamos"), items);
  $("vacio-reclamos").hidden = items.length > 0;
}

function pintarIntegridad(integ) {
  const ok = integ.integra;
  reemplazar($("integridad"),
    h("div", { class: `integridad__sello integridad__sello--${ok ? "ok" : "mal"}`, "aria-hidden": "true" }, ok ? "✓" : "!"),
    h("div", {},
      h("p", { class: "fuerte" }, ok ? `Cadena íntegra · ${integ.eventos} eventos` : `Cadena alterada en el evento ${integ.falla_en_seq}`),
      h("p", { class: "tenue mono", style: "word-break:break-all" }, ok ? `último hash ${integ.ultimo_hash.slice(0, 24)}…` :
        "un evento no coincide con su hash: la auditoría fue modificada")));
}

cadaTanto(async () => {
  const [est, ped, ord, aud, rec, integ] = await Promise.all([
    api("/api/estado"), api("/api/pedidos"), api("/api/ordenes"), api("/api/auditoria"), api("/api/reclamos"),
    api("/api/auditoria/integridad"),
  ]);
  ordenesPorPedido = {};
  for (const o of ord.ordenes) (ordenesPorPedido[o.pedido_id] ||= []).push(o);
  pintarCabecera(est);
  pintarKpis(est, ped.pedidos, ord.ordenes, rec.reclamos);
  pintarStreams(est, ped.pedidos);
  pintarDescartados(aud.eventos);
  pintarActividad(est, aud.eventos);
  pintarReclamos(rec.reclamos);
  pintarIntegridad(integ);
}, 2000);
