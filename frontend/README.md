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

## Implementado

- [x] Captura con CameraX + envío al backend
- [x] Semáforo de madurez (verde / amarillo / rojo) + recomendación
- [x] **Pantalla de historial** (`HistoryActivity`) con RecyclerView + pull-to-refresh
- [x] **Cache offline con Room** — los escaneos quedan disponibles aunque caiga la red
- [x] Refresh remoto del historial desde `GET /v1/history`
- [x] **Tests JVM** — Repository + ScanViewModel + HistoryViewModel
      (MockK + kotlinx-coroutines-test + Turbine + arch-core-testing)

## Correr tests

```bash
# Tests JVM (rápidos, sin emulador)
./gradlew test

# Solo el módulo app
./gradlew :app:testDebugUnitTest

# Tests instrumentados (necesitan emulador / device)
./gradlew connectedAndroidTest
```

## Siguiente (post-MVP)

- [ ] Integración real con autenticación JWT
- [ ] Detalle de un escaneo (tap en el item del historial)
- [ ] Dark mode tuneado
- [ ] Tests instrumentados (Espresso) de los flujos UI completos
