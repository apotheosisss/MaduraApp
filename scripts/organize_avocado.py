"""Organiza el dataset Mendeley 'Hass' Avocado Ripening en las 3 clases
canónicas de MaduraApp.

Fuente del dataset:
    https://data.mendeley.com/datasets/3xd9n945v8/1
    (Hass Avocado Ripening Photographic Dataset — 14.710 imágenes, 5 etapas)

Mapeo de etapas originales → clases canónicas:
    Etapa 1 (Underripe)          → INMADURO
    Etapa 2 (Breaking)           → INMADURO  (aún firme, no apto para consumo)
    Etapa 3 (Ripe – 1st Stage)   → OPTIMO
    Etapa 4 (Ripe – 2nd Stage)   → OPTIMO    (pico de madurez)
    Etapa 5 (Overripe)           → SOBRE_MADURO

Uso:
    python scripts/organize_avocado.py
    python scripts/organize_avocado.py --source datasets/raw/avocado-mendeley
    python scripts/organize_avocado.py --dry-run
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.stderr.write(
        "Falta openpyxl. Instala con:  pip install openpyxl\n"
    )
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Etapas originales del Ripening Index → clase canónica
STAGE_TO_CLASS: dict[int, str] = {
    1: "INMADURO",
    2: "INMADURO",
    3: "OPTIMO",
    4: "OPTIMO",
    5: "SOBRE_MADURO",
}

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def find_excel(source_dir: Path) -> Path:
    """Busca el archivo Excel de metadatos en el directorio del dataset."""
    for p in source_dir.rglob("*.xlsx"):
        return p
    for p in source_dir.rglob("*.xls"):
        return p
    raise FileNotFoundError(
        f"No se encontró ningún archivo Excel en {source_dir}.\n"
        "Asegúrate de haber extraído el ZIP completo del dataset Mendeley."
    )


def parse_excel(excel_path: Path) -> dict[str, int]:
    """Lee el Excel de Mendeley y devuelve {filename: ripening_stage}."""
    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("El archivo Excel está vacío.")

    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
    print(f"  Columnas encontradas en Excel: {headers}")

    # Detectar columna de nombre de archivo
    filename_col = next(
        (i for i, h in enumerate(headers)
         if any(k in h for k in ("file", "photo", "image", "foto", "name", "nombre"))),
        None,
    )
    # Detectar columna de etapa/ripening index
    stage_col = next(
        (i for i, h in enumerate(headers)
         if any(k in h for k in ("stage", "rip", "index", "etapa", "class", "label", "nivel"))),
        None,
    )

    if filename_col is None or stage_col is None:
        print(f"  ADVERTENCIA: No se detectaron columnas automáticamente.")
        print(f"  Columna nombre de archivo: {'col ' + str(filename_col) if filename_col is not None else 'NO ENCONTRADA'}")
        print(f"  Columna etapa: {'col ' + str(stage_col) if stage_col is not None else 'NO ENCONTRADA'}")
        print()
        print("  Escribe los índices manualmente (0 = primera columna):")
        filename_col = int(input("  Índice columna nombre de archivo: "))
        stage_col = int(input("  Índice columna etapa de madurez (1-5): "))

    mapping: dict[str, int] = {}
    skipped = 0
    for row in rows[1:]:
        if not row or row[filename_col] is None:
            continue
        try:
            fname = str(row[filename_col]).strip()
            stage = int(row[stage_col])
            if stage not in STAGE_TO_CLASS:
                skipped += 1
                continue
            # Asegurar que tiene extensión
            if not Path(fname).suffix:
                fname += ".jpg"
            mapping[fname] = stage
        except (ValueError, TypeError, IndexError):
            skipped += 1
            continue

    print(f"  {len(mapping)} entradas leídas del Excel ({skipped} filas omitidas)")
    return mapping


def organize(source_dir: Path, output_dir: Path, dry_run: bool = False) -> None:
    """Organiza las imágenes en subdirectorios por clase canónica."""
    print(f"\nBuscando Excel en {source_dir}...")
    excel_path = find_excel(source_dir)
    print(f"Excel encontrado: {excel_path.name}")
    mapping = parse_excel(excel_path)

    # Indexar imágenes disponibles (nombre → path completo)
    all_images: dict[str, Path] = {}
    for p in source_dir.rglob("*"):
        if p.suffix.lower() in IMAGE_SUFFIXES:
            all_images[p.name] = p
            # También indexar por stem por si el Excel no incluye extensión
            all_images[p.stem] = p

    print(f"\n{len(set(all_images.values()))} imágenes encontradas en {source_dir}")

    counts: dict[str, int] = {cls: 0 for cls in STAGE_TO_CLASS.values()}
    missing = 0

    for fname, stage in mapping.items():
        canonical_class = STAGE_TO_CLASS[stage]

        # Buscar la imagen
        img_path = all_images.get(fname) or all_images.get(Path(fname).stem)
        if img_path is None:
            missing += 1
            continue

        dest_dir = output_dir / canonical_class
        dest_file = dest_dir / img_path.name

        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img_path, dest_file)

        counts[canonical_class] += 1

    # ─── Reporte
    w = 60
    print()
    print("=" * w)
    print(" REPORTE organize_avocado")
    print("=" * w)
    print(f" Source  : {source_dir}")
    print(f" Output  : {output_dir}")
    print()
    print(f" {'Clase':<20}  {'Imágenes':>10}")
    print(" " + "-" * (w - 1))
    total = 0
    for cls in ("INMADURO", "OPTIMO", "SOBRE_MADURO"):
        n = counts[cls]
        total += n
        print(f" {cls:<20}  {n:>10}")
    print(" " + "-" * (w - 1))
    print(f" {'TOTAL':<20}  {total:>10}")
    if missing:
        print(f"\n  {missing} imágenes del Excel no encontradas en disco")
    print()
    if dry_run:
        print(" Dry-run: no se copiaron archivos.")
        print(" Re-ejecuta sin --dry-run para organizar.")
    else:
        print(f" Imágenes organizadas en {output_dir}")
        print()
        print(" Siguiente paso: agrega a prepare_config.yaml:")
        print(f"   - path: ../datasets/raw/avocado/{'{'}class{'}'}")
        print("     donde {class} = INMADURO | OPTIMO | SOBRE_MADURO")
    print("=" * w)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Organiza el dataset Mendeley Hass Avocado en clases canónicas"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "raw" / "avocado-mendeley",
        help="Carpeta donde extrajiste el ZIP de Mendeley",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "raw" / "avocado",
        help="Destino con subcarpetas INMADURO/ OPTIMO/ SOBRE_MADURO/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ver conteos sin copiar archivos",
    )
    args = parser.parse_args()

    if not args.source.exists():
        sys.stderr.write(
            f"No existe {args.source}.\n"
            f"Extrae el ZIP de Mendeley en esa carpeta primero.\n"
            f"URL: https://data.mendeley.com/datasets/3xd9n945v8/1\n"
        )
        return 1

    try:
        organize(args.source, args.output, dry_run=args.dry_run)
    except FileNotFoundError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1
    except KeyboardInterrupt:
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
