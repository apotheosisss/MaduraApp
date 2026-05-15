# 03 — Decisiones técnicas, restricciones y contexto

## Decisiones técnicas clave

### IA: YOLO26n en lugar de YOLOv8
- **Razón:** YOLO26n (Ultralytics, enero 2026) es 43% más rápido en CPU que YOLOv11, sin NMS, sin DFL.
- **API:** Idéntica a versiones anteriores → `from ultralytics import YOLO`
- **Restricción:** Solo variante **Nano** por compatibilidad con free tier cloud (CPU, <512MB RAM).
- **El informe ERS menciona YOLOv8** — esto fue corregido durante la planificación. Usar YOLO26n en todo el código.

### Backend: FastAPI en lugar de Django/Flask
- Async nativo (vital para no bloquear mientras YOLO infiere)
- Validación automática con Pydantic
- Documentación Swagger auto-generada (`/docs`)
- Menor overhead para microservicio de inferencia

### Frontend: Android Nativo (Kotlin) en lugar de Flutter/React Native
- Acceso directo a CameraX (hardware de cámara con precisión milimétrica)
- Gestión de ciclo de vida con Lifecycle de Activity
- Corrutinas de Kotlin para async sin bloquear UI (evita ANR)

### BD: PostgreSQL (prod) + SQLite (dev)
- SQLite en desarrollo → sin necesidad de Docker para trabajar localmente
- PostgreSQL en producción → escalabilidad, JSONB para bbox
- Misma interfaz via SQLAlchemy async → cambio por variable de entorno (`DB_URL`)

### Cloud: PaaS (Render/AWS App Runner) en lugar de IaaS (EC2)
- Free tier disponible
- SSL automático
- Sin gestión de servidores → foco en código
- Suficiente para MVP académico con tráfico bajo

---

## Restricciones del proyecto

| Restricción | Detalle |
|-------------|---------|
| Tiempo | 16 semanas de desarrollo + 2 de presentación |
| Presupuesto | Cloud free tier únicamente |
| Modelo | Solo variante Nano (CPU, <512MB RAM) |
| Latencia total | ≤ 5 segundos E2E en red 4G |
| Latencia inferencia | < 200ms |
| Precisión | mAP@50 ≥ 75% en validación |
| Plataforma móvil | Solo Android 10+ (API 29+) |
| Conectividad | Requiere internet para inferencia (no offline) |
| Frutas soportadas | Solo 4 climatéricas en MVP |

---

## Supuestos

- Dataset balanceado disponible (≥200 imágenes por clase) en condiciones de supermercado.
- Google Colab con GPU para entrenamiento YOLO26n.
- Dispositivos de usuarios con cámara ≥8 megapíxeles y autoenfoque.
- Conexión 4G/5G disponible en puntos de venta.
- Disponibilidad cloud ≥95% durante fase de evaluación.

---

## Contexto académico

| Campo | Valor |
|-------|-------|
| Institución | Duoc UC |
| Sede | Puerto Montt |
| Carrera | Ingeniería en Informática Mención Ciencia de Datos |
| Asignatura | TPY1101 — Taller Aplicado de Programación |
| Sección | 001D |
| Docente | José Ignacio Campos Arévalo |
| Autor principal | Claudio Aro |
| Estándar ERS | IEEE 830-1998 |
| Normativa | Ley 20.393, Política General Seguridad Duoc UC |

### Hitos de evaluación
| Hito | Semana | Entregable |
|------|--------|-----------|
| Informe Evaluación 1 | S4 | ERS + Diagramas + Estructura repositorio |
| Informe Evaluación 2 | S9 | Backend funcional + Modelo v1 |
| Entrega Final MVP | S16 | App completa desplegada en cloud |

---

## Metodología de trabajo

### Scrum (desarrollo software)
- Sprints de 2 semanas
- Backlog priorizado por sprint
- Daily async (GitHub Issues / comentarios en PR)
- Retrospectiva al final de cada sprint

### CRISP-DM (modelo de IA)
| Fase | Actividad | Semanas |
|------|-----------|---------|
| Comprensión negocio | Definir clases, métricas de éxito | S1–S2 |
| Comprensión datos | Recolección y análisis de dataset | S2–S4 |
| Preparación datos | Etiquetado, augmentation, split 70/15/15 | S3–S5 |
| Modelado | Fine-tuning YOLO26n, ajuste hiperparámetros | S5–S7 |
| Evaluación | mAP@50, confusion matrix, casos de fallo | S8–S9 |
| Despliegue | Integración con FastAPI, carga al servidor | S10 |

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Dataset insuficiente | Media | Alto | Roboflow Universe + data augmentation |
| Latencia >5s en cloud free | Media | Alto | YOLO26n Nano + caché de modelo en lifespan |
| Variabilidad iluminación en frutas | Alta | Medio | Augmentation: brillo, contraste, rotación |
| GPU no disponible en Colab | Baja | Medio | Kaggle Notebooks como alternativa |
| Rotación de equipo | Baja | Alto | Documentación exhaustiva, PRs descriptivos |

---

## Convenciones de código

### Commits (Conventional Commits)
```
feat:     nueva funcionalidad
fix:      corrección de bug
docs:     documentación
test:     tests
refactor: refactorización sin cambio funcional
ci:       cambios en CI/CD
chore:    tareas de mantenimiento
```

### Python
- Type hints obligatorios en todas las funciones
- Docstrings en servicios y wrappers
- `async/await` en todo el backend (sin funciones bloqueantes)
- Variables de entorno siempre via `settings` de `core/config.py`
- Nunca hardcodear credenciales, paths absolutos ni IPs

### Git
- Nunca hacer push directo a `main`
- PRs a `develop` primero, luego merge a `main`
- Pesos del modelo (`.pt`, `.onnx`) **nunca** versionados en Git
- Archivos `.env` **nunca** versionados (solo `.env.example`)

---

## Dataset — Referencias para entrenamiento

Datasets públicos recomendados para fine-tuning:

| Fuente | Contenido | URL |
|--------|-----------|-----|
| Roboflow Universe | Banana + Mango ripeness | https://universe.roboflow.com |
| Kaggle | Fruit ripeness classification | https://www.kaggle.com/datasets/asadullahprl/fruits-ripeness-classification-dataset |
| MDPI papers | Avocado, Tomato datasets | Referencias en ERS secciones 4.1–4.3 |

**Split recomendado:** 70% train / 15% validation / 15% test  
**Mínimo por clase:** 200 imágenes  
**Formato:** YOLO format (`.txt` con coordenadas normalizadas)  
**Augmentation:** rotación ±15°, brillo ±30%, flip horizontal, escala 0.8–1.2×
