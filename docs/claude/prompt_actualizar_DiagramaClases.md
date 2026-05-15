# Prompt — Actualizar Diagrama de Clases MaduraApp

## Contexto

El diagrama de clases original fue diseñado en la fase de planificación. El sistema
real implementado tiene más clases y relaciones. Usa esta especificación para
actualizarlo en tu herramienta UML (Draw.io, Lucidchart, StarUML, etc.).

---

## Clases implementadas — Backend (Python)

### `Settings` (core/config.py)
```
+ API_PORT: int
+ YOLO_MODEL_PATH: str
+ CONFIDENCE_THRESHOLD: float
+ DB_URL: str
+ AUTH_SECRET_KEY: str
+ ENVIRONMENT: str
```

### `YOLO26Wrapper` (core/yolo_wrapper.py)
```
- model_path: str
- device: str
- model: YOLO
+ load_model(): void
+ warmup(): void
+ predict(image): list
```

### `ScanEntity` (models/scan_entity.py) — ORM tabla `scans`
```
+ scan_id: str  [PK, UUID]
+ user_token: str
+ fruit_type: str
+ maturity_label: str
+ confidence: float
+ bbox: list  [JSON]
+ recommendation: str
+ color_code: str
+ created_at: datetime
```

### `InferenceService` (services/inference_service.py)
```
+ CLASS_MAP: dict
+ COLOR_MAP: dict
+ RECOMMENDATION_MAP: dict
+ validate_image(image_bytes): bool
+ preprocess(image_bytes): ndarray
+ postprocess(results): ScanResult
+ run(image_bytes, model): ScanResult
```

### `HistoryService` (services/history_service.py)
```
+ save(scan, user_token, session): ScanEntity
+ get_all(user_token, session, limit, offset): tuple
```

### Schemas Pydantic
```
ScanResult
+ fruit_type: str
+ maturity_label: str
+ confidence: float
+ bbox: list[float]
+ recommendation: str
+ color_code: str
+ to_json(): dict

PredictResponse
+ success: bool
+ data: ScanResult?
+ error: str?

HistoryResponse
+ items: list[ScanResult]
+ total: int
+ limit: int
+ offset: int
```

---

## Clases implementadas — Android (Kotlin)

### `MainActivity`
```
- viewModel: ScanViewModel
- imageCapture: ImageCapture
- binding: ActivityMainBinding
+ startCamera(): void
+ takePictureAndSubmit(): void
+ renderIdle(): void
+ renderLoading(): void
+ renderSuccess(result): void
```

### `HistoryActivity`
```
- viewModel: HistoryViewModel
- adapter: HistoryAdapter
+ observeViewModel(): void
```

### `ScanViewModel`
```
- repository: FruitRepository
+ state: LiveData<ScanState>
+ reset(): void
+ submitImage(imageBytes, token?): void
```

### `HistoryViewModel`
```
- repository: FruitRepository
+ cachedItems: LiveData<List<ScanResultDto>>
+ state: LiveData<HistoryState>
+ refresh(token?): void
```

### `ScanState` (sealed interface)
```
Idle
Loading
Success(result: ScanResultDto)
NoDetection(message: String)
Error(cause: Throwable)
```

### `HistoryState` (sealed interface)
```
Loading
Loaded(items: List<ScanResultDto>)
Error(cause: Throwable, cachedItems: List<ScanResultDto>)
```

### `FruitRepository`
```
- api: MaduraApiService
- local: LocalScanDataSource
+ predict(imageBytes, token?): Result<PredictResponseDto>
+ refreshHistory(limit, offset, token?): Result<HistoryResponseDto>
+ observeLocalHistory(limit): Flow<List<ScanResultDto>>
+ isBackendHealthy(): Boolean
```

### `MaduraApiService` (Retrofit interface)
```
+ predict(file, token?): PredictResponseDto
+ history(limit, offset, token?): HistoryResponseDto
+ health(): Map<String, Any>
```

### `MaduraDatabase` (Room)
```
+ scanDao(): ScanDao
```

### `ScanDao` (Room DAO)
```
+ insert(entity): Long
+ observeRecent(limit): Flow<List<ScanCacheEntity>>
+ getRecent(limit, offset): List<ScanCacheEntity>
+ count(): Int
+ clear(): void
```

### `ScanCacheEntity` (Room Entity)
```
+ id: Long  [PK autoincrement]
+ fruitType: str
+ maturityLabel: str
+ confidence: Double
+ bbox: List<Double>  [JSON]
+ recommendation: str
+ colorCode: str
+ capturedAt: Long  [epoch ms]
```

### `LocalScanDataSource`
```
- dao: ScanDao
+ cache(result, capturedAt?): Long
+ observeRecent(limit): Flow<List<ScanResultDto>>
+ getRecent(limit, offset): List<ScanResultDto>
+ count(): Int
+ clear(): void
```

---

## Relaciones principales

```
MainActivity          ──uses──>    ScanViewModel
HistoryActivity       ──uses──>    HistoryViewModel
ScanViewModel         ──uses──>    FruitRepository
HistoryViewModel      ──uses──>    FruitRepository
FruitRepository       ──uses──>    MaduraApiService
FruitRepository       ──uses──>    LocalScanDataSource
LocalScanDataSource   ──uses──>    ScanDao
MaduraDatabase        ──provides─> ScanDao
ScanDao               ──persists─> ScanCacheEntity

InferenceService      ──uses──>    YOLO26Wrapper
InferenceService      ──returns──> ScanResult
HistoryService        ──persists─> ScanEntity
```

---

## Instrucciones para actualizar

1. Abre el diagrama original en tu herramienta UML
2. **Agrega** las clases nuevas que no estaban (ScanCacheEntity, LocalScanDataSource,
   ScanDao, MaduraDatabase, HistoryViewModel, HistoryState, FruitRepository)
3. **Actualiza** las clases existentes con los atributos reales del código
4. **Elimina** clases del diseño original que no se implementaron
5. Organiza en dos paquetes: `backend` y `android`
6. Exporta como PNG y reemplaza `MaduraApp_DiagramaClases.png`
