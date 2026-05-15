# Prompt para Gemini — Actualizar ERS MaduraApp

## Instrucciones generales

Eres un asistente técnico académico. Tu tarea es **actualizar** la Especificación de
Requisitos de Software (ERS) del proyecto MaduraApp, corrigiendo inconsistencias entre
lo que el documento dice y lo que el equipo realmente implementó.

**Reglas estrictas:**
- Mantén el estilo académico, la estructura IEEE 830-1998 y el tono formal del documento.
- **No añadas** secciones nuevas ni cambies la numeración.
- **No elimines** párrafos completos, solo actualiza los valores incorrectos.
- Mantén todas las citas bibliográficas tal como están (números superíndices como ³).
- El idioma es **español**.

---

## Contexto del proyecto (estado real a mayo 2026)

MaduraApp es un sistema de análisis de madurez agrícola que usa visión computacional.
El equipo completó los Sprints 1 y 2, con estos componentes implementados:

| Capa | Tecnología implementada |
|---|---|
| App Android | Kotlin + CameraX + Retrofit + Room (cache offline historial) |
| Backend | Python 3.12 + FastAPI 0.135 + SQLAlchemy async + Alembic |
| Modelo IA | **YOLO26n** (Ultralytics, enero 2026) — variante Nano |
| Base de datos prod | **PostgreSQL 16** |
| Base de datos dev | **SQLite + aiosqlite** |
| Cache offline | **Room** en Android (historial disponible sin internet) |
| Cloud | **Render** (PaaS, free tier) o AWS App Runner |
| Dataset | 31.940 imágenes — Kaggle + Mendeley (no Roboflow) |

---

## Cambios específicos que debes aplicar

### 1. Reemplazar TODAS las menciones de "YOLOv8" por "YOLO26n"

El documento menciona YOLOv8 en múltiples lugares. El modelo real es **YOLO26n**
(Ultralytics, enero 2026), que es más rápido en CPU que YOLOv11, sin NMS, sin DFL.
La variante usada es **Nano** (igual que indicaba el documento).

Secciones afectadas y texto a cambiar:

**Sección 1.2 — Tabla de componentes:**
- ANTES: `"Núcleo de IA: Modelo de visión artificial basado en la arquitectura YOLOv8 (You Only Look Once), optimizado para la detección de objetos y clasificación multiclase de estados de madurez."`
- DESPUÉS: `"Núcleo de IA: Modelo de visión artificial basado en la arquitectura YOLO26n (You Only Look Once, versión enero 2026, Ultralytics), optimizado para la detección de objetos y clasificación multiclase de estados de madurez. Se utiliza la variante Nano para compatibilidad con infraestructura cloud de nivel gratuito (CPU, <512MB RAM)."`

**Sección 1.3 — Definiciones:**
- ANTES: `"YOLOv8: Modelo de red neuronal convolucional diseñado para la detección rápida y precisa de objetos en imágenes."`
- DESPUÉS: `"YOLO26n: Modelo de red neuronal convolucional de la familia YOLO (You Only Look Once, versión enero 2026, Ultralytics), diseñado para la detección rápida y precisa de objetos en imágenes. Es un 43% más veloz en CPU que versiones anteriores, sin Non-Maximum Suppression (NMS) ni Distribution Focal Loss (DFL)."`

**Sección 2.4 — Restricciones de diseño:**
- ANTES: `"El modelo YOLOv8 debe ser de arquitectura 'Nano' o 'Small'"`
- DESPUÉS: `"El modelo YOLO26n debe ser de variante 'Nano'"`

**Sección 3.2 — RF01:**
- ANTES: `"las redimensionará automáticamente a 640x640 píxeles para ser compatibles con YOLOv8"`
- DESPUÉS: `"las redimensionará automáticamente a 640x640 píxeles para ser compatibles con YOLO26n"`

**Sección 5.2 — Backend:**
- ANTES: `"El backend carga el modelo YOLOv8 utilizando la librería ultralytics."`
- DESPUÉS: `"El backend carga el modelo YOLO26n utilizando la librería Ultralytics, implementando una importación diferida (lazy import) para evitar que el módulo bloquee el inicio del servidor cuando los pesos no están disponibles."`

**Sección 7.2 — Cronograma:**
- ANTES: `"Modelo YOLOv8 entrenado (v1) y API REST funcional en Python."`
- DESPUÉS: `"Modelo YOLO26n entrenado (v1) y API REST funcional en Python."`

---

### 2. Corregir la base de datos

**Sección 2.1 — Perspectiva del Producto (Motores de Almacenamiento):**
- ANTES: `"Conexión con bases de datos relacionales (Oracle SQL o PostgreSQL)"`
- DESPUÉS: `"Conexión con bases de datos relacionales (PostgreSQL 16 en producción; SQLite con aiosqlite en desarrollo local). El ORM utilizado es SQLAlchemy async con Alembic para gestión de migraciones."`

