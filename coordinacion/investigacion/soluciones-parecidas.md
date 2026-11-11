# Rápido y con juez: lo que nadie combinó

**En corto:** no hay en el mundo un sistema que haga nuestro circuito completo. Hay sistemas que van rápido porque sacaron al juez: Italia (AGCOM, 30 minutos, cargan los propios titulares), Brasil (ANCINE/Anatel, órdenes nuevas cada 30 minutos) y Francia, que en julio de 2026 aprobó un bloqueo automatizado sin revisión humana previa. Hay otros que tienen juez pero le dejaron la lista al titular, como España y el Reino Unido. España es el caso testigo de daño colateral: unas 3.000 IP bloqueadas por fin de semana con una sentencia que nombra unas 120. Argentina ya tiene las piezas legales: una orden judicial dinámica, ENACOM notificando a los ISP y LaLiga autorizada desde septiembre de 2026 a bloquear IP en tiempo real. Le falta todo lo demás: una API, un acuse por ISP, el vencimiento verificable, un registro público y un canal de reclamos. Los vendors comerciales (Friend MTS, NAGRA, Viaccess-Orca, Sportian) venden detección y watermarking por contrato privado. Ninguno ofrece la firma judicial ni un canal universal a los ISP, así que ese hueco del medio está libre. En costos, lo caro nunca fue la plataforma central. En Italia esa plataforma cuesta entre decenas de miles y unos 2 millones de euros por año según la fuente, mientras los ISP reclaman unos €10M por año. Nuestro stack cuesta aproximadamente US$ 20–60 por mes **[estimación propia]**. El pitch tiene que apoyarse en esto: **"Europa tuvo que elegir entre rápido o con garantías. Nosotros no"**, demostrado en vivo y con un cronómetro en pantalla.

> Convenciones: **[ESTIMACIÓN]** = cálculo nuestro. **[PROPUESTA]** = diseño del equipo, no algo existente. **⚠️** = dato contradictorio o sin verificar: no decirlo en el escenario sin la aclaración indicada.

---

## Catorce sistemas, y ninguno junta juez, minutos y registro público

