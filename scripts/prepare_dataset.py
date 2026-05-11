"""Normaliza datasets crudos (Kaggle / Roboflow / capturas propias) al formato
YOLO contractual de MaduraApp.

Pipeline:
  1. Lee `prepare_config.yaml` con el mapeo `directorio_crudo → class_id`.
  2. Inspecciona cada source: cuenta imágenes válidas, ignora basura.
  3. Genera bboxes:
       - `full_frame`: una caja que cubre toda la imagen (clasificación →
         detección barata, útil cuando la fruta llena el frame).
       - `passthrough`: copia los `.txt` ya existentes (datasets que YA son
         de detección, como Laboro Tomato).
  4. Split estratificado por clase (cada clase aparece en train/valid/test).
  5. Copia a `datasets/maduraapp/{train,valid,test}/{images,labels}/`.
  6. Imprime reporte: imágenes por clase + por split + warnings.

Uso:
    python scripts/prepare_dataset.py
    python scripts/prepare_dataset.py --config scripts/prepare_config.yaml
    python scripts/prepare_dataset.py --dry-run     # inspecciona sin copiar
"""
from __future__ import annotations

import argparse
import logging
import random
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "Falta PyYAML. Instala con: pip install -r scripts/requirements.txt\n"
    )
    sys.exit(1)

# ───────────────────────────────────────────────────────────────── Constantes

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# Contrato con backend/app/services/inference_service.py::CLASS_MAP
CANONICAL_CLASSES: dict[int, str] = {
    0: "aguacate_hass_INMADURO",
    1: "aguacate_hass_OPTIMO",
    2: "aguacate_hass_SOBRE_MADURO",
    3: "platano_INMADURO",
    4: "platano_OPTIMO",
    5: "platano_SOBRE_MADURO",
    6: "tomate_usda_INMADURO",
    7: "tomate_usda_OPTIMO",
    8: "tomate_usda_SOBRE_MADURO",
    9: "mango_INMADURO",
    10: "mango_OPTIMO",
    11: "mango_SOBRE_MADURO",
}

logger = logging.getLogger("prepare_dataset")


# ──────────────────────────────────────────────────────────────────── Modelo

@dataclass
class Source:
    """Un origen de imágenes mapeado a una clase canónica."""

    path: Path
    class_id: int
    bbox_strategy: str  # "full_frame" o "passthrough"

    def __post_init__(self) -> None:
        if self.class_id not in CANONICAL_CLASSES:
            raise ValueError(
                f"class_id={self.class_id} inválido. Debe estar en 0..11. "
                f"Ver scripts/README.md para la tabla canónica."
            )
        if self.bbox_strategy not in ("full_frame", "passthrough"):
            raise ValueError(
                f"bbox_strategy='{self.bbox_strategy}' inválido. "
                f"Usa 'full_frame' o 'passthrough'."
            )


@dataclass
class Config:
    output_dir: Path
    sources: list[Source]
    split: tuple[float, float, float]  # train, valid, test
    min_per_class: int
    seed: int

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)

        default_bbox = raw.get("bbox_strategy", "full_frame")
        sources = [
            Source(
                path=(path.parent / src["path"]).resolve(),
                class_id=int(src["class_id"]),
                bbox_strategy=src.get("bbox_strategy", default_bbox),
            )
            for src in raw["sources"]
        ]

        split = raw.get("split", {})
        split_tuple = (
            float(split.get("train", 0.70)),
            float(split.get("valid", 0.15)),
            float(split.get("test", 0.15)),
        )
        if abs(sum(split_tuple) - 1.0) > 1e-6:
            raise ValueError(f"split debe sumar 1.0, suma {sum(split_tuple)}")

        return cls(
            output_dir=(path.parent / raw["output_dir"]).resolve(),
            sources=sources,
            split=split_tuple,
            min_per_class=int(raw.get("min_per_class", 200)),
            seed=int(raw.get("seed", 42)),
        )


# ───────────────────────────────────────────────────────── Lógica principal

def collect_images(source: Source) -> list[Path]:
    """Lista todas las imágenes válidas dentro de un Source (no recursivo
    si se quiere granularidad, recursivo si la carpeta tiene subniveles).
    """
    if not source.path.exists():
        logger.warning("Source no existe: %s", source.path)
        return []

    images = [
        p for p in source.path.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES
    ]
    return sorted(images)


