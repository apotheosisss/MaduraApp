"""Fine-tuning de YOLO26n para MaduraApp — Pipeline CRISP-DM.

Fases implementadas:
    1. Comprensión del negocio    → CLASS_MAP definido en data.yaml
    2. Comprensión de los datos   → estadísticas del dataset (audit)
    3. Preparación de los datos   → scripts/download_dataset.py + data.yaml
    4. Modelado                   → este script
    5. Evaluación                 → scripts/evaluate_model.py
    6. Despliegue                 → scripts/export_model.py

Uso:
    # Entrenamiento estándar con config.yaml por defecto
    python scripts/train_model.py

    # Override de hiperparámetros vía CLI
    python scripts/train_model.py --epochs 120 --batch 32 --device 0

    # Resumir desde un checkpoint
    python scripts/train_model.py --resume runs/maduraapp_v1/weights/last.pt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    from ultralytics import YOLO
except ImportError:
    sys.stderr.write(
        "Faltan dependencias. Instala con:\n"
        "    pip install -r scripts/requirements.txt\n"
    )
    sys.exit(1)

# ---------------------------------------------------------------------- Paths
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
DATASETS_DIR = PROJECT_ROOT / "datasets" / "maduraapp"
RUNS_DIR = PROJECT_ROOT / "runs"
DEFAULT_DATA_YAML = SCRIPTS_DIR / "data.yaml"
DEFAULT_CONFIG_YAML = SCRIPTS_DIR / "config.yaml"


# ──────────────────────────────────────────────────────────── 2. Data Audit

def audit_dataset(data_yaml_path: Path) -> None:
    """Imprime un sanity-check del dataset antes de entrenar."""
    if not DATASETS_DIR.exists():
        sys.stderr.write(
            f"ERROR: dataset no encontrado en {DATASETS_DIR}.\n"
            "Corre primero: python scripts/download_dataset.py\n"
        )
        sys.exit(1)

    with data_yaml_path.open() as fh:
        data_cfg = yaml.safe_load(fh)

    classes = data_cfg.get("names", {})
    print("─" * 60)
    print("📊 Auditoría del dataset")
    print("─" * 60)
    print(f"Clases declaradas: {len(classes)}")
    for class_id, name in classes.items():
        print(f"   {class_id:>2} → {name}")
    print()

    for split in ("train", "valid", "test"):
        images_dir = DATASETS_DIR / split / "images"
        labels_dir = DATASETS_DIR / split / "labels"
        if images_dir.exists():
            n_imgs = len(list(images_dir.glob("*")))
            n_lbls = len(list(labels_dir.glob("*"))) if labels_dir.exists() else 0
            ratio = "✅" if n_imgs == n_lbls else "⚠️"
            print(f"   {split:5}  {n_imgs:>5} imgs  /  {n_lbls:>5} labels  {ratio}")
        else:
            print(f"   {split:5}  (no encontrado)")
    print("─" * 60)


# ──────────────────────────────────────────────────────────── 4. Modelado

def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open() as fh:
        return yaml.safe_load(fh)


def build_train_kwargs(
    config: dict[str, Any],
    data_yaml: Path,
    overrides: argparse.Namespace,
) -> dict[str, Any]:
    """Mezcla config.yaml con overrides de CLI."""
    model_cfg = config.get("model", {})
    train_cfg = config.get("training", {})
    aug_cfg = config.get("augmentation", {})
    rep_cfg = config.get("reporting", {})

    return {
        "data": str(data_yaml),
        "epochs": overrides.epochs or train_cfg.get("epochs", 80),
        "batch": overrides.batch or train_cfg.get("batch", 16),
        "imgsz": model_cfg.get("imgsz", 640),
        "device": overrides.device if overrides.device is not None else model_cfg.get("device", 0),
        "patience": train_cfg.get("patience", 15),
        "optimizer": train_cfg.get("optimizer", "AdamW"),
        "lr0": train_cfg.get("lr0", 0.001),
        "lrf": train_cfg.get("lrf", 0.01),
        "momentum": train_cfg.get("momentum", 0.937),
        "weight_decay": train_cfg.get("weight_decay", 0.0005),
        "warmup_epochs": train_cfg.get("warmup_epochs", 3.0),
        "cos_lr": train_cfg.get("cos_lr", True),
        "amp": train_cfg.get("amp", True),
        # Augmentation
        "hsv_h": aug_cfg.get("hsv_h", 0.015),
        "hsv_s": aug_cfg.get("hsv_s", 0.7),
        "hsv_v": aug_cfg.get("hsv_v", 0.4),
        "degrees": aug_cfg.get("degrees", 15.0),
        "translate": aug_cfg.get("translate", 0.1),
        "scale": aug_cfg.get("scale", 0.5),
        "shear": aug_cfg.get("shear", 0.0),
        "perspective": aug_cfg.get("perspective", 0.0),
        "flipud": aug_cfg.get("flipud", 0.0),
        "fliplr": aug_cfg.get("fliplr", 0.5),
        "mosaic": aug_cfg.get("mosaic", 1.0),
        "mixup": aug_cfg.get("mixup", 0.1),
        "copy_paste": aug_cfg.get("copy_paste", 0.0),
        # Reporting
        "project": str(RUNS_DIR),
        "name": rep_cfg.get("name", "maduraapp_v1"),
        "save_period": rep_cfg.get("save_period", 10),
        "plots": rep_cfg.get("plots", True),
        "exist_ok": False,  # incrementa nombre del run en cada corrida
    }


def train(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    data_yaml = Path(args.data)

    print("🌱 MaduraApp — Fine-tuning YOLO26n")
    audit_dataset(data_yaml)

    base_model = args.resume or config.get("model", {}).get("base", "yolo26n.pt")
    print(f"🧠 Modelo base: {base_model}")
    print()

    model = YOLO(str(base_model))
    train_kwargs = build_train_kwargs(config, data_yaml, args)

    # Persistir el snapshot exacto de hiperparámetros usados para reproducibilidad
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = RUNS_DIR / f"{train_kwargs['name']}_hparams.yaml"
    with snapshot.open("w") as fh:
        yaml.safe_dump(train_kwargs, fh, sort_keys=False)
    print(f"📝 Hiperparámetros guardados: {snapshot.relative_to(PROJECT_ROOT)}")
    print()

    results = model.train(**train_kwargs)

    # Resumen final
    print()
    print("─" * 60)
    print("✅ Entrenamiento completado")
    print("─" * 60)
    save_dir = Path(results.save_dir) if hasattr(results, "save_dir") else None
    if save_dir:
        print(f"📁 Resultados en: {save_dir}")
        print("   - best.pt   → mejor checkpoint según val/mAP@50")
        print("   - last.pt   → último checkpoint")
        print("   - results.png, confusion_matrix.png")
    print()
    print("Siguiente paso:")
    print("   python scripts/evaluate_model.py")
    print("   python scripts/export_model.py")
    return 0


# ────────────────────────────────────────────────────────────── CLI

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tuning YOLO26n MaduraApp")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_YAML,
        help="Ruta a config.yaml con hiperparámetros",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_YAML,
        help="Ruta a data.yaml del dataset",
    )
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch", type=int, default=None)
    parser.add_argument(
        "--device",
        default=None,
        help="GPU id (0,1,...), 'cpu' o '-1' para autodetect",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="Checkpoint .pt desde el cual reanudar",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(train(parse_args()))
