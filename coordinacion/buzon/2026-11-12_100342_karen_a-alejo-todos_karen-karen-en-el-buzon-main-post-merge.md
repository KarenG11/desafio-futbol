---
de: karen
para: alejo,todos
fecha: 2026-11-12 10:03
asunto: Karen (karen) en el buzón + main post-merge verificado
requiere_respuesta: no
responde_a: 2026-11-11_122155_alejo_a-todos_bienvenida-como-arrancar.md
---
Hola, soy Karen Gutierrez (GitHub KarenG11), nombre de buzón: karen. Ya completé mi fila en equipo.md. Hice la integración del PR #1 (motor + despacho + entregables).

Verificación del main después del merge, en Windows con Python 3.15: pruebas unitarias 6 de 6 OK. partido_completo de práctica a x30, dos corridas: 7 de 7, visibilidad residual 3,5 % y 3,3 %, 0 colateral, 0 falsos positivos, 0 rechazadas, 0 fuera de turno, 0 IP post partido; los 12 chequeos OK. La URL pública responde (/juez/ 200, /api/estado ok). partido_demo.py llama a plataforma.main --base --sin-web y el motor nuevo acepta esas opciones.

Pendiente para el viernes:
1. Alejo: redeploy en Vercel y un partido desde /juez/demo.html con el motor nuevo (T11/T12 figuran como no re-verificados en entrega/README.md).
2. Respuesta de la organización sobre si el simulador del final se alcanza desde internet.
3. T04: probarla desde el celular con la URL pública.
4. T09: grabar el video; los números del pitch tienen que salir de evidencias/RESULTADOS.md (motor actual).
5. En la final, correr con --exportar-entrega.

Puedo encargarme de cualquiera que no requiera la cuenta de Vercel; díganme cuál.
