"""Normaliza datasets crudos (Kaggle / capturas propias) al formato YOLO
contractual de MaduraApp.

Pipeline:
  1. Lee `prepare_config.yaml` con el mapeo directorio_crudo → class_id.
  2. Inspecciona cada source: cuenta imágenes válidas, ignora basura.
  3. Genera bboxes:
       - `full_frame`: una caja que cubre toda la imagen (clasificación →
         detección barata, útil cuando la fruta llena el frame).
       - `passthrough`: copia los `.txt` ya existentes y reescribe los
         class_ids usando `class_remap` (útil para datasets de detección
         con taxonomía distinta, como Laboro Tomato).
  4. `glob_pattern`: filtra qué archivos tomar de una carpeta que mezcla
     múltiples frutas (ej: `mango_*` en `Train/Unripe/`).
  5. Split estratificado por clase (cada clase aparece en train/valid/test).
  6. Copia a `datasets/maduraapp/{train,valid,test}/{images,labels}/`.
  7. Imprime reporte: imágenes por clase + por split + warnings.

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
from dataclasses import dataclass, field
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
    """Un origen de imágenes con su mapeo a clase(s) canónica(s)."""

    path: Path
    class_id: int              # -1 si se usa class_remap
    bbox_strategy: str         # "full_frame" o "passthrough"
    class_remap: dict[int, int] | None = None  # para passthrough multi-clase
    glob_pattern: str | None = None            # filtro de archivos en carpeta mixta

    def __post_init__(self) -> None:
        if self.bbox_strategy not in ("full_frame", "passthrough"):
            raise ValueError(
                f"bbox_strategy='{self.bbox_strategy}' inválido. "
                f"Usa 'full_frame' o 'passthrough'."
            )
        if self.class_remap is not None:
            for orig, canon in self.class_remap.items():
                if canon not in CANONICAL_CLASSES:
                    raise ValueError(
                        f"class_remap: target {canon} inválido. "
                        f"Debe estar en 0..11."
                    )
        else:
            if self.class_id not in CANONICAL_CLASSES:
                raise ValueError(
                    f"class_id={self.class_id} inválido. Debe estar en 0..11 "
                    f"(o usar class_remap). Ver scripts/README.md."
                )

    @property
    def naming_class_id(self) -> int:
        """Class id representativo para nombrar archivos de salida."""
        if self.class_remap is not None:
            return min(self.class_remap.values())
        return self.class_id


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
                class_id=int(src.get("class_id", -1)),
                bbox_strategy=src.get("bbox_strategy", default_bbox),
                class_remap={int(k): int(v) for k, v in src["class_remap"].items()}
                             if src.get("class_remap") else None,
                glob_pattern=src.get("glob_pattern"),
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
            raise ValueError(f"split debe sumar 1.0, suma {sum(split_tuple):.4f}")

        return cls(
            output_dir=(path.parent / raw["output_dir"]).resolve(),
            sources=sources,
            split=split_tuple,
            min_per_class=int(raw.get("min_per_class", 200)),
            seed=int(raw.get("seed", 42)),
        )


# ───────────────────────────────────────────────────────── Lógica principal

def collect_images(source: Source) -> list[Path]:
    """Lista todas las imágenes válidas dentro de un Source."""
    if not source.path.exists():
        logger.warning("Source no existe: %s", source.path)
        return []

    if source.glob_pattern:
        # Búsqueda plana con patrón — útil para carpetas con múltiples frutas
        images = sorted(
            p for p in source.path.glob(source.glob_pattern)
            if p.suffix.lower() in IMAGE_SUFFIXES and p.is_file()
        )
    else:
        images = sorted(
            p for p in source.path.rglob("*")
            if p.suffix.lower() in IMAGE_SUFFIXES
        )
    return images


def stratified_split(
    images: list,
    ratios: tuple[float, float, float],
    rng: random.Random,
) -> tuple[list, list, list]:
    """Reparte aleatoriamente manteniendo las proporciones."""
    shuffled = list(images)
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(n * ratios[0])
    n_valid = int(n * ratios[1])
    train = shuffled[:n_train]
    valid = shuffled[n_train : n_train + n_valid]
    test = shuffled[n_train + n_valid :]
    return train, valid, test


def write_label(
    label_path: Path,
    class_id: int,
    strategy: str,
    src_image: Path,
    class_remap: dict[int, int] | None = None,
) -> None:
    """Crea el `.txt` YOLO para una imagen."""
    label_path.parent.mkdir(parents=True, exist_ok=True)

    if strategy == "full_frame":
        label_path.write_text(
            f"{class_id} 0.5 0.5 1.0 1.0\n", encoding="utf-8"
        )
        return

    if strategy == "passthrough":
        external = src_image.with_suffix(".txt")
        # Laboro guarda labels en ../labels/ en vez de junto a la imagen
        if not external.exists():
            labels_dir = src_image.parent.parent / "labels"
            external = labels_dir / src_image.with_suffix(".txt").name
        if not external.exists():
            raise FileNotFoundError(
                f"passthrough: no existe label para {src_image}.\n"
                f"  Buscado en: {src_image.with_suffix('.txt')} y {external}"
            )

        lines: list[str] = []
        for line in external.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            orig_class = int(parts[0])
            if class_remap is not None:
                if orig_class not in class_remap:
                    continue  # bbox de clase no relevante — omitir
                parts[0] = str(class_remap[orig_class])
            else:
                parts[0] = str(class_id)
            lines.append(" ".join(parts))

        label_path.write_text(
            "\n".join(lines) + "\n" if lines else "", encoding="utf-8"
        )
        return

    raise ValueError(f"bbox_strategy desconocida: {strategy}")


def copy_image_and_label(
    src_image: Path,
    target_root: Path,
    split_name: str,
    class_id: int,
    strategy: str,
    sequence: int,
    class_remap: dict[int, int] | None = None,
) -> None:
    """Copia imagen + crea label en la estructura final."""
    suffix = src_image.suffix.lower()
    new_stem = f"{class_id:02d}_{sequence:06d}"

    image_dest = target_root / split_name / "images" / f"{new_stem}{suffix}"
    label_dest = target_root / split_name / "labels" / f"{new_stem}.txt"

    image_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_image, image_dest)
    write_label(label_dest, class_id, strategy, src_image, class_remap)


def prepare(config: Config, dry_run: bool = False) -> int:
    """Ejecuta el pipeline completo. Retorna exit code (0 = ok, 2 = warnings)."""
    rng = random.Random(config.seed)

    # ─── Paso 1: agrupar imágenes por naming_class_id
    per_class: dict[int, list[tuple[Path, str, dict | None]]] = defaultdict(list)
    for source in config.sources:
        images = collect_images(source)
        try:
            displayed = source.path.relative_to(PROJECT_ROOT)
        except ValueError:
            displayed = source.path
        strategy_info = source.bbox_strategy
        if source.class_remap:
            strategy_info += "+remap"
        if source.glob_pattern:
            strategy_info += f"[{source.glob_pattern}]"
        logger.info(
            "  - class_id=%2d (%s)  <-  %s  [%d imgs, %s]",
            source.naming_class_id,
            CANONICAL_CLASSES[source.naming_class_id],
            displayed,
            len(images),
            strategy_info,
        )
        per_class[source.naming_class_id].extend(
            (img, source.bbox_strategy, source.class_remap) for img in images
        )

    # ─── Paso 2: validar threshold y clases faltantes
    warnings: list[str] = []
    for class_id in range(12):
        count = len(per_class.get(class_id, []))
        if count == 0:
            warnings.append(
                f"[SIN DATOS]  clase {class_id:>2} "
                f"({CANONICAL_CLASSES[class_id]})"
            )
        elif count < config.min_per_class:
            warnings.append(
                f"[BAJO MIN]   clase {class_id:>2} "
                f"({CANONICAL_CLASSES[class_id]}): "
                f"{count} imgs < min {config.min_per_class}"
            )

    if dry_run:
        logger.info("--- DRY RUN: no se copiara nada ---")
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
        train, valid, test = stratified_split(entries, config.split, rng)
        for split_name, bucket in (
            ("train", train), ("valid", valid), ("test", test)
        ):
            for img_path, strategy, class_remap in bucket:
                copy_image_and_label(
                    src_image=img_path,
                    target_root=config.output_dir,
                    split_name=split_name,
                    class_id=class_id,
                    strategy=strategy,
                    sequence=seq,
                    class_remap=class_remap,
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
    w = 70
    print()
    print("=" * w)
    print(" REPORTE DE PREPARACION -- MaduraApp dataset")
    print("=" * w)
    print(f" Output      : {config.output_dir}")
    print(f" Min/clase   : {config.min_per_class}")
    print(
        f" Split       : train={config.split[0]:.0%}  "
        f"valid={config.split[1]:.0%}  test={config.split[2]:.0%}"
    )
    print(f" Seed        : {config.seed}")
    print()
    print(" Conteo por clase:")
    print(f" {'id':>3}  {'clase':<32}  {'total':>6}  {'train':>6}  {'valid':>6}  {'test':>6}")
    print(" " + "-" * (w - 1))
    total = 0
    for class_id in range(12):
        count = len(per_class.get(class_id, []))
        total += count
        row = f" {class_id:>3}  {CANONICAL_CLASSES[class_id]:<32}  {count:>6}"
        if splits_done and split_counts is not None:
            row += (
                f"  {split_counts['train'][class_id]:>6}"
                f"  {split_counts['valid'][class_id]:>6}"
                f"  {split_counts['test'][class_id]:>6}"
            )
        print(row)
    print(" " + "-" * (w - 1))
    print(f" {'':>3}  {'TOTAL':<32}  {total:>6}")
    print()

    if warnings:
        print(" Advertencias:")
        for w_msg in warnings:
            print(f"   {w_msg}")
        print()

    if splits_done:
        print(f" Dataset listo en: {config.output_dir}")
        print(" Siguiente paso: python scripts/train_model.py")
    else:
        print(" Dry-run completado. Re-ejecuta sin --dry-run para generar.")
    print("=" * 70)


# ──────────────────────────────────────────────────────────────────── CLI

def main(argv: Iterable[str] | None = None) -> int:
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
            f"No existe {args.config}.\n"
            f"Crea scripts/prepare_config.yaml basandote en "
            f"scripts/prepare_config.example.yaml\n"
        )
        return 1

    try:
        config = Config.from_yaml(args.config)
    except (KeyError, ValueError) as exc:
        sys.stderr.write(f"Config invalida: {exc}\n")
        return 1

    return prepare(config, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
