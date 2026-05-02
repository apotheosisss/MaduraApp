"""Descarga el dataset de entrenamiento desde Roboflow.

Lee credenciales desde variables de entorno (.env) para no hardcodear
la API key. Si necesitas mezclar varios datasets (Roboflow Universe + Kaggle
+ tus propias capturas), agrega más entradas a `DATASETS` y este script las
descargará secuencialmente.

Uso:
    export ROBOFLOW_API_KEY=xxx
    python scripts/download_dataset.py

Variables de entorno:
    ROBOFLOW_API_KEY (obligatorio)
    ROBOFLOW_WORKSPACE (default: maduraapp-duoc)
    ROBOFLOW_PROJECT   (default: maduraapp-ripeness)
    ROBOFLOW_VERSION   (default: 1)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    from roboflow import Roboflow
except ImportError:
    sys.stderr.write(
        "Faltan dependencias. Instala con:\n"
        "    pip install -r scripts/requirements.txt\n"
    )
    sys.exit(1)

# Permite ejecutar el script desde cualquier ubicación
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets" / "maduraapp"


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")

    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        sys.stderr.write(
            "ERROR: ROBOFLOW_API_KEY no está definida.\n"
            "Crea un .env en la raíz del proyecto con:\n"
            "    ROBOFLOW_API_KEY=tu_api_key\n"
        )
        return 1

    workspace = os.environ.get("ROBOFLOW_WORKSPACE", "maduraapp-duoc")
    project_slug = os.environ.get("ROBOFLOW_PROJECT", "maduraapp-ripeness")
    version_num = int(os.environ.get("ROBOFLOW_VERSION", "1"))

    DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📥 Descargando dataset desde Roboflow:")
    print(f"   workspace = {workspace}")
    print(f"   project   = {project_slug}")
    print(f"   version   = {version_num}")
    print(f"   destino   = {DATASETS_DIR}")

    rf = Roboflow(api_key=api_key)
    project = rf.workspace(workspace).project(project_slug)
    version = project.version(version_num)

    # Formato YOLOv8 (compatible con YOLO26n via Ultralytics)
    dataset = version.download("yolov8", location=str(DATASETS_DIR))

    print(f"✅ Dataset listo en: {dataset.location}")
    print()
    print("Verifica que existan estas carpetas:")
    for split in ("train", "valid", "test"):
        n_imgs = len(list((DATASETS_DIR / split / "images").glob("*"))) \
            if (DATASETS_DIR / split / "images").exists() else 0
        print(f"   {split}/images ({n_imgs} archivos)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
