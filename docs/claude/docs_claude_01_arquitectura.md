# 01 — Arquitectura del Sistema

## Visión general

MaduraApp opera bajo una arquitectura **cliente-servidor distribuida**. El procesamiento pesado de visión artificial se delega al servidor en la nube, permitiendo que dispositivos Android de gama media accedan a inferencia compleja sin consumir batería ni memoria local.

```
┌─────────────────────────────────────────────────┐
│              CLIENTE (Android)                  │
│  Kotlin + CameraX + Retrofit + Room DB          │
│  Patrón: MVVM                                   │
│  - MainActivity                                 │
│  - ScanViewModel (LiveData)                     │
│  - FruitRepository                              │
│  - MaduraApiService (Retrofit)                  │
└──────────────────┬──────────────────────────────┘
                   │ HTTPS / REST / JSON
                   │ multipart/form-data (imagen)
                   ▼
┌─────────────────────────────────────────────────┐
│           BACKEND (FastAPI / Python)            │
│  Render o AWS App Runner (PaaS)                 │
│                                                 │
│  POST /v1/predict   ← recibe imagen             │
│  GET  /v1/history   ← historial usuario         │
│  GET  /v1/health    ← health check              │
│                                                 │
│  InferenceService → YOLO26Wrapper               │
│  HistoryService   → AsyncSession                │
└──────┬──────────────────────┬───────────────────┘
       │                      │
       ▼                      ▼
┌─────────────┐      ┌─────────────────┐
│  YOLO26n    │      │   PostgreSQL     │
│  (.pt file) │      │   (historial)   │
│  CPU-only   │      │                 │
└─────────────┘      └─────────────────┘
```

---

## Flujo de una petición completa

```
1. Usuario apunta cámara → CameraX captura frame
2. Android redimensiona imagen a 640×640 px (pre-procesamiento local)
3. Android envía POST /v1/predict con imagen (multipart/form-data) + token JWT
4. FastAPI valida token → InferenceService.validate_image()
5. InferenceService.preprocess() → ndarray normalizado
6. YOLO26Wrapper.predict() → Results (bbox, class_id, confidence)
7. InferenceService.postprocess() → ScanResult (pydantic)
8. HistoryService.save() → INSERT en PostgreSQL
9. FastAPI retorna JSON con ScanResult
10. Android parsea JSON → ScanViewModel actualiza LiveData
11. UI actualiza semáforo (verde/amarillo/rojo) + recomendación
```

**Tiempo objetivo:** ≤5 segundos extremo a extremo en red 4G.

---

## Modelo de datos — Diagrama ER simplificado

```
USUARIO (1) ──────────── (N) ESCANEO
                               │
                    ┌──────────┼──────────┐
                    │          │          │
                 FRUTA(1)  MADUREZ(1)  MODELO_IA(1)
                    │          │
                 (N)MADUREZ (N)RECOMENDACION
```

**Tablas:**

| Tabla | PK | FKs | Descripción |
|-------|----|-----|-------------|
| USUARIO | user_id (UUID) | — | Cuenta de usuario |
| ESCANEO | scan_id (UUID) | user_id, fruta_id, maturity_id | Registro de cada análisis |
| FRUTA | fruta_id (INT) | — | Catálogo: Aguacate, Plátano, Tomate, Mango |
| MADUREZ | maturity_id (INT) | fruta_id | Estados: INMADURO, OPTIMO, SOBRE_MADURO |
| RECOMENDACION | rec_id (INT) | maturity_id, fruta_id | Consejos de consumo/almacenamiento |
| MODELO_IA | model_id (INT) | — | Versiones del modelo deployado |

---

## Atributos de calidad (KPIs)

| Atributo | Métrica | Target |
|----------|---------|--------|
| Latencia E2E | t_captura + t_red + t_inferencia | ≤ 5 segundos |
| Latencia inferencia | YOLO26n en CPU | < 200ms |
| Precisión modelo | mAP@50 en validación | ≥ 75% |
| Concurrencia | Peticiones simultáneas sin degradar >20% | ≥ 5 req |
| Disponibilidad | Uptime durante evaluación | ≥ 95% |
| Seguridad | Cifrado en tránsito | TLS 1.2+ |

---

## Frutas soportadas (MVP)

| Fruta | Nombre científico | Indicador visual principal | Estados |
|-------|------------------|--------------------------|---------|
| Aguacate Hass | Persea americana | Color piel (verde → negro) + textura | INMADURO / OPTIMO / SOBRE_MADURO |
| Plátano | Musa sapientum | Índice de Color CI1–CI6 (verde → amarillo/marrón) | INMADURO / OPTIMO / SOBRE_MADURO |
| Tomate USDA | Solanum lycopersicum | Escala USDA 6 etapas (green → red) | INMADURO / PROXIMO / OPTIMO / MUY_MADURO |
| Mango | Mangifera indica | Morfología hombros + amarilleamiento pulpa | INMADURO / OPTIMO / SOBRE_MADURO |

---

## Seguridad

- **Transporte:** HTTPS obligatorio (TLS 1.2+). Certificados automáticos via Render/AWS.
- **Autenticación:** JWT tokens. Header: `Authorization: Bearer <token>`.
- **Validación:** Pydantic en cada endpoint. Tipos de imagen: jpeg, png, webp únicamente.
- **Imágenes:** Procesadas en memoria, no persistidas en disco del servidor.
- **Compliance:** Ley 20.393 (Chile), políticas de integridad Duoc UC.
- **Auditoría:** Logs de acceso en servidor para detectar uso no autorizado.

---

## Cloud — Estrategia de despliegue

**Seleccionado:** PaaS (Render o AWS App Runner)

| Criterio | IaaS (EC2) | PaaS (Render/App Runner) |
|----------|-----------|--------------------------|
| Control | Total | Limitado |
| Gestión | Manual | Automática |
| Costo | Variable | Free tier disponible |
| SSL | Manual | Automático |
| Escalado | Manual | Automático |
| **Ideal para** | Tráfico alto constante | **MVP académico** ✅ |

**Restricción técnica:** Usar modelo YOLO26n **Nano** exclusivamente para compatibilidad con free tier (CPU-only, <512MB RAM).
