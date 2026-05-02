package cl.duoc.maduraapp.data.local

import androidx.room.TypeConverter
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.builtins.serializer
import kotlinx.serialization.json.Json

/**
 * Type converters para Room.
 *
 * Room no soporta nativamente `List<Double>`, así que persistimos `bbox` como
 * un string JSON. Usamos Kotlinx Serialization (ya en el classpath para los
 * DTOs) para evitar agregar Gson/Moshi.
 */
class Converters {

    @TypeConverter
    fun fromBbox(bbox: List<Double>): String =
        Json.encodeToString(ListSerializer(Double.serializer()), bbox)

    @TypeConverter
    fun toBbox(raw: String): List<Double> =
        Json.decodeFromString(ListSerializer(Double.serializer()), raw)
}
