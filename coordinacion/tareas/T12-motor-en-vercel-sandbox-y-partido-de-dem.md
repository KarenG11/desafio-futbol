---
id: T12
titulo: Motor en Vercel Sandbox y partido de demo online
carpeta: plataforma/nube/
estado: hecha
dueno: alejo
desde: 2026-11-11 19:18
creada_por: alejo
depende_de: T05, T11
---
## Qué hay que hacer
- Desde la app de Vercel (T11), una ruta que prende un Vercel Sandbox (SDK de Python: paquete vercel, vercel.sandbox) con el repo clonado.
- Modo demo: en el Sandbox corren el simulador de la organización (escenario de práctica, --acelerar 6) y nuestro motor apuntando a él. Al terminar corre evaluacion/verificar.py y guarda la salida en la base para mostrarla en la web.
- Modo final: solo el motor, apuntando a la URL del simulador que asigne la organización.
- DATABASE_URL entra por env del Sandbox. Nada de claves en el repo.
- Un Sandbox por partido. En Hobby la sesión dura 45 min: alcanza con --acelerar 6.

## Terminada cuando
Desde la URL pública se aprieta Correr partido de práctica, el juez aprueba desde el celular y al final se ve la salida del verificador, sin ninguna notebook prendida.