| Sistema | Quién decide | Velocidad | Alcance ISP | Costo y quién paga | Empaquetado | Transparencia / reclamos | Fallas conocidas |
|---|---|---|---|---|---|---|---|
| **Italia** (Piracy Shield, AGCOM) | Regulador administrativo, sin juez previo. Los "segnalatori" acreditados (p. ej., para DAZN) cargan los objetivos directamente ([Punto Informatico](https://www.punto-informatico.it/blocco-google-drive-diffida-agcom-dazn/)) | El ISP debe bloquear en **30 min** ([RIPE Labs](https://labs.ripe.net/author/antonio-prado/live-event-blocking-at-scale-effectiveness-vs-collateral-damage-in-italys-piracy-shield/)) | Todos los ISP. Presión sobre DNS públicos y VPN: multa de €14,2M a Cloudflare, apelada ([TorrentFreak](https://torrentfreak.com/italy-fines-cloudflare-e14-million-for-refusing-to-filter-pirate-sites-on-public-1-1-1-1-dns/)) | Plataforma: ⚠️ cifras contradictorias (€25k a €2M/año). La paga el Estado. Los ISP reclaman **~€10M/año** sin compensación ([ZeusNews](https://www.zeusnews.it/n.php?c=31580)) | Plataforma **donada por la Lega Serie A**, hecha por SP Tech, vinculada a los abogados de la Lega ([QuiFinanza](https://quifinanza.it/sport-economy/pezzotto-piracy-shield-blocco-vpn/910712/)) | No hay lista completa descargable, solo consultas una por una ([PPC Land](https://ppc.land/cloudflare-faces-eu14-2-million-fine-from-italian-regulator-over-piracy-enforcement/)). El canal de incidentes recibe críticas | Google Drive bloqueado durante horas (oct-2024). IP de Cloudflare. Miles de sitios legítimos con una exposición mediana de **meses**. IPv6 sin filtrar ([RIPE Labs](https://labs.ripe.net/author/antonio-prado/live-event-blocking-at-scale-effectiveness-vs-collateral-damage-in-italys-piracy-shield/)) |
| **Francia** (ARCOM, L.333-10) | Juez (Tribunal de París) + ARCOM extiende a espejos. Ley de jul-2026: sistema automatizado, auditoría **posterior** ([Reclaim The Net](https://reclaimthenet.org/france-just-deleted-the-human-review-step-from-stream-blocking)) | Bajó de semanas a **~45 min**, que la propia ARCOM considera insuficiente ([Siècle Digital](https://siecledigital.fr/2026/03/24/le-streaming-illegal-recule-en-france/)). Ley nueva: "sin demora", todavía sin implementar | Grandes ISP + DNS alternativos + VPN ([CMS](https://cms.law/en/fra/legal-updates/lutte-contre-le-piratage-sportif-renforcement-du-dispositif-d-injonctions-dynamiques)) | Sin cifra publicada. Fondos públicos de ARCOM. Los ISP cargan con su parte | Regulador público + órdenes judiciales por temporada | Apelación ante el presidente de ARCOM **durante el partido** (ley nueva) | Escaló de 772 dominios (2022) a ~6.500 (2025) ([Next](https://next.ink/230400/piratage-larcom-revendique-le-blocage-de-plus-de-15-000-noms-de-domaine-depuis-2022/)). ARCOM misma advertía que sobrebloquear podía ser inconstitucional |
| **España** (LaLiga) | Juzgado Mercantil nº 6 de Barcelona (dic-2024). Después **LaLiga actualiza la lista sin nueva resolución** ([Tech Times](https://www.techtimes.com/articles/316733/20260516/spains-parliament-votes-rein-laligas-mass-ip-blockades-test-case-eu-internet-governance.htm)) | Tiempo real | 4 ISP (Movistar, Vodafone, Orange, DIGI), todos licenciatarios. VPN desde feb-2026, sin oírlas | LaLiga paga su detección, los ISP ejecutan y **el daño colateral lo pagan terceros** | Privado: liga + ISP que venden el fútbol | Sin registro público, sin aviso a proveedores cloud. Sin apelación en la orden a VPN | ~3.000 IP por fin de semana contra ~120 en la sentencia ([Bandaancha](https://bandaancha.eu/articulos/esta-verdadera-dimension-bloqueos-futbol-11323)). Caen bancos, GitHub Pages, el Ayuntamiento de Madrid |
| **Reino Unido** (FAPL v BT) | High Court, una orden "live" por temporada desde 2017 ([Pinsent Masons](https://www.pinsentmasons.com/out-law/news/first-live-blocking-order-granted-in-the-uk-to-curb-unauthorised-streaming-of-football-matches)) | Bloquea servidores **solo mientras se juega** | Grandes ISP (⚠️ lista exacta sin verificar) | ⚠️ Sin verificar quién paga la implementación | Juez fija el criterio y el titular arma la lista técnica. Sky y BT no se oponen porque son licenciatarios | **Detalles secretos** ([TorrentFreak](https://torrentfreak.com/?p=193224)) | ⚠️ Datos de 2017–2021. Sin cifras recientes |
| **Grecia** (EDPPI) | Comité administrativo | Órdenes **preventivas** antes del evento. El FAQ oficial menciona un procedimiento de 15 días ([EDPPI](https://edppi.gr/information_en)) | ISP griegos | Sin datos | Comité estatal + multas de hasta €750 a usuarios de IPTV pirata | Procedimiento público | Volumen chico: 124 decisiones, 810 IP y 49 dominios en 2024 ([TorrentFreak](https://torrentfreak.com/greece-approves-framework-to-fine-pirate-iptv-users-ramps-up-blocking-250221/)) |
| **Portugal** (IGAC + MAPINET) | La IGAC valida las pruebas de MAPINET. Protocolo **voluntario**, sin juez | 48 h + 48 h (⚠️ dato viejo) ([TorrentFreak](https://torrentfreak.com/voluntary-live-sports-piracy-blocking-implemented-in-portugal/)) | Operadores de Apritel, por DNS | Sin datos | Autorregulación con sello estatal | Sin datos | Bloqueos sin fundamento reportados. Las telcos dicen que no funciona (2025) ([TorrentFreak](https://torrentfreak.com/piracy-blocks-dont-work-portuguese-telcos-now-call-for-sanctions-against-users-250430/)) |
| **Argentina hoy** | Juez de Garantías N°4 de San Isidro, a pedido de la UFEIC. ALIANZA y LaLiga aportan las listas. Desde sep-2026, el Juzgado Civil y Comercial Federal n.º 2 autoriza a LaLiga a bloquear IP en tiempo real ([RedesZone](https://www.redeszone.net/noticias/redes/laliga-bloquear-webs-tiempo-real-partidos-argentina/)) | No hay tiempos medidos públicos. En ago-2026 los bloqueos arrancaron 10 min después del inicio del partido ([ADSLZone](https://www.adslzone.net/noticias/descargas/bloqueo-300-webs-futbol-pirata-argentina/)) | "Todos los ISP", vía cámaras (2025) o ENACOM (2026). **Sin acuse por ISP** | ISP y cámaras absorben el costo. En 2025 la herramienta de rastreo la pagaron LaLiga y ALIANZA | Oficio judicial → ENACOM/cámaras → ISP | Las órdenes se conocen **por la prensa**. No hay registro ni apelación formal | ENACOM sin registro actualizado de ISP. Orden sin duración ni forma de reversión (2025) ([BAE Negocios](https://www.baenegocios.com/sociedad/Habra-un-inedito-bloqueo-al-futbol-libre-en-vivo-durante-el-fin-de-semana-20250530-0031.html)) |
| **Perú** (Indecopi) | Comisión de Derecho de Autor, administrativa | Bloqueo ejecutado el 10/06/2026 y **anunciado un mes después** ([El Peruano](https://elperuano.pe/noticia/300328-pirateria-en-el-mundial-2026-que-falta-tras-el-bloqueo-de-238-webs-ordenado-por-indecopi)) | Telefónica, América Móvil, Entel y otros | Sin datos | Regulador + operaciones regionales (Lumen: 317 sitios) | No hay apelación visible para terceros | Los sitios reaparecen con nuevas direcciones |
| **México** (IMPI) | Administrativo (art. 340 LFPPI) | "Tiempo real", según el IMPI | Coordinación con ISP no nombrados | Sin datos | Regulador + FIFA durante el Mundial | Cifras inconsistentes (57 / 140 / ~60 por día) ([Crónica](https://www.cronica.com.mx/nacional/2026/06/15/impi-bloquea-57-sitios-que-transmitian-el-mundial-ilegalmente-y-refuerza-vigilancia-contra-mercancia-pirata/)) | Constitucionalidad en revisión en la SCJN ([Xataka MX](https://www.xataka.com.mx/legislacion-y-derechos/pirateria-mexico-podria-enfrentarse-a-su-golpe-fuerte-scjn-analiza-legalizar-bloqueo-sitios)) |
| **Brasil** (ANCINE + Anatel) | ANCINE ordena y Anatel ejecuta. Administrativo (Lei 14.815/2024) | **Órdenes nuevas cada 30 min** los fines de semana con fútbol ([Teletime](https://teletime.com.br/12/08/2026/anatel-e-ancine-articulam-acoes-globais-de-combate-a-antipirataria/)) | **Más de 21.000 prestadoras** | Sin datos sobre quién paga a las prestadoras | Regulador + laboratorio de Anatel + Operação 404 (policial) | ANCINE informa 2 reclamos (<0,1%). Acepta denuncia ciudadana | Bloqueos de hasta 12 meses ([GEDAI](https://gedai.ufpr.br/iptv-ilegal/)). ⚠️ Cifras autodeclaradas y contradictorias |
| **Chile** (Subtel) | 19.º Juzgado Civil (causa de Warner) + Subtel, que instruye a los ISP | ISP con **hasta 5 días** de plazo ([CNN Chile](https://www.cnnchile.com/pais/golpe-a-la-tv-pirata-subtel-ordena-bloqueo-de-cerca-de-2-mil-sitios-y-advierte-riesgos-de-robo-de-datos-y-estafas/)) | ISP chilenos | Sin datos | Orden amplia + protocolo Subtel–Fiscalía–Warner–Alianza. Las listas las arma la Alianza | Se agregan sitios **"por interpretación"** de la orden ([TorrentFreak](https://torrentfreak.com/chile-blocks-1954-pirate-tv-urls-to-protect-citizens-privacy-and-personal-data/)) | 1.954 URL en 5 meses, pero siguen apareciendo clones |
| **Colombia** (DNDA + Fiscalía) | DNDA, medida cautelar administrativa desde 2025. Fiscalía en los operativos | Sin datos | ISP vía MinTIC | Sin datos | Regulador + operativos con LaLiga, Dimayor y ALIANZA (Tarjeta Roja: 1.140 dominios en Colombia) ([RCN](https://www.noticiasrcn.com/colombia/operacion-tarjeta-roja-1-140-dominios-bloqueados-1041683)) | Sin datos | Críticas por bloquear IP compartidas de Cloudflare ([El Espectador](https://www.elespectador.com/opinion/columnistas/carolina-botero-cabrera/neutralidad-de-la-red-en-riesgo-el-caso-dnda-mintic-y-la-pirateria-del-futbol/)). Proyecto de "bloqueo exprés" con reparos constitucionales |
| **Vendors comerciales** (Friend MTS, NAGRA, Irdeto, Viaccess-Orca, Sportian, Fastly) | No deciden: los contrata el titular | No publican tiempos de respuesta | **Sin canal universal a los ISP** | Contratos privados anuales, **sin precios públicos**. Paga el broadcaster o la liga | Servicio gestionado: monitoreo + watermarking + takedown. Hay conectores ISP de terceros (Aryel, ⚠️ €1.500/año sin verificar) | Producen evidencia para tribunales (VO con la LFP) pero no la publican ([TVBEurope](https://www.tvbeurope.com/media-delivery/viaccess-orca-french-football-league-block-football-piracy)) | No cubren la firma judicial ni la confirmación del ISP |
| **Nuestra propuesta** **[PROPUESTA]** | **Juez de turno firma cada orden** desde el celular, sobre un expediente con evidencia hasheada | Objetivo: minutos. **No medido todavía: medirlo en la demo** | Todos los ISP por API, **en el tipo de bloqueo que aceptan** (IP, DNS/RPZ, dominio), con acuse | Cloud ≈US$ 20–60/mes **[ESTIMACIÓN]**. Tasa por orden a cargo del solicitante. Gratis para ISP chicos | Infraestructura pública open source: ENACOM opera registro + API, el Poder Judicial firma | Registro público, log encadenado, reclamos abiertos a cualquiera | Sin probar en producción. Depende de que haya un juez de turno 24/7 (⚠️ no verificado). VPN, DNS públicos e IPv6 siguen siendo vías de escape |

**Cómo leer la tabla.** El espectro va de **administrativo-rápido** (Italia, Brasil, Perú, México y Francia desde 2026) a **judicial con lista privada** (España, Reino Unido, Chile), pasando por **voluntario** (Portugal) y **comité por evento** (Grecia). Los que logran velocidad lo hacen sacando al juez o entregándole la lista al titular, y es ahí donde aparece el sobrebloqueo. En Argentina, el art. 57 de la Ley 27.078 prohíbe a los prestadores bloquear contenidos "salvo orden judicial o expresa solicitud del usuario" ([Infoleg](https://servicios.infoleg.gob.ar/infolegInternet/anexos/235000-239999/239771/texact.htm)). Por eso el modelo administrativo de Perú o Brasil no se puede importar, y **el juez en el loop no es un lujo: es la ley**. Nuestro diseño convierte esa restricción en ventaja.

**Lo más parecido a nosotros:**
- **Francia** comparte la idea (orden judicial de base + extensión dinámica + apelación durante el partido), pero para ganar velocidad **quitó la verificación humana**.
- **Reino Unido** aportó la idea del bloqueo que solo rige durante el partido, antecedente directo de nuestro vencimiento automático.
- **Argentina 2025** ya aplicó IP temporal en la franja del partido + DNS permanente, con técnicos de guardia en los ISP ([BAE Negocios](https://www.baenegocios.com/sociedad/Habra-un-inedito-bloqueo-al-futbol-libre-en-vivo-durante-el-fin-de-semana-20250530-0031.html)). **No inventamos un circuito: digitalizamos uno que ya existe.**

---

## La plataforma es barata; lo caro son los ISP y el daño colateral

### Lo que se sabe de costos (y cuánto confiar en cada número)

| Dato | Valor | Fuente | Confiabilidad |
|---|---|---|---|
| Desarrollo de Piracy Shield | ~€25.000 (SP Tech a la Lega) | [QuiFinanza](https://quifinanza.it/sport-economy/pezzotto-piracy-shield-blocco-vpn/910712/) | ⚠️ Baja. Otras fuentes: €20k o €650k |
| Operación de SP Tech | ~€58.000/año (la paga la Lega) | [QuiFinanza](https://quifinanza.it/sport-economy/pezzotto-piracy-shield-blocco-vpn/910712/) | ⚠️ Baja. Otra versión: €100k/año ([Borsa&Finanza](https://borsaefinanza.it/piracy-shield-come-funziona-piattaforma-anti-pirateria/)) |
| Mantenimiento a cargo de AGCOM | €66.000 | [Punto Informatico](https://www.punto-informatico.it/piracy-shield-la-piattaforma-regalata-dalla-serie-a-costa-66-mila-euro/) | Media |
| Gasto de AGCOM en nube y servicios (2024) | ~€256.000. Total con personal: ~€650.000 | [HDblog](https://www.hdblog.it/microsoft/articoli/n599103/piracy-shield-aumento-costi/) | Media |
| Costo de funcionamiento esperado | **~€2M/año**, pagado con impuestos | La Repubblica vía [TorrentFreak](https://torrentfreak.com/piracy-shield-2-0-iptv-blocking-system-costs-will-be-paid-by-italian-taxpayers-240620/) | ⚠️ Media-baja: La Repubblica está detrás de paywall y AGCOM no lo confirma |
| Costo para los ISP italianos | **~€10M/año** reclamados, sin compensación | [ZeusNews](https://www.zeusnews.it/n.php?c=31580) | Media. Lo reclaman los propios ISP |
| Subsidio a los ISP italianos | Cubriría ~2/3. Monto no informado | [TorrentFreak](https://torrentfreak.com/piracy-shield-2-0-iptv-blocking-system-costs-will-be-paid-by-italian-taxpayers-240620/) | Media |
| De qué está hecho el costo del ISP | Sobre todo **horas extra de personal**, no hardware | [TorrentFreak](https://torrentfreak.com/piracy-shield-2-0-iptv-blocking-system-costs-will-be-paid-by-italian-taxpayers-240620/) | Media |
| Francia, España, Reino Unido, LatAm | **Sin cifras publicadas** | — | No existe el dato |
| Vendors (watermarking, monitoreo) | Sin precios públicos. Todo por contrato privado | [notas de vendors](https://www.friendmts.com/blog/a-year-of-decisive-action-friend-mts-2025-highlights) | No existe el dato |

**La conclusión es robusta aunque cada cifra sea débil.** Con cualquier versión, la plataforma central de Italia cuesta entre decenas de miles y unos pocos millones de euros por año, mientras los ISP reclaman unos €10M por año y el daño colateral (Google Drive, Cloudflare, miles de sitios) no figura en ninguna planilla. Construir el orquestador es barato. El costo está en la **operación manual del ISP** (guardias, cargar reglas a mano, acordarse de sacarlas) y en el **sobrebloqueo**. Nuestras dos features centrales, el agente ISP automático y el vencimiento automático, atacan justo esos dos costos.

**Quién paga hoy:**

| Modelo | Plataforma | Costo del ISP | Sobrebloqueo |
|---|---|---|---|
| Italia | Estado (impuestos) + Lega | ISP, con subsidio parcial prometido | Terceros y usuarios |
| Francia | Estado (ARCOM) | ISP | Terceros |
| España | LaLiga | ISP (que además venden el fútbol) | Terceros (Cloudflare, pymes) |
| Argentina hoy | Nadie: oficio → ENACOM o cámaras | ISP y cámaras (CABASE se queja) | Nadie lo mide |
| **Nosotros [PROPUESTA]** | **Tasa por orden al solicitante** | **Gratis para ISP chicos (agente + feed)** | **Solicitante** (lo pide EuroISPA ([Ecosistema Startup](https://ecosistemastartup.com/?p=91815))) + vencimiento automático |

### Nuestro costo cloud por partido **[ESTIMACIÓN]**

Supuestos: 30 partidos por mes, un motor (detector + armado del expediente) por partido, 2,5 h por motor (90 min + entretiempo + previa y cierre), sandbox de 2 vCPU / 4 GB y región iad1. Precios: Vercel Sandbox Pro a US$ 0,128 por hora de CPU activa y US$ 0,0212 por GB-h de memoria ([Vercel Docs](https://vercel.com/docs/sandbox/pricing)). Neon Free incluye 100 CU-h y Launch cuesta US$ 0,106 por CU-h ([Neon](https://neon.com/pricing)).

| Ítem | Escenario bajo (25% CPU) | Escenario alto (100% CPU) |
|---|---|---|
| Memoria (300 GB-h) | US$ 6,36 | US$ 6,36 |
| CPU activa | US$ 4,80 | US$ 19,20 |
| **Sandbox / mes** | **≈US$ 11** | **≈US$ 26** |
| Neon (app + log de auditoría) | US$ 0 (Free) | ≈US$ 18 (Launch) |
| **Total mensual** (con plan Pro) | **≈US$ 20–25** | **≈US$ 45–60** |
| **Por partido y por motor** | **≈US$ 0,35** | **≈US$ 0,90** |

- Escala de forma lineal. Con 10 motores por partido (uno por cada plataforma pirata vigilada) quedaría en unos US$ 200–500 por mes.
- ⚠️ **Falta verificar antes del pitch:** el precio por asiento de Vercel Pro (se cree que ~US$ 20 por miembro por mes, sin confirmar en vercel.com/pricing), las tarifas de la región São Paulo (gru1) y el CPU que consume decodificar HLS, que puede empujar el costo al escenario alto.
- ⚠️ **Límite de la demo:** en el plan Hobby, una sesión de Sandbox dura **como máximo 45 minutos** ([Vercel Docs](https://vercel.com/docs/sandbox/pricing)). Con Hobby no se puede vigilar un partido entero: hay que mostrar un tramo o reiniciar la sesión. Si alguien pregunta, decirlo así.
- Frase utilizable: *"Vigilar un partido nos cuesta entre 35 y 90 centavos de dólar de nube"*, aclarando que es una estimación nuestra.
- **No conviene** decir "Italia gasta €2M y nosotros US$ 600" como comparación directa: compara su operación completa con nuestra nube sin personal. Mejor: "el costo grande nunca fue el software: en Italia los ISP reclaman ~€10M por año; nosotros les sacamos el trabajo manual".

---

## Un orquestador público y open source, pagado por quien pide el bloqueo

### Cómo se vende hoy

- **Plataforma donada por el beneficiario (Italia).** Al Estado le sale barato, pero pierde legitimidad: la hizo una empresa ligada a los abogados de la Lega ([Cloudflare blog](https://blog.cloudflare.com/standing-up-for-the-open-internet/)).
- **Servicio privado de la liga (España, LaLiga / Sportian).** La liga detecta y manda listas, y su brazo comercial vende "Piracy Guard" ([Wikipedia: Sportian](https://en.wikipedia.org/wiki/Sportian)). Es eficaz para el titular, pero los terceros no tienen voz.
- **Servicio gestionado por contrato (vendors).** El cliente típico de Friend MTS es el **broadcaster licenciatario** (beIN, JAS TV, VOYO), no la liga ([Friend MTS](https://www.friendmts.com/blog/a-year-of-decisive-action-friend-mts-2025-highlights)). En Argentina equivaldría a ESPN o TNT más que a la LPF.
- **Regulador con laboratorio propio (Brasil, Anatel).** Escala bien, pero es un modelo administrativo que acá no se puede copiar por el art. 57.
- **Conectores ISP de terceros (Italia, Aryel).** Existe un mercado chico de "enchufes" a la API estatal (⚠️ €1.500 por año según un resumen de buscador; la página no se pudo leer) ([piracyshield.it](https://piracyshield.it/)). Esto confirma que un feed estándar puede generar su propio ecosistema.

### Nuestra propuesta de empaquetado **[PROPUESTA]**

| Componente | Lo opera | Lo paga |
|---|---|---|
| Motor de detección + expediente | El titular o su proveedor, con el motor open source | El titular (es su costo de enforcement) |
| Firma del juez de turno (celular) | Poder Judicial | Fondos judiciales. La tasa cubre la plataforma |
| Registro + API + log público | ENACOM, que hoy ya recibe los oficios | **Tasa por orden** pagada por el solicitante |
| Agente ISP (feed RPZ + lista de IP con TTL) | Cada ISP | **Gratis**. Las grandes telcos ya tienen la capacidad |
| Reclamos | Cualquier afectado, desde el registro público | Gratis. Si el reclamo prospera, paga el solicitante |

- **Orden de magnitud de la tasa [ESTIMACIÓN]:** suponiendo que la plataforma completa (nube + 1–2 personas de operación en ENACOM) cueste unos US$ 100.000 por año y haya unos 1.000 partidos por año (LPF + copas), la tasa da **≈US$ 100 por partido**. Ambos supuestos son nuestros, sin benchmark.
- **Por qué open source y público:** neutraliza la crítica del conflicto de intereses de Italia y permite que cualquiera audite el guardrail anti-CDN.
- **Por qué gratis para el ISP:** las cámaras hablan de más de 1.200–1.500 pymes y cooperativas (⚠️ dato gremial, no censo oficial) ([dplnews](https://dplnews.com/telecomunicaciones-empresarios-de-internet-advierte-riesgo-para-pymes-y-cooperativas/)). CABASE ya objetó que la orden de 2025 suponía que cualquier prestador puede bloquear en tiempo real y no contemplaba costos ([BAE Negocios](https://www.baenegocios.com/sociedad/Habra-un-inedito-bloqueo-al-futbol-libre-en-vivo-durante-el-fin-de-semana-20250530-0031.html)). También pidió que la Justicia no use a las cámaras como intermediarias ([CABASE](https://www.cabase.org.ar/los-bloqueos-no-son-la-solucion-al-problema-de-la-pirateria/)). La API resuelve las dos quejas.
- **Diseño a cuidar:** en Canadá, algunos ISP **registraron las IP de sus clientes** al aplicar bloqueos dinámicos ([TorrentFreak](https://torrentfreak.com/canadian-isps-blocked-pirate-iptv-logged-customer-ip-addresses-230331/)). Nuestro agente no debe loguear a los abonados, y conviene decirlo.

### Propuesta normativa (para el criterio de 15 puntos) **[PROPUESTA]**

1. **No hace falta cambiar la ley de fondo:** el art. 57 de la Ley 27.078 ya exige orden judicial y la plataforma la provee.
2. **Protocolo o acordada de juez de turno** para órdenes de propiedad intelectual en vivo (⚠️ no verificamos que hoy exista ese turno para fines de semana).
3. **Resolución de ENACOM:** registro de prestadores con un endpoint técnico obligatorio y declaración del tipo de bloqueo que cada ISP soporta. Hoy ENACOM no tiene un registro actualizado.
4. **Reglas de daño colateral:** ninguna IP de un ASN de CDN o de hosting compartido sin aviso previo. Toda IP vence al final del partido más un margen. El dominio puede persistir solo por orden expresa.
5. **Transparencia:** registro público de cada orden, su vencimiento y su acuse, más reclamos con respuesta en plazo.
6. **Responsabilidad del solicitante** por el sobrebloqueo (tasa o fianza), como pide EuroISPA.

---

## Ganar el pitch: un número, cinco ángulos y respuestas listas

### Candidatos para "un número" (ordenados por solidez)

| # | Frase | Fuente | Por qué sí | Riesgo |
|---|---|---|---|---|
| 1 | **"Para un solo Superclásico, la Justicia ordenó bloquear 182 dominios y ENACOM avisó a todos los ISP del país. ¿Cuántos cumplieron, y cuándo? Nadie lo sabe."** | [Infobae](https://www.infobae.com/judiciales/2026/11/01/la-justicia-ordeno-el-bloqueo-de-mas-de-180-sitios-web-que-planeaban-transmitir-ilegalmente-el-superclasico/); [La Nación](https://www.lanacion.com.ar/seguridad/el-otro-superclasico-bloquearon-182-sitios-ilegales-que-iban-a-retransmitir-el-partido-que-boca-le-nid02112026/) | Es un hecho judicial, local y de hace 10 días. Apunta al **proceso** (lo que resolvemos), no a pérdidas que se pueden discutir | Bajo. "Nadie lo sabe" = no se publicó. Decirlo así |
| 2 | "Los 30 sitios piratas más visitados desde Argentina sumaron **97 millones de visitas en un mes**" (junio 2026) | [ADSLZone](https://www.adslzone.net/noticias/descargas/bloqueo-300-webs-futbol-pirata-argentina/); [DPL News](https://dplnews.com/?p=329227) | Reciente, local y muestra urgencia | Medio: lo dice la industria (ALIANZA) y son visitas, no personas |
| 3 | "**Más de 14 millones** de usuarios únicos por mes consumen contenido pirata en Argentina" | ASIET vía [DPL News](https://dplnews.com/?p=276615) | Redondo y fácil de entender | Medio: es de **2023** e incluye todo contenido, no solo fútbol |
| 4 | "Casi 46 millones de hogares de LatAm, unos US$ 10.000 millones perdidos por año" | Alianza/Fabric vía [Piracy Monitor](https://piracymonitor.org/latin-america-in-q4-of-2025-pirates-invaded-46-million-online-households-nearly-10-billion-lost/) | Escala regional | Medio-alto: lo dice la industria y hay versiones de 8 y de 22 países |

**Recomendación:** abrir con el **#1** porque el jurado evalúa el circuito y la evidencia, y ese número muestra un circuito sin evidencia. Usar el #2 como dato de tamaño. No meter un número de pérdidas en dólares en los 30 segundos iniciales.

### Ángulos de pitch, ordenados por peso en la rúbrica

1. **Circuito completo (25): "Cada uno tiene una pieza; nadie tiene el circuito".** Italia: rápido, sin juez. España: juez, pero la lista la maneja la liga. Argentina: juez, pero sin API ni acuse. Vendors: detección, sin juez ni ISP. Nosotros: detección → expediente → firma → orden por API → acuse → vencimiento → registro. **Mostrarlo de punta a punta en vivo.**
2. **Evidencia (25): "Cada orden es verificable por cualquiera".** Italia no publica la lista completa, y Cloudflare tuvo que apelar para pedir acceso a los registros de Piracy Shield ([Cloudflare blog](https://blog.cloudflare.com/standing-up-for-the-open-internet/)). En el Reino Unido los detalles son secretos. En Chile se suman sitios "por interpretación". Nosotros: expediente con hash, log encadenado y registro público. En la demo, verificar un hash delante del jurado.
3. **Daño colateral (20): "Bloqueos que se apagan solos y nunca tocan una CDN".** En España, unas 3.000 IP por fin de semana contra unas 120 en la sentencia ([Bandaancha](https://bandaancha.eu/articulos/esta-verdadera-dimension-bloqueos-futbol-11323)). En Italia, sitios legítimos bloqueados durante meses ([RIPE Labs](https://labs.ripe.net/author/antonio-prado/live-event-blocking-at-scale-effectiveness-vs-collateral-damage-in-italys-piracy-shield/)). En la demo: (a) una IP de Cloudflare que el sistema rechaza o degrada a bloqueo por dominio y (b) un bloqueo de IP que vence al pitazo final. Pegarle a Argentina ahora: desde septiembre LaLiga tiene autorización para bloquear IP acá "igual que en España" ([RedesZone](https://www.redeszone.net/noticias/redes/laliga-bloquear-webs-tiempo-real-partidos-argentina/)).
4. **Velocidad (15): "Un partido dura 90 minutos".** En Francia el plazo bajó a unos 45 minutos y ARCOM lo considera insuficiente ([Siècle Digital](https://siecledigital.fr/2026/03/24/le-streaming-illegal-recule-en-france/)). Italia exige 30 y Brasil emite órdenes cada 30. **Poner un cronómetro en pantalla** desde la detección hasta el acuse del ISP simulado y decir el número medido. No prometer uno que no se midió.
5. **Claridad + propuesta normativa (15): "No hay que cambiar la ley: hay que darle una API".** El art. 57 ya exige juez, así que la propuesta se reduce a juez de turno + resolución de ENACOM + tasa del solicitante. El cierre federal: "desde Telecom hasta la cooperativa de Cafayate, con el mismo feed".
6. *(Secundario)* **Costo:** "el software nunca fue lo caro: en Italia los ISP reclaman ~€10M por año. A nosotros vigilar un partido nos cuesta centavos de nube **[estimación]**".
7. *(Cierre)* **"Generamos los datos que nadie tiene".** La Comisión Europea admite que **no hay datos suficientes** sobre la eficacia de las órdenes dinámicas ([TorrentFreak](https://torrentfreak.com/live-sports-piracy-eu-commission-admits-that-anti-piracy-advice-had-limited-impact-251124/)). El registro público es el instrumento que mide.

**Frase síntesis:** *"Europa tuvo que elegir. Italia y Francia sacaron al juez; España le dio la lista a la liga. Nosotros: juez en el loop, minutos, bloqueos que vencen solos y todo público."*

### Preguntas probables del jurado

| Objeción | Respuesta corta |
|---|---|
| **"¿Y el sobrebloqueo?"** | Chequeo de ASN en el expediente: si la IP es de una CDN o de hosting compartido, va solo por dominio o con aviso. Toda IP vence al final del partido. El registro público permite que cualquiera vea si su sitio cayó y reclame |
| **"¿Existe un juez de turno que firme esto un domingo a la noche?"** | Hoy no lo verificamos; es parte de la propuesta normativa (protocolo o acordada). Sin firma no sale ninguna orden: preferimos no bloquear antes que bloquear sin juez |
| **"¿Por qué no hacerlo administrativo, como Brasil o Perú, que es más rápido?"** | Porque el art. 57 de la Ley 27.078 exige orden judicial. Además, nuestro objetivo es que la firma tarde lo mismo que un aviso administrativo |
| **"Se van a VPN o a DNS públicos."** | Cierto para una minoría. La evidencia muestra que bloquear muchos sitios a la vez redujo la piratería un 16–22% en el Reino Unido aunque existieran VPN ([CMU](https://www.cmu.edu/entertainment-analytics/documents/effectiveness-of-anti-piracy-efforts/the-effect-of-piracy-website-blocking.pdf)). No buscamos el 100%: buscamos que piratear durante 90 minutos sea incómodo. ⚠️ Es un estudio de 2014–2019 sobre sitios en general, no sobre fútbol en vivo |
| **"¿Funciona en vivo? ¿Hay pruebas?"** | Honestamente, no hay un estudio específico sobre deporte en vivo: lo reconocen los propios investigadores y la Comisión Europea. Por eso el registro público genera esos datos |
| **"¿Y los clones (Fútbol Libre → Pelota Libre)?"** | La orden es dinámica: el motor vuelve a detectar y el juez aprueba la reincidencia con un toque ([Diario de Cuyo](https://www.diariodecuyo.com.ar/tecnologia/el-cierre-de-futbol-libre-le-abrio-la-puerta-a-pelota-libre-quien-trasmite-de-forma-ilegal-partidos-de-futbol-y-otros-deportes-1651343)) |
| **"¿Quién paga? Los ISP chicos no pueden."** | Paga el solicitante con una tasa por orden. El agente ISP es gratis y consume el tipo de bloqueo que cada ISP declara poder aplicar |
| **"¿No viola la neutralidad de red?"** | El art. 56 la garantiza y el art. 57 admite el bloqueo con orden judicial. Cada orden de la plataforma la tiene, con alcance y vencimiento explícitos |
| **"¿El Estado va a vigilar qué mira la gente?"** | No. La detección la hace el titular sobre los streams piratas, no sobre los usuarios. El agente ISP no registra abonados (al revés de lo que pasó en Canadá) |
| **"¿Para qué un log encadenado y no una base común?"** | Para que nadie pueda reescribir la historia, ni el Estado ni el titular. En Italia, Cloudflare tuvo que litigar para ver los registros |
| **"LaLiga ya tiene su orden en Argentina, ¿para qué esto?"** | Esas órdenes pueden pasar por la plataforma y ganan acuse, vencimiento y guardrail anti-CDN. Es el canal, no un competidor |
| **"¿Cuánto cuesta?"** | Entre US$ 20 y 60 de nube por mes, o unos centavos por partido y motor **[estimación]**. El costo real son las personas de operación y lo cubre la tasa |
| **"¿Lo que vimos es real?"** | Decir qué está simulado (ISP, firma, datos) y qué no, y aclarar que el plan Hobby corta las sesiones de Sandbox a los 45 minutos |

---

## Números que nadie debe decir mal en el escenario

| Dato | Versiones que circulan | Qué decir (o no decir) |
|---|---|---|
| % de hogares argentinos que piratean | 42,6% (prensa local, pero parece ser el **promedio de LatAm**) ([Piracy Monitor](https://piracymonitor.org/latin-america-in-q4-of-2025-pirates-invaded-46-million-online-households-nearly-10-billion-lost/)) · 45,5% ([La Nación](https://www.lanacion.com.ar/seguridad/bloquearon-en-vivo-sitios-y-apps-que-transmitian-partidos-de-futbol-de-manera-ilegal-nid02062025/)) · "más del 46%" (Bacaloni) · 54,4% ([ConverCom](https://convercom.info/comunidades/contenidos/pirateria-audiovisual-mueve-mas-us-12-000-millones-ano-america-latina-alcanza-cuatro-cada-diez-hogares-banda-ancha/)) | **No usarlo.** Si hace falta: "cerca de la mitad, según estudios de la industria" |
| Pérdidas en Argentina | US$ 590M/año (La Nación) · US$ 571M (⚠️ sin URL primaria) · US$ 258M (LM Neuquén) | Evitar. Si preguntan: "cientos de millones de dólares por año, según la industria; no hay cifra auditada" |
| Pérdidas en LatAm | US$ 12.360M · ~US$ 12.000M · US$ 9.970M solo online · US$ 6.500M · US$ 8.000M+ | Si se usa: "más de US$ 10.000 millones por año, según la industria". Impuestos y empleos no coinciden entre versiones (US$ 1.800M vs 2.545M; 46.272 vs 75.103) |
| Costo de Piracy Shield | €20k · €25k · €58k/año · €66k · €100k/año · €256k · €650k · €2M/año | No dar un único número como dato. Usar "los ISP reclaman ~€10M/año" |
| Daño colateral en España | >13.500 webs (Hayahora) · >500.000 dominios (OONI) · 554.507 dominios (estudio del PE) | "Cientos de miles de dominios según mediciones independientes", o lo más seguro: "3.000 IP por fin de semana con una sentencia de 120" |
| IP bloqueadas en España | ~3.000 por fin de semana · 500–1.000 por partido · "10.000 por jornada" (directivo de beIN, ⚠️) | "Miles de IP por fin de semana" |
| "60%" de LaLiga | Datos de LaLiga: bloquea **~60% de los streams** ([Tech Times](https://www.techtimes.com/articles/316733/20260516/spains-parliament-votes-rein-laligas-mass-ip-blockades-test-case-eu-internet-governance.htm)). Otra nota: los bloqueos **bajaron la piratería 60%** ([Vozpópuli](https://www.vozpopuli.com/economia/empresas/laliga-y-tebas-se-enfrentan-a-un-aluvion-de-demandas-por-bloquear-las-ip-para-evitar-el-futbol-pirata.html)) | Son dos afirmaciones distintas y las dos son autodeclaradas. **No usar** |
| Duración del bloqueo de Google Drive (Italia) | Entre 3 y 12+ horas según la fuente ([Gigazine](https://gigazine.net/gsc_news/en/20241021-google-drive-blackout)) | "Durante horas" |
| Francia: cuándo arranca el sistema automático | "Más adelante este año" (Reclaim The Net) · "enero de 2027" (Siècle Digital) | "Aprobado en julio de 2026, todavía no implementado" |
| Francia: velocidad | ~45 min (ARCOM, 2026). No hay medición oficial independiente | "Unos 45 minutos según ARCOM, que lo considera insuficiente". **No** decir "la mejor de Europa" |
| Brasil | 43.000 IP bloqueadas (ago-2026) vs 55 IP bloqueadas en mayo-2026. Caída del 82% y <0,1% de reclamos | Siempre "según ANCINE". Son cifras autodeclaradas |
| Cantidad de ISP en Argentina | >1.200 (CAPPI) · >1.500 (LAC-ISP) · 547 cooperativas (2021) · 97,7% de los accesos en manos de grandes (⚠️) | "Más de mil pymes y cooperativas, según las cámaras" |
| Reino Unido | Todas las fuentes son de 2017–2021 | Presentarlo como "pionero desde 2017", sin cifras actuales |
| Nuestra velocidad | No medida | Solo el número que muestre el cronómetro de la demo |
| Nuestro costo | Estimación con precios de Vercel y Neon. El asiento de Vercel Pro no está verificado | Decir siempre "estimado" |

---

## Conclusión

El hallazgo que cambia el pitch es dónde está el hueco. El mercado está lleno de **detección** (vendors) y de **ejecución** (ISP, reguladores), y la capa del medio está vacía: el orquestador que convierte un hallazgo en una orden firmada, la distribuye a miles de ISP en el formato que cada uno puede aplicar, recibe el acuse y la apaga sola. Nadie la vende. Italia la tiene, pero sin juez y donada por el beneficiario, y en Argentina hoy es un oficio que se reenvía por mail. La restricción argentina (sin juez no hay bloqueo) obliga a diseñar esa capa con garantías desde el principio, en lugar de agregarlas después de un escándalo como el de Google Drive o el de Cloudflare. Eso es exportable: la UE discute un reglamento de 30 minutos sin resolver las garantías, y Francia todavía no implementó su sistema automático.

Además, el momento es ahora, y no por la piratería en general. Desde septiembre de 2026 LaLiga tiene autorización judicial para bloquear IP en tiempo real en Argentina con el mismo modelo que en España afecta a cientos de miles de dominios. El riesgo de daño colateral ya dejó de ser europeo y teórico. Una plataforma con guardrail anti-CDN, vencimiento automático y registro público no compite con esas órdenes: es el canal que las vuelve auditables. Ese es el argumento que se gana el 20 de daño colateral y el 15 normativo sin necesitar ningún número dudoso.