def stratified_split(
    images: list[Path], ratios: tuple[float, float, float], rng: random.Random
) -> tuple[list[Path], list[Path], list[Path]]:
    """Split por porcentaje preservando el orden aleatorio.

    No es estratificado por clase aquí — el caller llama esto por cada clase
    para garantizar que cada clase aparece en los 3 splits.
    """
    shuffled = list(images)
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(n * ratios[0])
    n_valid = int(n * ratios[1])
    # El resto a test, así no perdemos imágenes por redondeo
    train = shuffled[:n_train]
    valid = shuffled[n_train : n_train + n_valid]
    test = shuffled[n_train + n_valid :]
    return train, valid, test


def write_label(label_path: Path, class_id: int, strategy: str, src_image: Path) -> None:
    """Crea el `.txt` de YOLO para una imagen.

    full_frame  → 1 línea, bbox cubre toda la imagen
    passthrough → copia el `.txt` que ya existe junto al source (mismo stem)
    """
    label_path.parent.mkdir(parents=True, exist_ok=True)

    if strategy == "full_frame":
        # Formato YOLO: <class_id> <cx> <cy> <w> <h> normalizados a [0,1]
        label_path.write_text(f"{class_id} 0.5 0.5 1.0 1.0\n", encoding="utf-8")
        return

    if strategy == "passthrough":
        external = src_image.with_suffix(".txt")
        if not external.exists():
            raise FileNotFoundError(
                f"bbox_strategy=passthrough pero no existe {external}. "
                f"Confirma que el dataset crudo trae sus propios .txt."
            )
        # Reescribir class_ids para que coincidan con CANONICAL_CLASSES.
        # En passthrough asumimos que el `.txt` original ya viene con
        # bboxes válidos, pero los `class_id` originales rara vez coinciden
        # con nuestro orden — forzamos el class_id del Source.
        lines = []
        for line in external.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            # Reemplazamos solo el class_id, dejamos las coordenadas tal cual
            parts[0] = str(class_id)
            lines.append(" ".join(parts))
        label_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    raise ValueError(f"bbox_strategy desconocida: {strategy}")


def copy_image_and_label(
    src_image: Path,
    target_root: Path,
    split_name: str,
    class_id: int,
    strategy: str,
    sequence: int,
) -> None:
    """Copia imagen + crea label en la estructura final.

    Renombra los archivos a `{class_id:02d}_{sequence:06d}.{ext}` para evitar
    colisiones entre datasets que casualmente compartan nombres.
    """
    suffix = src_image.suffix.lower()
    new_stem = f"{class_id:02d}_{sequence:06d}"

    image_dest = target_root / split_name / "images" / f"{new_stem}{suffix}"
    label_dest = target_root / split_name / "labels" / f"{new_stem}.txt"

    image_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_image, image_dest)
    write_label(label_dest, class_id, strategy, src_image)


