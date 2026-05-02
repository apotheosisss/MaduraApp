# CLAUDE.md — MaduraApp
> Archivo de contexto principal para Claude Code. Lee este archivo primero, luego los documentos en `/docs/claude/`.

## Qué es este proyecto

MaduraApp es un sistema de análisis de madurez agrícola mediante visión computacional. Una app Android nativa captura imágenes de frutas climatéricas y las envía a una API REST (FastAPI) que ejecuta inferencia con YOLO26n, devolviendo un diagnóstico de madurez en tiempo real.

**Repositorio:** https://github.com/apotheosisss/MaduraApp  
**Estado actual:** Sprint 1 backend completo (servicios, routers, tests, Alembic). Sprint 2 Android scaffolding listo.  
**Fase actual:** Sprint 2 — App Android (CameraX + Retrofit + MVVM).

---

## Stack tecnológico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | Android Nativo — Kotlin + CameraX | API 29+ |
| Backend | Python + FastAPI | 3.12 / 0.135 |
| Modelo IA | YOLO26n (Ultralytics) | Enero 2026 |
| ORM | SQLAlchemy async | 2.0.30 |
| BD (prod) | PostgreSQL | 16 |
| BD (dev) | SQLite + aiosqlite | — |
| Containerización | Docker + Docker Compose | — |
| CI/CD | GitHub Actions | — |
| Cloud | Render / AWS App Runner | — |

---

## Estructura del repositorio

```
MaduraApp/
├── CLAUDE.md                        ← Este archivo
├── docs/
│   ├── claude/                      ← Contexto extendido para Claude Code
│   │   ├── 01_arquitectura.md
│   │   ├── 02_backend.md
│   │   └── 03_decisiones.md
│   ├── diagramas/
│   │   ├── MaduraApp_DiagramaCasosDeUso.png
│   │   ├── MaduraApp_DiagramaClases.png
│   │   ├── MaduraApp_MER.png
│   │   ├── Gantt_MaduraApp.png
│   │   └── Ishikawa.png
│   ├── informes/
│   │   ├── Informe_Evaluacion_1.pdf
│   │   └── ERS_MaduraApp.pdf
│   ├── prototypes/
│   └── wireframes/
│       └── WireFrame MaduraApp.pdf
├── backend/
│   ├── app/
│   │   ├── main.py                  ← Entry point FastAPI + lifespan
│   │   ├── routers/
│   │   │   ├── predict.py           ← POST /v1/predict
│   │   │   └── history.py           ← GET /v1/history
│   │   ├── services/
│   │   │   ├── inference_service.py ← Lógica YOLO26n (PENDIENTE)
│   │   │   └── history_service.py   ← CRUD historial (PENDIENTE)
│   │   ├── models/
│   │   │   └── scan_entity.py       ← SQLAlchemy ORM (PENDIENTE)
│   │   ├── schemas/
│   │   │   ├── scan_result.py       ← Pydantic response
│   │   │   └── request.py           ← Pydantic input
│   │   └── core/
│   │       ├── config.py            ← Settings pydantic-settings
│   │       └── yolo_wrapper.py      ← Wrapper YOLO26n
│   ├── tests/
│   │   ├── test_predict.py          ← Solo placeholder por ahora
│   │   └── test_history.py
│   ├── weights/                     ← .pt excluido de Git (.gitignore)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                        ← Android Kotlin (pendiente)
├── scripts/
│   └── train_model.py               ← CRISP-DM training pipeline (PENDIENTE)
├── .github/workflows/
│   └── backend_ci.yml               ← CI: install + pytest
├── docker-compose.yml
└── .env.example
```

---

## Comandos frecuentes

```bash
# Backend — levantar en desarrollo
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Documentación API (Swagger)
# http://localhost:8000/docs

# Tests
pytest tests/ -v

# Docker completo (backend + PostgreSQL)
docker-compose up --build

# Git — flujo de trabajo
git checkout develop
git checkout -b feature/nombre-feature
# ... trabajar ...
git add .
git commit -m "feat: descripción"
git push origin feature/nombre-feature
# → Abrir PR a develop en GitHub
```

---

## Ramas activas

| Rama | Propósito |
|------|-----------|
| `main` | Código estable, producción |
| `develop` | Integración continua |
| `feature/backend-api` | Desarrollo API FastAPI |
| `feature/android-app` | App Android Kotlin |
| `feature/yolo26n-training` | Entrenamiento modelo IA |

---

## Qué está implementado vs pendiente

### ✅ Sprint 1 — Backend (completo)
- Estructura de carpetas y `Dockerfile` + `docker-compose.yml`
- `main.py` con lifespan, CORS, routers, app.state.model
- `core/config.py` (pydantic-settings v2) y `core/database.py` (AsyncEngine)
- `core/yolo_wrapper.py` con import lazy de ultralytics
- `services/inference_service.py` — CLASS_MAP/COLOR_MAP/RECOMMENDATION_MAP + preprocess + postprocess
- `services/history_service.py` — save/get_all con AsyncSession
- `models/scan_entity.py` — ORM tabla `scans`
- `routers/predict.py` — async completo (asyncio.to_thread) + DB
- `routers/history.py` — GET /v1/history paginado
- `schemas/scan_result.py` — ScanResult + PredictResponse + HistoryResponse
- **Alembic** — `alembic.ini`, `env.py` async, migración inicial `0001_create_scans_table`
- **Tests reales** — 9/9 passing (predict + history) con SQLite in-memory
- `.github/workflows/backend_ci.yml` (CI con tests reales)

### 🔲 Sprint 2 — Android (en progreso)
- ✅ Estructura del proyecto Gradle Kotlin DSL (`frontend/`)
- ✅ `AndroidManifest.xml` + permisos CAMERA/INTERNET + tema Material 3
- ✅ Data layer: DTOs (Kotlinx Serialization) + `MaduraApiService` (Retrofit) + `ApiClient` + `FruitRepository`
- ✅ MVVM: `ScanState` (sealed) + `ScanViewModel` (LiveData)
- ✅ `MainActivity` con CameraX preview + captura + JPEG compress
- ✅ Layout principal con semáforo de madurez (verde/amarillo/rojo)
- 🔲 Pantalla de historial (consumir `GET /v1/history`)
- 🔲 Persistencia local con Room (cache offline)

### 🔲 Pendiente — feature/yolo26n-training
- Dataset colección y etiquetado
- Script CRISP-DM entrenamiento
- Fine-tuning YOLO26n en 4 clases

---

## Convenciones de código

- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
- **Python:** PEP8, type hints obligatorios, docstrings en servicios
- **Async:** Todo el backend es async/await — no usar funciones bloqueantes
- **Variables de entorno:** Nunca hardcodear — siempre via `settings` de `core/config.py`
- **Pesos del modelo:** Nunca subir a Git — van en `weights/` que está en `.gitignore`
