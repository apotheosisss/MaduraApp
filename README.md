# MaduraApp

> Sistema de análisis de madurez agrícola mediante visión computacional e IA en la nube.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)
![YOLO26n](https://img.shields.io/badge/YOLO-26n-purple)
![Android](https://img.shields.io/badge/Android-Kotlin-orange)
![License](https://img.shields.io/badge/License-Private-red)

## Descripción

MaduraApp clasifica el estado de madurez de 4 frutos climatéricos (Aguacate Hass, Plátano, Tomate USDA, Mango) usando un modelo YOLO26n desplegado en FastAPI + nube, accedido desde una app Android nativa.

## Stack Tecnológico

| Capa       | Tecnología                          |
|------------|-------------------------------------|
| Frontend   | Android Nativo — Kotlin + CameraX   |
| Backend    | Python 3.12 + FastAPI 0.135         |
| IA         | YOLO26n Nano (Ultralytics)          |
| BD         | PostgreSQL / SQLite (dev)           |
| Cloud      | Render / AWS App Runner             |
| CI/CD      | GitHub Actions                      |

## Estructura del Repositorio

MaduraApp/
├── backend/              # API FastAPI + YOLO26n
│   ├── app/
│   │   ├── routers/      # Endpoints REST
│   │   ├── services/     # Lógica de inferencia e historial
│   │   ├── models/       # Entidades BD (SQLAlchemy)
│   │   ├── schemas/      # Modelos Pydantic
│   │   └── core/         # Config, YOLO wrapper
│   ├── tests/
│   ├── weights/          # Pesos del modelo (.pt) — no versionados
│   └── Dockerfile
├── frontend/             # App Android Kotlin
│   └── app/src/main/java/cl/duocuc/maduraapp/
├── docs/                 # Diagramas y documentación
│   ├── diagramas/        # UML, MER, Gantt, Ishikawa, WireFrame
│   └── prototypes/
├── scripts/              # Entrenamiento y utilidades
├── docker-compose.yml
└── README.md

## Setup rápido (Backend)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # Ajusta variables
uvicorn app.main:app --reload
```

API disponible en: http://localhost:8000/docs

## Endpoints principales

| Método | Endpoint          | Descripción                        |
|--------|-------------------|------------------------------------|
| POST   | /v1/predict       | Envía imagen → retorna diagnóstico |
| GET    | /v1/history       | Historial de escaneos del usuario  |
| GET    | /v1/health        | Estado del servidor y modelo       |

## Equipo

- Claudio Aro — Ingeniería en Informática Mención Ciencia de Datos
- Institución: Duoc UC — Sede Puerto Montt
- Asignatura: Taller Aplicado de Programación (TPY1101)
- Docente: José Ignacio Campos Arévalo

