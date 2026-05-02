package cl.duoc.maduraapp.data.local

import cl.duoc.maduraapp.data.dto.ScanResultDto
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Wrapper sobre [ScanDao] que traduce entre [ScanResultDto] (capa de red /
 * dominio expuesto a la UI) y [ScanCacheEntity] (modelo de Room).
 */
class LocalScanDataSource(private val dao: ScanDao) {

    suspend fun cache(result: ScanResultDto, capturedAt: Long = System.currentTimeMillis()): Long =
        dao.insert(result.toCacheEntity(capturedAt))

    fun observeRecent(limit: Int = 50): Flow<List<ScanResultDto>> =
        dao.observeRecent(limit).map { rows -> rows.map { it.toDto() } }

    suspend fun getRecent(limit: Int = 50, offset: Int = 0): List<ScanResultDto> =
        dao.getRecent(limit, offset).map { it.toDto() }

    suspend fun count(): Int = dao.count()

    suspend fun clear() = dao.clear()
}

// ----------------------------------------------------------- Mappers internos

private fun ScanResultDto.toCacheEntity(capturedAt: Long) = ScanCacheEntity(
    fruitType = fruitType,
    maturityLabel = maturityLabel,
    confidence = confidence,
    bbox = bbox,
    recommendation = recommendation,
    colorCode = colorCode,
    capturedAt = capturedAt,
)

private fun ScanCacheEntity.toDto() = ScanResultDto(
    fruitType = fruitType,
    maturityLabel = maturityLabel,
    confidence = confidence,
    bbox = bbox,
    recommendation = recommendation,
    colorCode = colorCode,
)
