package cl.duoc.maduraapp.data.repository

import cl.duoc.maduraapp.MaduraApp
import cl.duoc.maduraapp.data.api.ApiClient
import cl.duoc.maduraapp.data.api.MaduraApiService
import cl.duoc.maduraapp.data.dto.HistoryResponseDto
import cl.duoc.maduraapp.data.dto.PredictResponseDto
import cl.duoc.maduraapp.data.dto.ScanResultDto
import cl.duoc.maduraapp.data.local.LocalScanDataSource
import kotlinx.coroutines.flow.Flow
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

/**
 * Capa de repositorio: encapsula el acceso a la API y al cache local Room.
 *
 * Estrategia:
 *  - El backend es la **fuente de verdad** del historial.
 *  - Tras una predicción exitosa, el resultado se cachea en Room para que la
 *    pantalla de historial pueda mostrarlo aún sin conexión.
 *  - El refresh remoto del historial reemplaza el cache local.
 */
class FruitRepository(
    private val api: MaduraApiService = ApiClient.service,
    private val local: LocalScanDataSource = LocalScanDataSource(MaduraApp.get().scanDao),
) {

    // ------------------------------------------------------------------ Predict

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
        val response = api.predict(part, bearerToken?.let { "Bearer $it" })

        // Cachear localmente solo si hubo detección
        response.data?.let { local.cache(it) }

        response
    }

    // ----------------------------------------------------------------- History

    /**
     * Refresca el historial desde el backend. Si tiene éxito, sustituye el
     * cache local. Si falla, devuelve el error sin tocar la cache (la UI
     * sigue mostrando lo último conocido vía [observeLocalHistory]).
     */
    suspend fun refreshHistory(
        limit: Int = 50,
        offset: Int = 0,
        bearerToken: String? = null,
    ): Result<HistoryResponseDto> = runCatching {
        val response = api.history(limit, offset, bearerToken?.let { "Bearer $it" })

        if (offset == 0) {
            local.clear()
            response.items.forEach { local.cache(it) }
        }

        response
    }

    /** Stream reactivo del cache local — la UI se actualiza al insertar nuevos. */
    fun observeLocalHistory(limit: Int = 50): Flow<List<ScanResultDto>> =
        local.observeRecent(limit)

    suspend fun localHistoryCount(): Int = local.count()

    // ------------------------------------------------------------------- Health

    suspend fun isBackendHealthy(): Boolean = runCatching {
        val response = api.health()
        response["status"] == "ok"
    }.getOrDefault(false)
}
