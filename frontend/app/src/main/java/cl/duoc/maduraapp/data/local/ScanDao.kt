package cl.duoc.maduraapp.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

/**
 * DAO del cache local de escaneos. Todas las operaciones son async via
 * suspend o Flow para no bloquear el hilo principal.
 */
@Dao
interface ScanDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: ScanCacheEntity): Long

    /** Stream reactivo: la UI se actualiza sola cuando entra un escaneo nuevo. */
    @Query("SELECT * FROM scan_cache ORDER BY captured_at DESC LIMIT :limit")
    fun observeRecent(limit: Int = 50): Flow<List<ScanCacheEntity>>

    @Query("SELECT * FROM scan_cache ORDER BY captured_at DESC LIMIT :limit OFFSET :offset")
    suspend fun getRecent(limit: Int = 50, offset: Int = 0): List<ScanCacheEntity>

    @Query("SELECT COUNT(*) FROM scan_cache")
    suspend fun count(): Int

    @Query("DELETE FROM scan_cache")
    suspend fun clear()
}
