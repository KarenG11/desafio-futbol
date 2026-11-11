# Propuesta Normativa: Bloqueo en Vivo de Transmisiones Ilegales

**Objetivo:** Establecer un marco legal ágil y seguro que permita combatir la piratería de eventos deportivos en vivo sin afectar el acceso a internet de la ciudadanía ni perjudicar a sitios legítimos.

## 1. Anclaje en la Ley Actual
La propuesta no inventa una nueva figura legal, sino que acelera un mecanismo existente. El artículo 57, inciso a) de la Ley 27.078 (Argentina Digital) ya faculta a los jueces a ordenar el bloqueo de sitios web. Lo que falta es un procedimiento digital que haga efectiva esa orden en minutos, y no en días.

## 2. Juez de Turno y Firma Digital Verificable
Debe garantizarse un juez de turno federal disponible las 24 horas durante los eventos deportivos para evitar demoras jurisdiccionales. Las órdenes deben firmarse digitalmente en la plataforma utilizando los estándares de la **Ley 25.506** y el art. 288 del Código Civil y Comercial. 
*   **Seguridad:** La plataforma nunca debe guardar la clave privada del juez. Se debe utilizar la Plataforma de Firma Digital Remota (PFDR) del Estado (con doble factor o código de un solo uso).
*   **Validación:** El proveedor de internet debe verificar la firma digital con el certificado público antes de aplicar el bloqueo.

## 3. Registro Obligatorio de Proveedores (ENACOM)
Una resolución del ENACOM debe obligar a todos los licenciatarios TIC (grandes y chicos) a declarar un canal electrónico (API o sistema RPZ) para recibir órdenes en tiempo real y establecer un plazo máximo de aplicación. Esto evita que los proveedores pequeños queden fuera del radar.

## 4. Preferencia del Bloqueo por Dominio (Cero Daño Colateral)
Para evitar afectar a ciudadanos inocentes, la ley debe priorizar el bloqueo por nombre de dominio (URL) sobre el bloqueo por dirección IP. Si el servidor aloja exclusivamente sitios piratas, se podrá bloquear la IP; si la IP es compartida con sitios legítimos, el bloqueo debe ser estrictamente por dominio. Además, los bloqueos deben tener un vencimiento automático al finalizar el evento.

## 5. Canal de Reclamos y Transparencia
Se debe establecer un canal rápido para que los sitios bloqueados por error puedan reclamar. Si se comprueba el error, un juez debe levantar la orden con firma digital y reemplazarla por un bloqueo más preciso. Asimismo, debe existir un registro público de transparencia (como el desarrollado en este proyecto) que detalle qué se bloqueó, por orden de quién y hasta cuándo.

## 6. Costos y Responsabilidad
La norma debe definir quién financia la adecuación tecnológica de los proveedores pequeños (por ejemplo, el titular de los derechos de transmisión) y exigir una caución (art. 79 de la Ley 11.723) para cubrir posibles daños por bloqueos erróneos.