package cl.duoc.maduraapp.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters

/**
 * Base de datos local Room. Cache offline de escaneos.
 *
 * No es source of truth: el backend lo es. Esta capa sirve para:
 *  - Mostrar el último resultado aunque se pierda conectividad.
 *  - Reducir trips al backend al volver a abrir la pantalla de historial.
 */
@Database(
    entities = [ScanCacheEntity::class],
    version = 1,
    exportSchema = false,
)
@TypeConverters(Converters::class)
abstract class MaduraDatabase : RoomDatabase() {

    abstract fun scanDao(): ScanDao

    companion object {
        private const val DB_NAME = "maduraapp.db"

        @Volatile
        private var INSTANCE: MaduraDatabase? = null

        fun get(context: Context): MaduraDatabase = INSTANCE ?: synchronized(this) {
            INSTANCE ?: Room.databaseBuilder(
                context.applicationContext,
                MaduraDatabase::class.java,
                DB_NAME,
            )
                .fallbackToDestructiveMigration()
                .build()
                .also { INSTANCE = it }
        }
    }
}
