/* Centro de partidos. Las selecciones, jugadores y horarios son de DEMOSTRACIÓN (nombres de jugadores inventados).
   Lo que sí es real es la protección: minuto, streams piratas, firmas y órdenes salen de la API del simulador. */
"use strict";

const BANDERAS = {
  ARG: '<rect width="30" height="20" fill="#74ACDF"/><rect y="6.67" width="30" height="6.67" fill="#fff"/><circle cx="15" cy="10" r="2.2" fill="#F6B40E"/>',
  BRA: '<rect width="30" height="20" fill="#009B3A"/><path d="M15 2.5 27 10 15 17.5 3 10Z" fill="#FEDF00"/><circle cx="15" cy="10" r="4" fill="#002776"/>',
  URU: '<rect width="30" height="20" fill="#fff"/><g fill="#0038A8"><rect y="2.22" width="30" height="2.22"/><rect y="6.67" width="30" height="2.22"/><rect y="11.1" width="30" height="2.22"/><rect y="15.6" width="30" height="2.22"/></g><rect width="11" height="11.1" fill="#fff"/><circle cx="5.5" cy="5.5" r="2.6" fill="#FCD116"/>',
  COL: '<rect width="30" height="20" fill="#CE1126"/><rect width="30" height="15" fill="#003893"/><rect width="30" height="10" fill="#FCD116"/>',
  MEX: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#006847"/><rect x="20" width="10" height="20" fill="#CE1126"/><circle cx="15" cy="10" r="2.4" fill="#8C5A2B"/>',
  CHI: '<rect width="30" height="20" fill="#D52B1E"/><rect width="30" height="10" fill="#fff"/><rect width="10" height="10" fill="#0039A6"/><path d="M5 2.4 5.9 5.2H8.8L6.4 6.9 7.3 9.7 5 8 2.7 9.7 3.6 6.9 1.2 5.2H4.1Z" fill="#fff"/>',
  ESP: '<rect width="30" height="20" fill="#AA151B"/><rect y="5" width="30" height="10" fill="#F1BF00"/>',
  FRA: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#002395"/><rect x="20" width="10" height="20" fill="#ED2939"/>',
  PER: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#D91023"/><rect x="20" width="10" height="20" fill="#D91023"/>',
  ECU: '<rect width="30" height="20" fill="#ED1C24"/><rect width="30" height="15" fill="#034EA2"/><rect width="30" height="10" fill="#FFDD00"/><circle cx="15" cy="10" r="2.4" fill="#8C5A2B"/>',
};

function bandera(codigo, clase = "bandera") {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 30 20");
  svg.setAttribute("class", clase);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `Bandera ${codigo}`);
  svg.innerHTML = BANDERAS[codigo] || '<rect width="30" height="20" fill="#555"/>';   // constantes propias, no datos externos
  return svg;
}

const EQUIPOS = {
  ARG: { nombre: "Argentina", corto: "ARG", once: [
    [1, "ARQ", "T. Ferreyra"], [4, "DEF", "L. Arce"], [2, "DEF", "M. Quiroga"], [6, "DEF", "B. Sosa"], [3, "DEF", "N. Ledesma"],
    [5, "MED", "F. Cabral"], [8, "MED", "J. Benítez"], [10, "MED", "S. Ojeda"], [7, "DEL", "R. Funes"], [9, "DEL", "A. Medina"], [11, "DEL", "G. Paz"]] },
  BRA: { nombre: "Brasil", corto: "BRA", once: [
    [1, "ARQ", "R. Moura"], [2, "DEF", "D. Lacerda"], [3, "DEF", "C. Prado"], [4, "DEF", "W. Teles"], [6, "DEF", "I. Rocha"],
    [5, "MED", "V. Queiroz"], [8, "MED", "E. Barreto"], [10, "MED", "Thi. Lins"], [7, "DEL", "Kauã Melo"], [9, "DEL", "P. Dantas"], [11, "DEL", "L. Faria"]] },
  URU: { nombre: "Uruguay", corto: "URU" }, COL: { nombre: "Colombia", corto: "COL" },
  MEX: { nombre: "México", corto: "MEX" }, CHI: { nombre: "Chile", corto: "CHI" },
  ESP: { nombre: "España", corto: "ESP" }, FRA: { nombre: "Francia", corto: "FRA" },
  PER: { nombre: "Perú", corto: "PER" }, ECU: { nombre: "Ecuador", corto: "ECU" },
};

