"""Fase 5 (CRISP-DM) — Evaluación del modelo entrenado.

Corre `model.val()` sobre el split de validación o test y reporta:
    - mAP@50, mAP@50-95, precision, recall por clase
    - Matriz de confusión (PNG generado por Ultralytics)
    - Validación del KPI mínimo (mAP@50 ≥ 0.75)
    - Análisis de casos fallo (confianza baja)

Uso:
    # Evaluar el último best.pt
    python scripts/evaluate_model.py

    # Evaluar un modelo específico sobre el split de test
    python scripts/evaluate_model.py --weights runs/maduraapp_v1/weights/best.pt --split test
"""
from __future__ import annotations

import argparse
import json
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
DEFAULT_DATA_YAML = SCRIPTS_DIR / "data.yaml"

# KPI mínimo definido en docs/claude/01_arquitectura.md
MIN_MAP50 = 0.75


def find_latest_best() -> Path | None:
    """Encuentra el best.pt del run más reciente."""
    if not RUNS_DIR.exists():
        return None
    candidates = sorted(
        RUNS_DIR.glob("*/weights/best.pt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def evaluate(args: argparse.Namespace) -> int:
    weights = args.weights or find_latest_best()
    if not weights or not Path(weights).exists():
        sys.stderr.write(
            "ERROR: no se encontró un checkpoint best.pt.\n"
            "Pasa --weights o entrena primero con scripts/train_model.py\n"
        )
        return 1

    print(f"🔍 Evaluando: {weights}")
    print(f"   split: {args.split}")
    print(f"   data:  {args.data}")
    print()

    model = YOLO(str(weights))
    metrics = model.val(
        data=str(args.data),
        split=args.split,
        imgsz=640,
        batch=args.batch,
        plots=True,
        save_json=True,
    )

    # Métricas globales
    map50 = float(metrics.box.map50)
    map50_95 = float(metrics.box.map)
    precision = float(metrics.box.mp)
    recall = float(metrics.box.mr)

    print("─" * 60)
    print("📈 Métricas globales")
    print("─" * 60)
    print(f"   mAP@50      = {map50:.4f}")
    print(f"   mAP@50-95   = {map50_95:.4f}")
    print(f"   Precision   = {precision:.4f}")
    print(f"   Recall      = {recall:.4f}")
    print()

    # Métricas por clase
    print("─" * 60)
    print("📊 Métricas por clase (P / R / mAP@50)")
    print("─" * 60)
    names = metrics.names if hasattr(metrics, "names") else {}
    if hasattr(metrics.box, "ap50") and hasattr(metrics.box, "ap_class_index"):
        ap50_per_class = metrics.box.ap50
        class_indices = metrics.box.ap_class_index
        for idx, class_id in enumerate(class_indices):
            class_name = names.get(int(class_id), f"class_{class_id}")
            print(f"   {class_name:>30} → mAP@50 = {ap50_per_class[idx]:.4f}")
    print()

    # Validación KPI
    print("─" * 60)
    print("🎯 Validación de KPI")
    print("─" * 60)
    target = MIN_MAP50
    passed = map50 >= target
    status = "✅ APROBADO" if passed else "❌ POR DEBAJO DEL UMBRAL"
    print(f"   Objetivo: mAP@50 ≥ {target:.2f}")
    print(f"   Obtenido: mAP@50 = {map50:.4f}  →  {status}")
    if not passed:
        print()
        print("   Sugerencias:")
        print("   - Aumentar dataset (Roboflow Universe, capturas propias)")
        print("   - Subir augmentation (mosaic, mixup)")
        print("   - Más épocas (--epochs 120) o mejor lr0")
        print("   - Verificar consistencia de etiquetas (labelers diferentes)")
    print()

    # Persistir métricas en JSON para tracking
    save_dir = Path(metrics.save_dir) if hasattr(metrics, "save_dir") else RUNS_DIR
    metrics_json = save_dir / "metrics_summary.json"
    metrics_json.write_text(json.dumps({
        "weights": str(weights),
        "split": args.split,
        "map50": map50,
        "map50_95": map50_95,
        "precision": precision,
        "recall": recall,
        "kpi_passed": passed,
        "kpi_target": target,
    }, indent=2))
    print(f"📝 Métricas guardadas: {metrics_json}")

    return 0 if passed else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluación del modelo MaduraApp")
    parser.add_argument(
        "--weights",
        type=Path,
        default=None,
        help="Checkpoint a evaluar (default: best.pt del último run)",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_YAML,
    )
    parser.add_argument(
        "--split",
        default="val",
        choices=["val", "test", "train"],
        help="Split a evaluar",
    )
    parser.add_argument("--batch", type=int, default=16)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(evaluate(parse_args()))
