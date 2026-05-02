package cl.duoc.maduraapp.data.dto

import kotlinx.serialization.Serializable

/**
 * Espejo de `PredictResponse` del backend.
 *
 *  - `success=true`  → `data` está poblado.
 *  - `success=false` → `error` describe la razón (ej: "No se detectó ninguna fruta soportada").
 */
@Serializable
data class PredictResponseDto(
    val success: Boolean,
    val data: ScanResultDto? = null,
    val error: String? = null,
)
