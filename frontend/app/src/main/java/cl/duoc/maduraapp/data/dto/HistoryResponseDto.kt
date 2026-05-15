package cl.duoc.maduraapp.data.dto

import kotlinx.serialization.Serializable

/** Espejo de `HistoryResponse` del backend (`GET /v1/history`). */
@Serializable
data class HistoryResponseDto(
    val items: List<ScanResultDto>,
    val total: Int,
    val limit: Int,
    val offset: Int,
)