/* El partido "en vivo" muestra los datos reales del simulador con estas selecciones de demostración. */
const PARTIDO_EN_VIVO = { local: "ARG", visitante: "BRA", torneo: "Copa Ficticia 2026 · Fecha 3", sede: "Estadio Ficticio del Norte" };
const PROXIMOS = [
  { local: "URU", visitante: "COL", torneo: "Copa Ficticia 2026 · Fecha 3", hora: "Hoy 21:00" },
  { local: "MEX", visitante: "CHI", torneo: "Copa Ficticia 2026 · Fecha 3", hora: "Hoy 23:30" },
  { local: "ESP", visitante: "FRA", torneo: "Amistoso ficticio", hora: "Mañana 16:00" },
  { local: "PER", visitante: "ECU", torneo: "Copa Ficticia 2026 · Fecha 4", hora: "Sáb 18:00" },
];

/* Resumen de protección del partido en vivo a partir de la API real. */
async function proteccionEnVivo() {
  const [est, ped, ord] = await Promise.all([api("/api/estado"), api("/api/pedidos"), api("/api/ordenes")]);
  const aplicadas = new Set(ord.ordenes.filter((o) => o.aplicada_min != null).map((o) => o.pedido_id));
  return {
    est, pedidos: ped.pedidos, ordenes: ord.ordenes,
    piratas: est.contadores?.casos_piratas ?? 0,
    expulsados: ped.pedidos.filter((p) => aplicadas.has(p.pedido_id)).length,
    activas: ord.ordenes.filter((o) => o.estado === "aplicada").length,
  };
}

function equipoNombre(cod) { return EQUIPOS[cod]?.nombre || cod; }

function equipos(local, visitante, centro) {
  return h("div", { class: "encuentro__equipos" },
    h("div", { class: "encuentro__equipo" }, bandera(local), equipoNombre(local)),
    h("div", { class: "encuentro__centro" }, centro),
    h("div", { class: "encuentro__equipo encuentro__equipo--der" }, equipoNombre(visitante), bandera(visitante)));
}

function tarjetaVivo(d) {
  const est = d.est;
  const sinPartido = est.minuto_actual == null;
  const [texto] = estadoPartido(est);
  const rojas = Array.from({ length: Math.min(d.expulsados, 12) }, () => h("span", { class: "roja" }));
  return h("a", { class: "encuentro encuentro--vivo", href: "/partido", "data-tipo": "vivo" },
    h("div", { class: "encuentro__cabeza" },
      h("span", { class: "encuentro__torneo" }, `${PARTIDO_EN_VIVO.torneo} · ${PARTIDO_EN_VIVO.sede}`),
      texto === "En vivo" ? chip("En vivo", "", "chip--vivo") : chip(sinPartido ? "Esperando" : texto, "")),
    equipos(PARTIDO_EN_VIVO.local, PARTIDO_EN_VIVO.visitante,
      h("span", { class: "caja caja--lima" }, sinPartido ? "VS" : minuto(Math.min(est.minuto_actual, est.fin_min || 105)))),
    h("div", { class: "encuentro__pie" },
      h("span", { class: "expulsados" }, ...rojas, `${d.expulsados} piratas expulsados`,
        h("span", { class: "tenue", style: "font-style:normal" }, ` · ${d.piratas} detectados · ${d.activas} órdenes activas`)),
      h("span", { class: "boton boton--primario boton--chico" }, "Ver partido")));
}

function tarjetaProximo(p) {
  return h("article", { class: "encuentro", "data-tipo": "proximo" },
    h("div", { class: "encuentro__cabeza" }, h("span", { class: "encuentro__torneo" }, p.torneo), chip(p.hora, "azul")),
    equipos(p.local, p.visitante, "VS"),
    h("div", { class: "encuentro__pie" },
      h("span", { class: "expulsados tenue" }, h("i", { class: "galon" }), "Protección programada"),
      h("span", { class: "tenue", style: "font-size:12px" }, "Se activa con el pitazo inicial")));
}
