# Propuesta normativa: órdenes judiciales de bloqueo en vivo

*Versión de entrega (1 página). Amplía [`propuesta-normativa.md`](propuesta-normativa.md), escrita por Rocío durante el evento, con lo que aprendimos al probar la plataforma contra el simulador oficial. No es asesoramiento legal.*

**Objetivo:** que un juez pueda ordenar en minutos, durante un partido, el bloqueo de un stream pirata en **todos** los proveedores de internet, sin dañar sitios legítimos y dejando un rastro verificable.

**1. Orden marco y juez de turno.**
- El art. 57 de la Ley 27.078 ya admite el bloqueo con orden judicial: no hace falta una figura nueva, sino un **procedimiento**.
- Una acordada fija un juzgado de turno por evento, con su horario publicado. Solo firma el juez de turno en ese minuto, y el entrante **ratifica** las órdenes vigentes.
- Sin juez de turno, no sale ninguna orden.
- *Por qué:* el turno cambia en medio del partido. Con esta regla, el verificador dio 0 órdenes fuera de turno.

**2. Firma digital y expediente.**
- Cada orden va con su expediente (capturas con huella SHA-256, origen, motivo del tipo de bloqueo) y con **firma digital** del juez (Ley 25.506, art. 288 CCyC), por ejemplo con la Plataforma de Firma Digital Remota.
- El proveedor verifica la firma antes de aplicar. El HMAC con clave compartida del prototipo **no** alcanza legalmente.
- Cada acción queda en una auditoría encadenada por hashes, que se conserva durante un plazo legal.

**3. Registro de proveedores y plazos (ENACOM).**
- Todo licenciatario, grande o chico, declara un **canal electrónico** de órdenes y qué bloqueos puede aplicar (IP, dominio).
- La norma fija un **plazo máximo de aplicación en minutos** (en el simulador, el proveedor más lento tarda 6) y un **acuse obligatorio** por orden: recibida, aplicada, fallida o rechazada con motivo. Si una orden falla, se reenvía.
- *Por qué:* hoy nadie sabe quién cumplió.

**4. Proporcionalidad y daño colateral.**
- **Se prefiere el dominio.** Una IP se bloquea solo si hay evidencia de que aloja exclusivamente al sitio pirata. Ante la duda, se bloquea el dominio.
- Toda orden **vence al terminar el evento**; extenderla requiere una orden nueva.
- Un dominio en común no prueba un único titular. Por eso el hosting debe informar en minutos, a pedido del juzgado, si una IP es exclusiva de un cliente.

**5. Reclamos y levantamiento rápido.**
- Canal público para que un sitio afectado reclame durante el partido. El reclamo se cruza con las órdenes activas y llega al juez de turno.
- Si procede, el juez **levanta con firma** en todos los proveedores y ordena un bloqueo más preciso. El reclamo queda resuelto cuando **todos** confirman el levantamiento.

**6. Transparencia.**
- Registro público en tiempo real: qué se bloqueó, tipo, juzgado, vigencia y estado por proveedor, sin datos de usuarios.
- Permite reclamar y genera datos sobre la eficacia del bloqueo en vivo, que hoy no existen.

**7. Costos y responsabilidad.**
- Paga quien se beneficia, el titular de derechos; para el proveedor el canal es gratuito.
- El titular presta **caución** (art. 79, Ley 11.723) por bloqueos erróneos. El proveedor que cumple una orden válida queda exento de responsabilidad.
