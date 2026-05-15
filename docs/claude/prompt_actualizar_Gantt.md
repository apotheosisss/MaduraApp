# Prompt — Actualizar Gantt MaduraApp

## Contexto

El Gantt original cubre 16 semanas del proyecto MaduraApp. Necesitas actualizarlo
para reflejar el estado real: **Sprints 1 y 2 completados**, entrenamiento en progreso.

---

## Estado real a mayo 2026

| Semanas | Fase | Estado |
|---|---|---|
| 1–4 | Comprensión de negocio y datos | ✅ Completado |
| 5–8 | Modelado + Desarrollo Backend | ✅ Completado |
| 9–12 | Desarrollo Frontend y Conectividad | ✅ Completado |
| 13–16 | Pruebas, Ajuste y Despliegue Cloud | 🔄 En progreso |

---

## Tareas completadas por fase (para agregar al Gantt si tiene ese nivel de detalle)

### Semanas 1–4 ✅
- Definición de 12 clases (4 frutas × 3 estados)
- Recolección de dataset: 31.940 imágenes (Kaggle + Mendeley)
- ERS, diagramas UML, MER, WireFrame

### Semanas 5–8 ✅ (Sprint 1 — Backend)
- FastAPI + SQLAlchemy async + Alembic
- inference_service.py con CLASS_MAP/COLOR_MAP/RECOMMENDATION_MAP
- history_service.py (CRUD)
- 9 tests reales (pytest + SQLite in-memory)
- CI/CD con GitHub Actions

### Semanas 9–12 ✅ (Sprint 2 — Android)
- App Android Kotlin + CameraX + Retrofit
- MVVM: ScanViewModel + HistoryViewModel
- Cache offline Room (ScanCacheEntity + ScanDao)
- HistoryActivity con RecyclerView + pull-to-refresh
- 20 tests JVM (MockK + Turbine + coroutines-test)

### Semanas 13–16 🔄 (En progreso)
- Entrenamiento YOLO26n en Kaggle (GPU T4 x2, 80 épocas)
- Validación mAP@50 ≥ 0.75 — **pendiente resultado**
- Deploy en Render / AWS App Runner — **pendiente**
- Pruebas E2E Android ↔ backend — **pendiente**

---

## Instrucciones para actualizar

1. Abre el archivo original del Gantt (Excel / Google Sheets / Project)
2. Marca las barras de las semanas 1–12 con color **verde** o estado "Completado"
3. Marca la semana 13–16 con color **amarillo** o estado "En progreso"
4. Si el Gantt tiene hitos, agrega:
   - **Hito Sprint 1 completado** → Semana 8
   - **Hito Sprint 2 completado** → Semana 12
   - **Hito Entrenamiento iniciado** → Semana 13
5. Exporta como PNG y reemplaza `Gantt_MaduraApp.png`
