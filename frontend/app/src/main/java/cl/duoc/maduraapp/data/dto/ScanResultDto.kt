package cl.duoc.maduraapp.data.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Espejo del schema `ScanResult` del backend FastAPI.
 *
 * Estados:
 *  - `maturity_label`: INMADURO | OPTIMO | SOBRE_MADURO
 *  - `color_code`:     green   | yellow | red
 */
@Serializable
data class ScanResultDto(
    @SerialName("fruit_type") val fruitType: String,
    @SerialName("maturity_label") val maturityLabel: String,
    val confidence: Double,
    val bbox: List<Double>,
    val recommendation: String,
    @SerialName("color_code") val colorCode: String,
)
