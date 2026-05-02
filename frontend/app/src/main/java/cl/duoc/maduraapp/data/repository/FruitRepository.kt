package cl.duoc.maduraapp.data.repository

import cl.duoc.maduraapp.data.api.ApiClient
import cl.duoc.maduraapp.data.api.MaduraApiService
import cl.duoc.maduraapp.data.dto.HistoryResponseDto
import cl.duoc.maduraapp.data.dto.PredictResponseDto
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

/**
 * Capa de repositorio: encapsula el acceso a la API y normaliza errores.
 *
 * Convierte `ByteArray` (imagen capturada por CameraX) en `MultipartBody.Part`
 * antes de llamar al endpoint /v1/predict.
 */
class FruitRepository(
    private val api: MaduraApiService = ApiClient.service,
) {

    suspend fun predict(
        imageBytes: ByteArray,
        bearerToken: String? = null,
    ): Result<PredictResponseDto> = runCatching {
        val mediaType = "image/jpeg".toMediaTypeOrNull()
        val requestBody = imageBytes.toRequestBody(mediaType)
        val part = MultipartBody.Part.createFormData(
            name = "file",
            filename = "scan.jpg",
            body = requestBody,
        )
        api.predict(part, bearerToken?.let { "Bearer $it" })
    }

    suspend fun history(
        limit: Int = 50,
        offset: Int = 0,
        bearerToken: String? = null,
    ): Result<HistoryResponseDto> = runCatching {
        api.history(limit, offset, bearerToken?.let { "Bearer $it" })
    }

    suspend fun isBackendHealthy(): Boolean = runCatching {
        val response = api.health()
        response["status"] == "ok"
    }.getOrDefault(false)
}
