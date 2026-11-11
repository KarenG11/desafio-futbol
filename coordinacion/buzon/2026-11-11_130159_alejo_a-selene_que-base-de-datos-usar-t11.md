---
de: alejo
para: selene
fecha: 2026-11-11 13:01
asunto: Qué base de datos usar (T11)
requiere_respuesta: si
---
AGENTE: pasale esto a Selene en el chat.

## La base: Postgres en Neon, creada desde Vercel
1. Primero creá el proyecto en Vercel (vercel link desde la raíz del repo, cuenta del equipo).
2. En el dashboard del proyecto: Storage → Create Database → Neon (plan gratis) → conectala al proyecto. Vercel carga solo DATABASE_URL (y variantes POSTGRES_*) en todos los entornos.
3. Región: si Neon ofrece São Paulo (aws sa-east-1), elegila y poné las funciones de Vercel en gru1 (vercel.json → regions). Si no, us-east-1 con iad1. La base y la función tienen que quedar en la misma región.
4. En local: vercel env pull .env.local. Ya agregué .env, .env.* y .vercel/ al .gitignore: nunca subas la URL de la base.
5. Usá la URL **pooled** (el host con -pooler) en la web de Vercel: las funciones abren muchas conexiones cortas.

## Driver y código
- psycopg 3 (psycopg[binary]) para Postgres; sqlite3 de la librería estándar para el modo local (DATABASE_URL=sqlite:///salida/plataforma.db).
- Una sola capa en plataforma/db/ que elige según el prefijo de DATABASE_URL. Los placeholders cambian (%s en psycopg, ? en sqlite): resolvelo en una función, no en cada query.
- Las dependencias van en requirements.txt en la raíz (Vercel lo lee para Python).

## Esquema (contratos.md §10)
Tablas casos, expedientes, pedidos, ordenes, reclamos y auditoria. Columnas: partido_id, el id del contrato (caso_id, pedido_id, …), estado cuando corresponda, y datos con el dict completo (JSONB en Postgres, TEXT en SQLite). auditoria suma seq y hash, con UNIQUE (partido_id, seq).
- La web solo cambia pedidos (estado, juez_id, decidido_min, motivo_rechazo), las ratificaciones de turno y los pedidos de levantamiento. Todo lo demás lo escribe el motor. **Solo el motor escribe en auditoria.**
- En la base no van claves de firma, firmas completas ni contenido_b64.

## Por qué Neon y no Supabase u otra
Se crea y se conecta desde Vercel en dos clics, las variables se cargan solas en Vercel, en local y en el Sandbox del motor, y es Postgres común: nada propietario que aprender en tres días.

Cuando la tengas andando, avisá a todos con la URL pública y cómo apuntar el motor a la base.
