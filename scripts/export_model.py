"""Fase 6 (CRISP-DM) — Despliegue: copia el best.pt a backend/weights/.

El backend espera el modelo en `backend/weights/yolo26n_maduraapp.pt` (path
configurado en `backend/app/core/config.py`). Este script automatiza el copiado
y opcionalmente exporta a otros formatos (ONNX, TorchScript) para entornos sin
PyTorch.

Uso:
    python scripts/export_model.py
    python scripts/export_model.py --weights runs/maduraapp_v3/weights/best.pt
    python scripts/export_model.py --format onnx
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    sys.stderr.write(
        "Faltan dependencias. Instala con:\n"
        "    pip install -r scripts/requirements.txt\n"
    )
    sys.exit(1)

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
RUNS_DIR = PROJECT_ROOT / "runs"
BACKEND_WEIGHTS = PROJECT_ROOT / "backend" / "weights"
TARGET_PT = BACKEND_WEIGHTS / "yolo26n_maduraapp.pt"


def find_latest_best() -> Path | None:
    if not RUNS_DIR.exists():
        return None
    candidates = sorted(
        RUNS_DIR.glob("*/weights/best.pt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def export(args: argparse.Namespace) -> int:
    weights = args.weights or find_latest_best()
    if not weights or not Path(weights).exists():
        sys.stderr.write(
            "ERROR: no se encontró un best.pt.\n"
            "Pasa --weights o entrena primero con scripts/train_model.py\n"
        )
        return 1

    weights = Path(weights)
    BACKEND_WEIGHTS.mkdir(parents=True, exist_ok=True)

    # Backup del modelo anterior si existe
    if TARGET_PT.exists():
        backup = TARGET_PT.with_suffix(".pt.bak")
        shutil.copy2(TARGET_PT, backup)
        print(f"💾 Backup del modelo anterior: {backup.relative_to(PROJECT_ROOT)}")

    print(f"📦 Copiando {weights.relative_to(PROJECT_ROOT)}")
    print(f"   →    {TARGET_PT.relative_to(PROJECT_ROOT)}")
    shutil.copy2(weights, TARGET_PT)
    print(f"✅ Modelo desplegado en backend ({TARGET_PT.stat().st_size / 1024 / 1024:.2f} MB)")

    # Export adicional a otros formatos
    if args.format and args.format != "pt":
        print()
        print(f"🔄 Exportando a formato '{args.format}'...")
        model = YOLO(str(weights))
        exported_path = model.export(format=args.format)
        if exported_path:
            print(f"✅ Export {args.format} disponible en: {exported_path}")

    print()
    print("Siguiente paso (en un host con el backend):")
    print("   docker compose up --build")
    print("   curl http://localhost:8000/v1/health")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Despliega el modelo entrenado al backend"
    )
    parser.add_argument(
        "--weights",
        type=Path,
        default=None,
        help="Checkpoint a desplegar (default: best.pt del último run)",
    )
    parser.add_argument(
        "--format",
        default="pt",
        choices=["pt", "onnx", "torchscript"],
        help="Formato de export adicional (pt = solo copia .pt)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(export(parse_args()))
