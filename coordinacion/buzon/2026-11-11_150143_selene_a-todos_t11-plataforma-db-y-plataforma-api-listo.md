---
de: selene
para: todos
fecha: 2026-11-11 15:01
asunto: T11: plataforma/db y plataforma/api listos en el repo
requiere_respuesta: no
---
Ya subí plataforma/db/ (esquema.sql, todas las funciones de la guía para Postgres y SQLite, y semilla.py), plataforma/api/app.py (API de contratos v1.4 con X-Juez-Pin y /juez montado) y la config de Vercel (pyproject.toml, requirements.txt, vercel.json). Pruebas: python -m plataforma.db.test_db_api (10/10 OK). Ahora conecto el proyecto en Vercel + Neon para compartir la URL pública.
