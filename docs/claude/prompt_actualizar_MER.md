# Prompt — Actualizar MER (Modelo Entidad-Relación) MaduraApp

## Contexto

El MER original fue diseñado en la planificación con un modelo normalizado de 6 tablas.
El sistema real implementó una arquitectura **desnormalizada** con una sola tabla
principal en el backend y una tabla de cache local en Android.

---

## Esquema real implementado

### Base de datos Backend — PostgreSQL (producción) / SQLite (desarrollo)

#### Tabla: `scans` (única tabla del backend)
```sql
CREATE TABLE scans (
    scan_id       VARCHAR(36)   PRIMARY KEY,     -- UUID generado por Python
    user_token    VARCHAR(512)  NOT NULL,         -- token de autenticación del usuario
    fruit_type    VARCHAR(50)   NOT NULL,         -- 'aguacate_hass' | 'platano' | 'tomate_usda' | 'mango'
    maturity_label VARCHAR(20)  NOT NULL,         -- 'INMADURO' | 'OPTIMO' | 'SOBRE_MADURO'
    confidence    FLOAT         NOT NULL,         -- 0.0 a 1.0
    bbox          JSON          NOT NULL,         -- [x1, y1, x2, y2] coordenadas del bounding box
    recommendation VARCHAR(255) NOT NULL,         -- texto de recomendación al usuario
    color_code    VARCHAR(10)   NOT NULL,         -- 'green' | 'yellow' | 'red'
    created_at    DATETIME      NOT NULL          -- timestamp del escaneo
);

CREATE INDEX ix_scans_user_token ON scans (user_token);
```

**Nota:** Los datos de fruta, madurez y recomendación están desnormalizados — no existen
tablas separadas FRUTA, MADUREZ ni RECOMENDACION. Los valores se determinan en código
mediante CLASS_MAP y RECOMMENDATION_MAP en `inference_service.py`.

---

### Base de datos Android — Room/SQLite (cache local offline)

#### Tabla: `scan_cache`
```sql
CREATE TABLE scan_cache (
    id             INTEGER       PRIMARY KEY AUTOINCREMENT,
    fruit_type     TEXT          NOT NULL,
    maturity_label TEXT          NOT NULL,
    confidence     REAL          NOT NULL,
    bbox           TEXT          NOT NULL,   -- JSON serializado: "[x1,y1,x2,y2]"
    recommendation TEXT          NOT NULL,
    color_code     TEXT          NOT NULL,
    captured_at    INTEGER       NOT NULL    -- epoch milliseconds
);
```

---

## Diferencia con el MER original

El diseño original contemplaba estas 6 tablas (que NO se implementaron):

| Tabla original | Estado | Motivo |
|---|---|---|
| `USUARIO` | ❌ No implementada | Autenticación via token simple (MVP) |
| `ESCANEO` | ✅ → renombrada a `scans` | Implementada con campos desnormalizados |
| `FRUTA` | ❌ No implementada | Los datos de fruta van hardcodeados en CLASS_MAP |
| `MADUREZ` | ❌ No implementada | Embebido en `maturity_label` de la tabla scans |
| `RECOMENDACION` | ❌ No implementada | Embebido en `recommendation` de la tabla scans |
| `MODELO_IA` | ❌ No implementada | Versión fija en settings.py |

---

## Instrucciones para actualizar

1. Abre el MER original en tu herramienta (Draw.io, Lucidchart, ERDPlus, etc.)
2. **Elimina** las tablas: USUARIO, FRUTA, MADUREZ, RECOMENDACION, MODELO_IA
3. **Reemplaza** la tabla ESCANEO con la tabla `scans` con los campos reales
4. **Agrega** la tabla `scan_cache` (Android Room) como entidad separada, con una
   nota indicando que pertenece a la capa Android (no al servidor)
5. Elimina todas las relaciones entre tablas eliminadas
6. Agrega una nota en el diagrama: *"Diseño desnormalizado — valores de fruta
   y madurez determinados por CLASS_MAP en inference_service.py"*
7. Exporta como PNG y reemplaza `MaduraApp_MER.png`

---

## Diagrama textual de referencia

```
┌─────────────────────────────────────────────────────────┐
│                    BACKEND (PostgreSQL)                  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                     scans                        │   │
│  ├──────────────────────────────────────────────────┤   │
│  │ scan_id (PK)     VARCHAR(36)                     │   │
│  │ user_token       VARCHAR(512)  [INDEXED]         │   │
│  │ fruit_type       VARCHAR(50)                     │   │
│  │ maturity_label   VARCHAR(20)                     │   │
│  │ confidence       FLOAT                           │   │
│  │ bbox             JSON                            │   │
│  │ recommendation   VARCHAR(255)                    │   │
│  │ color_code       VARCHAR(10)                     │   │
│  │ created_at       DATETIME                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│               ANDROID (Room / SQLite local)             │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                  scan_cache                      │   │
│  ├──────────────────────────────────────────────────┤   │
│  │ id (PK)         INTEGER (autoincrement)          │   │
│  │ fruit_type      TEXT                             │   │
│  │ maturity_label  TEXT                             │   │
│  │ confidence      REAL                             │   │
│  │ bbox            TEXT (JSON serializado)          │   │
│  │ recommendation  TEXT                             │   │
│  │ color_code      TEXT                             │   │
│  │ captured_at     INTEGER (epoch ms)               │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

Nota: scan_cache es un espejo local de scans para uso offline.
      Los datos se sincronizan al llamar GET /v1/history.
```