**Sección 3.1.2 — Interfaz de Software:**
- ANTES: `"GET /v1/history: Recupera el historial de escaneos del usuario almacenado en Oracle SQL."`
- DESPUÉS: `"GET /v1/history: Recupera el historial de escaneos del usuario almacenado en PostgreSQL (producción) o SQLite (desarrollo), con soporte de paginación (parámetros limit y offset)."`

---

### 3. Actualizar la restricción de modo offline

La app implementa **cache offline con Room** para el historial, aunque la inferencia
sigue requiriendo conexión.

**Sección 1.2 — Lo que el sistema no hará:**
- ANTES: `"Funcionamiento en modo offline sin conexión a internet."`
- DESPUÉS: `"Ejecución de inferencia de visión artificial en modo offline. El historial de escaneos previos puede consultarse sin conexión gracias al cache local implementado con Room (SQLite embebido en Android)."`

**Sección 2.4 — Restricciones (Conectividad):**
- ANTES: `"El sistema no operará en modo offline en su versión inicial, requiriendo obligatoriamente una conexión de datos activa para el procesamiento de inferencia en la nube."`
- DESPUÉS: `"El sistema requiere conexión de datos activa para la inferencia de visión artificial en la nube. El historial de diagnósticos previos está disponible offline mediante un cache local implementado con la librería Room en Android."`

---

### 4. Actualizar la decisión de arquitectura cloud

**Sección 5.3 — Estrategia Cloud:**
- ANTES: `"Decisión Arquitectónica: Se utilizará AWS SageMaker o ECS Fargate para el despliegue del microservicio de IA"`
- DESPUÉS: `"Decisión Arquitectónica: Para el MVP académico se utilizará un servicio PaaS de nivel gratuito (Render o AWS App Runner), que gestiona el despliegue automático del contenedor Docker sin administración de servidores. Esta elección prioriza la velocidad de despliegue y el costo cero sobre el control de bajo nivel, adecuado para el nivel de tráfico esperado durante la evaluación. La migración a AWS ECS o SageMaker se contempla para fases de escalado post-MVP."`

---

### 5. Actualizar el estado del cronograma (Sección 7.2)

Actualiza la tabla de fases para reflejar que los Sprints 1 y 2 están completados:

| Semanas | Fase | Entregables Clave | Estado |
|---|---|---|---|
| 1-4 | Comprensión de Negocio y Datos | Dataset etiquetado (31.940 imgs, 4 frutas climatéricas, Kaggle + Mendeley) | ✅ Completado |
| 5-8 | Modelado y Desarrollo Backend | Modelo YOLO26n en entrenamiento; API REST funcional en Python con FastAPI, SQLAlchemy, Alembic y 9 tests reales. | ✅ Completado |
| 9-12 | Desarrollo Frontend y Conectividad | App Android con CameraX, MVVM, historial con Room, 20 tests JVM. | ✅ Completado |
| 13-16 | Pruebas, Ajuste y Despliegue Cloud | Validación mAP@50 ≥ 0.75; despliegue en Render/AWS App Runner. | 🔄 En progreso |

---

### 6. Actualizar las fuentes del dataset (Sección 2.5 Suposiciones)

**Sección 2.5:**
- ANTES: `"La precisión del modelo depende de la disponibilidad de un dataset de entrenamiento balanceado de al menos 200 imágenes por clase bajo condiciones de iluminación de supermercado."`
- DESPUÉS: `"La precisión del modelo depende de la calidad del dataset de entrenamiento. El dataset utilizado cuenta con 31.940 imágenes distribuidas en 12 clases (4 frutas × 3 estados de madurez), recopiladas desde fuentes públicas: Kaggle (plátano, tomate, mango) y Mendeley (aguacate Hass, 14.710 imágenes con etiquetas de 5 etapas de madurez). El split es 70% entrenamiento / 15% validación / 15% test."`

---

## Lo que NO debes cambiar

- La introducción y motivación del problema (desperdicio alimentario)
- Las secciones de análisis biológico de frutas (4.1 a 4.4)
- Las consideraciones éticas (sección 8)
- Las conclusiones (sección 9) — excepto si mencionan YOLOv8 explícitamente
- El análisis de Ishikawa (sección 6)
- Las citas bibliográficas y sus números
- El estándar IEEE 830-1998 como base
- Las restricciones de plataforma (solo Android), lenguajes (Kotlin, Python) y KPIs (≤5s, mAP ≥75%)

---

## Formato de entrega esperado

Entrega el documento ERS completo actualizado en formato de texto corrido, manteniendo
la estructura de secciones numeradas (1. Introducción, 2. Descripción General, etc.)
y las tablas en formato de texto o markdown.
