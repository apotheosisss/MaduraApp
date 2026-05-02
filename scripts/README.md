# MaduraApp — Pipeline de entrenamiento (CRISP-DM)

Pipeline completo de fine-tuning de YOLO26n para detección y clasificación de
madurez en 4 frutas climatéricas (12 clases totales). Sigue las 6 fases de
CRISP-DM.

## Frutas y estados

| Fruta | INMADURO | OPTIMO | SOBRE_MADURO |
|---|---|---|---|
| Aguacate Hass | 0 | 1 | 2 |
| Plátano       | 3 | 4 | 5 |
| Tomate USDA   | 6 | 7 | 8 |
| Mango         | 9 | 10 | 11 |

> ⚠️ **Importante:** este orden de class_id es el contrato con el backend
> (`backend/app/services/inference_service.py::CLASS_MAP`). Cualquier cambio
> requiere actualizar ambos lados a la vez.

---

## KPIs objetivo

| Métrica | Target | Justificación |
|---|---|---|
| mAP@50 (val) | ≥ 0.75 | Hito de aprobación del modelo (`docs/claude/01_arquitectura.md`) |
| Latencia inferencia | < 200 ms (CPU) | Restricción del free-tier cloud |
| Tamaño .pt | < 30 MB | YOLO26n Nano cabe holgado en RAM <512MB |

---

## Setup local (con GPU)

```bash
# Desde la raíz del proyecto
python -m venv .venv-train
source .venv-train/bin/activate          # Linux/Mac
.venv-train\Scripts\activate              # Windows

pip install -r scripts/requirements.txt
```

Crea `.env` en la raíz:
```
ROBOFLOW_API_KEY=tu_api_key_aquí
ROBOFLOW_WORKSPACE=maduraapp-duoc
ROBOFLOW_PROJECT=maduraapp-ripeness
ROBOFLOW_VERSION=1
```

---

## Flujo CRISP-DM

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ 1. Comprensión      │ →   │ 2. Comprensión      │ →   │ 3. Preparación      │
│    del negocio      │     │    de los datos     │     │    de los datos     │
│                     │     │                     │     │                     │
│ data.yaml           │     │ download_dataset.py │     │ Augmentation        │
│ (12 clases)         │     │ + audit en train.py │     │ (en config.yaml)    │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                                                                   │
                                                                   ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ 6. Despliegue       │ ←   │ 5. Evaluación       │ ←   │ 4. Modelado         │
│                     │     │                     │     │                     │
│ export_model.py     │     │ evaluate_model.py   │     │ train_model.py      │
│ → backend/weights/  │     │ → mAP, KPI check    │     │ → best.pt           │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

### Fase 2-3 — Datos

```bash
python scripts/download_dataset.py
# Descarga el dataset desde Roboflow → datasets/maduraapp/
# Verifica que existan train/, valid/, test/ con images/ + labels/
```

### Fase 4 — Modelado

```bash
# Entrenamiento estándar (80 épocas, batch 16, GPU 0)
python scripts/train_model.py

# Override de hiperparámetros
python scripts/train_model.py --epochs 120 --batch 32 --device 0

# CPU-only (lento, solo para smoke test)
python scripts/train_model.py --epochs 5 --device cpu
```

Output: `runs/maduraapp_v1/weights/best.pt` + `last.pt` + `results.png` +
`confusion_matrix.png` + `*_hparams.yaml` (snapshot de hiperparámetros).

### Fase 5 — Evaluación

```bash
# Evaluar el último best.pt sobre el split de validación
python scripts/evaluate_model.py

# Evaluar sobre el split de test (opcional, solo una vez al final)
python scripts/evaluate_model.py --split test

# Evaluar un checkpoint específico
python scripts/evaluate_model.py --weights runs/maduraapp_v3/weights/best.pt
```

Output: tabla con `mAP@50`, `mAP@50-95`, P/R por clase + matriz de confusión
guardada como PNG. Exit code `0` si pasa el KPI, `2` si está debajo.

### Fase 6 — Despliegue

```bash
# Copia best.pt → backend/weights/yolo26n_maduraapp.pt
python scripts/export_model.py

# Export adicional a ONNX (opcional, para entornos sin PyTorch)
python scripts/export_model.py --format onnx
```

El script hace backup del modelo anterior como `.pt.bak`.

---

## Entrenamiento en Google Colab

Si no tienes GPU local, usa el notebook
[`notebooks/train_yolo26n_colab.ipynb`](../notebooks/train_yolo26n_colab.ipynb).

1. Abrir el notebook en Colab (`File → Open from GitHub`)
2. `Runtime → Change runtime type → GPU (T4)`
3. Ejecutar celdas en orden — al final descarga `best.pt` automáticamente.
4. En tu PC: copiar el `.pt` a `runs/maduraapp_v1/weights/best.pt` y correr
   `python scripts/export_model.py`

---

## Tuning sugerido si mAP@50 < 0.75

| Síntoma | Acción |
|---|---|
| Loss explota / NaN | Bajar `lr0` a 0.0005 |
| mAP plateauiza < 0.6 | `--epochs 120` + `mosaic: 1.0` + `mixup: 0.15` |
| Confusión INMADURO ↔ OPTIMO en bananas | Más imágenes con CI3-CI4 (transición) |
| Confianza promedio baja | Verificar consistencia de etiquetas (mismo labeler) |
| Recall bajo en mango | Aumentar `degrees` y `scale` (variabilidad de pose) |

---

## Estructura de archivos generados

```
MaduraApp/
├── datasets/maduraapp/         ← descargado por download_dataset.py (gitignore)
│   ├── train/{images,labels}/
│   ├── valid/{images,labels}/
│   └── test/{images,labels}/
├── runs/                        ← experimentos (gitignore)
│   ├── maduraapp_v1/
│   │   ├── weights/{best.pt,last.pt}
│   │   ├── results.png
│   │   ├── confusion_matrix.png
│   │   └── metrics_summary.json
│   ├── maduraapp_v2/
│   └── ...
└── backend/weights/
    ├── yolo26n_maduraapp.pt    ← producido por export_model.py
    └── yolo26n_maduraapp.pt.bak (backup automático)
```
