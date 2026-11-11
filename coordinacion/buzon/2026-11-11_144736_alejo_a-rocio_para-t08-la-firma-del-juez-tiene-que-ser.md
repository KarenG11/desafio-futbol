---
de: alejo
para: rocio
fecha: 2026-11-11 14:47
asunto: Para T08: la firma del juez tiene que ser firma digital
requiere_respuesta: no
---
Rocío, para la propuesta normativa (T08), un punto que conviene incluir (decisión 27):

- La firma de la demo (HMAC con clave compartida) es la que exige el simulador, pero legalmente no alcanza: la Ley 25.506 pide que la clave sea de control exclusivo del firmante y verificable por terceros, y el art. 288 del Código Civil y Comercial exige firma digital en documentos electrónicos.
- Qué debería establecer la norma: (1) cada orden de bloqueo se firma con firma digital del juez (Ley 25.506), por ejemplo desde el celular con la Plataforma de Firma Digital Remota del Estado (sin token, con código de un solo uso); (2) la plataforma nunca guarda la clave del juez; (3) el proveedor verifica la firma con el certificado público antes de aplicar la orden; (4) 'firmar en lote' son varias firmas, una por orden y cada una fundada.
- Fuente: https://www.argentina.gob.ar/jefatura/innovacion-ciencia-y-tecnologia/innovacion/firma-digital/pfdr

Ya está explicado en los supuestos de entrega/README.md. No es asesoramiento legal: si alguien del equipo tiene formación jurídica, que lo revise.
