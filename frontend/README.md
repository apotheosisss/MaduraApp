# MaduraApp — Frontend Android

App nativa Kotlin que captura imágenes de frutas con CameraX y consume la API
FastAPI del backend para devolver el estado de madurez.

## Requisitos

- Android Studio Iguana o superior
- JDK 17
- Android SDK con API 34
- Dispositivo o emulador con **API 29+** (Android 10+)

## Configuración inicial

1. **Abrir el proyecto** en Android Studio: seleccionar la carpeta `frontend/`.
2. **Generar el wrapper** (primera vez): desde la terminal de Android Studio:
   ```
   gradle wrapper --gradle-version 8.9
   ```
   (o dejar que Android Studio lo descargue al sincronizar)
3. **URL del backend**: por defecto apunta a `http://10.0.2.2:8000/`
   (loopback del emulador hacia el host). Para cambiarla, edita
   `gradle.properties`:
   ```
   maduraapp.api.baseUrl=http://192.168.1.10:8000/
   ```

## Estructura

```
frontend/
├── app/
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/cl/duoc/maduraapp/
│       │   ├── MainActivity.kt              ← UI + CameraX
│       │   ├── data/
│       │   │   ├── api/
│       │   │   │   ├── MaduraApiService.kt  ← Retrofit interface
│       │   │   │   └── ApiClient.kt         ← Singleton HTTP
│       │   │   ├── dto/                     ← Espejo del backend
│       │   │   └── repository/
│       │   │       └── FruitRepository.kt
│       │   └── ui/
│       │       ├── ScanState.kt             ← sealed interface
│       │       └── ScanViewModel.kt         ← MVVM + LiveData
│       └── res/
│           ├── layout/activity_main.xml
│           ├── values/{strings,colors,themes}.xml
│           └── drawable/
└── build.gradle.kts (root + app)
```

## Patrón arquitectónico

**MVVM** con LiveData:

```
PreviewView (CameraX)  →  MainActivity  ─observe─→  ScanState
                                │
                                ↓ submitImage(bytes)
                          ScanViewModel
                                │
                                ↓
                          FruitRepository
                                │
                                ↓
                          MaduraApiService (Retrofit)
                                │
                                ↓ HTTPS multipart
                          Backend FastAPI
```

## Permisos

- `CAMERA` (runtime) — captura de imágenes
- `INTERNET` — comunicación con backend
- `ACCESS_NETWORK_STATE` — verificar conectividad

## Siguiente

- [ ] Pantalla de historial (consumir `GET /v1/history`)
- [ ] Persistencia local con Room (offline cache)
- [ ] Integración real con autenticación JWT
