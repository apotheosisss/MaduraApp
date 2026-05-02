package cl.duoc.maduraapp.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Versión local-cache del escaneo.
 *
 * Es independiente del DTO de red ([cl.duoc.maduraapp.data.dto.ScanResultDto])
 * y de la entidad del backend (`ScanEntity` en SQLAlchemy). Esto permite que
 * los esquemas evolucionen por separado sin acoplarse.
 *
 * `bbox` se persiste como JSON serializado (List<Double>) vía [Converters].
 */
@Entity(tableName = "scan_cache")
data class ScanCacheEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "fruit_type") val fruitType: String,
    @ColumnInfo(name = "maturity_label") val maturityLabel: String,
    val confidence: Double,
    val bbox: List<Double>,
    val recommendation: String,
    @ColumnInfo(name = "color_code") val colorCode: String,

    /** Epoch millis. Determina el orden DESC del historial. */
    @ColumnInfo(name = "captured_at") val capturedAt: Long,
)