def prepare(config: Config, dry_run: bool = False) -> int:
    """Ejecuta el pipeline completo. Retorna el exit code (0 = éxito,
    2 = warnings críticos como clases por debajo del mínimo).
    """
    rng = random.Random(config.seed)

    # ─── Paso 1: agrupar imágenes por class_id (un Source puede aportar a
    # la misma clase desde múltiples carpetas)
    per_class: dict[int, list[tuple[Path, str]]] = defaultdict(list)
    for source in config.sources:
        images = collect_images(source)
        try:
            displayed = source.path.relative_to(PROJECT_ROOT)
        except ValueError:
            displayed = source.path
        logger.info(
            "  - class_id=%2d (%s)  <-  %s  [%d imgs, %s]",
            source.class_id,
            CANONICAL_CLASSES[source.class_id],
            displayed,
            len(images),
            source.bbox_strategy,
        )
        per_class[source.class_id].extend((img, source.bbox_strategy) for img in images)

    # ─── Paso 2: validar threshold y clases faltantes
    warnings: list[str] = []
    for class_id in range(12):
        count = len(per_class.get(class_id, []))
        if count == 0:
            warnings.append(
                f"❌ clase {class_id} ({CANONICAL_CLASSES[class_id]}): SIN imágenes"
            )
        elif count < config.min_per_class:
            warnings.append(
                f"⚠️  clase {class_id} ({CANONICAL_CLASSES[class_id]}): "
                f"{count} imgs < min {config.min_per_class}"
            )

    if dry_run:
        logger.info("--- DRY RUN: no se copiará nada ---")
        print_report(per_class, warnings, config, splits_done=False)
        return 2 if warnings else 0

    # ─── Paso 3: limpiar output_dir e instanciar estructura
    if config.output_dir.exists():
        logger.warning("Limpiando %s antes de regenerar", config.output_dir)
        shutil.rmtree(config.output_dir)
    for split in ("train", "valid", "test"):
        (config.output_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (config.output_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    # ─── Paso 4: split estratificado y copia
    split_counts: dict[str, dict[int, int]] = {
        "train": defaultdict(int),
        "valid": defaultdict(int),
        "test": defaultdict(int),
    }
    seq = 0
    for class_id, entries in sorted(per_class.items()):
        # Mantenemos la estrategia por imagen (un mismo class_id puede mezclar
        # carpetas full_frame y passthrough — aunque no es común, lo soportamos)
        train, valid, test = stratified_split(entries, config.split, rng)
        for split_name, bucket in (("train", train), ("valid", valid), ("test", test)):
            for img_path, strategy in bucket:
                copy_image_and_label(
                    src_image=img_path,
                    target_root=config.output_dir,
                    split_name=split_name,
                    class_id=class_id,
                    strategy=strategy,
                    sequence=seq,
                )
                seq += 1
                split_counts[split_name][class_id] += 1

    # ─── Paso 5: reporte final
    print_report(per_class, warnings, config, splits_done=True, split_counts=split_counts)

    return 2 if warnings else 0


# ───────────────────────────────────────────────────────────────── Reporting

def print_report(
    per_class: dict[int, list],
    warnings: list[str],
    config: Config,
    splits_done: bool,
    split_counts: dict[str, dict[int, int]] | None = None,
) -> None:
    print()
    print("═" * 70)
    print(" REPORTE DE PREPARACIÓN — MaduraApp dataset")
    print("═" * 70)
    print(f" Output      : {config.output_dir}")
    print(f" Min/clase   : {config.min_per_class}")
    print(f" Split       : train={config.split[0]:.0%}  valid={config.split[1]:.0%}  test={config.split[2]:.0%}")
    print(f" Seed        : {config.seed}")
    print()
    print(" Conteo por clase:")
    print(f" {'id':>3}  {'clase':<30}  {'total':>6}  {'train':>6}  {'valid':>6}  {'test':>6}")
    print(" " + "─" * 67)
    total = 0
    for class_id in range(12):
        count = len(per_class.get(class_id, []))
        total += count
        row = f" {class_id:>3}  {CANONICAL_CLASSES[class_id]:<30}  {count:>6}"
        if splits_done and split_counts is not None:
            row += (
                f"  {split_counts['train'][class_id]:>6}"
                f"  {split_counts['valid'][class_id]:>6}"
                f"  {split_counts['test'][class_id]:>6}"
            )
        print(row)
    print(" " + "─" * 67)
    print(f" {'':>3}  {'TOTAL':<30}  {total:>6}")
    print()

    if warnings:
        print(" Warnings:")
        for w in warnings:
            print(f"   {w}")
        print()

    if splits_done:
        print(" ✅ Dataset listo en:", config.output_dir)
        print(" Siguiente paso:  python scripts/train_model.py")
    else:
        print(" 🔍 Dry-run completado. Re-ejecuta sin --dry-run para generar.")
    print("═" * 70)


# ──────────────────────────────────────────────────────────────────── CLI

def main(argv: Iterable[str] | None = None) -> int:
    # Windows: la consola por defecto es cp1252; forzar UTF-8 para que los
    # emojis y cajas Unicode del reporte no rompan el print.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Normaliza datasets crudos al formato YOLO de MaduraApp"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "scripts" / "prepare_config.yaml",
        help="Ruta al YAML de mapeo (default: scripts/prepare_config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspecciona los sources y muestra el reporte sin copiar nada",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Logging DEBUG"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)-7s %(message)s",
    )

    if not args.config.exists():
        sys.stderr.write(
            f"❌ No existe {args.config}.\n"
            f"   Copia scripts/prepare_config.example.yaml → {args.config.name} "
            f"y ajusta los paths.\n"
        )
        return 1

    try:
        config = Config.from_yaml(args.config)
    except (KeyError, ValueError) as exc:
        sys.stderr.write(f"❌ Config inválida: {exc}\n")
        return 1

    return prepare(config, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
