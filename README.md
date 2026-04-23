# MaduraApp

> Sistema de análisis de madurez agrícola mediante visión computacional e IA en la nube.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)
![YOLO26n](https://img.shields.io/badge/YOLO-26n-purple)
![Android](https://img.shields.io/badge/Android-Kotlin-orange)
![License](https://img.shields.io/badge/License-Private-red)

## Descripción

MaduraApp clasifica el estado de madurez de 4 frutos climatéricos (Aguacate Hass, Plátano, Tomate USDA, Mango) usando un modelo YOLO26n desplegado en FastAPI + nube, accedido desde una app Android nativa.

## Stack Tecnológico

| Capa       | Tecnología                          |
|------------|-------------------------------------|
| Frontend   | Android Nativo — Kotlin + CameraX   |
| Backend    | Python 3.12 + FastAPI 0.135         |
| IA         | YOLO26n Nano (Ultralytics)          |
| BD         | PostgreSQL / SQLite (dev)           |
| Cloud      | Render / AWS App Runner             |
| CI/CD      | GitHub Actions                      |

## Estructura del Repositorio