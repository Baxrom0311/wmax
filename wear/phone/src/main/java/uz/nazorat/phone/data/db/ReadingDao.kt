package uz.nazorat.phone.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface ReadingDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertReading(reading: ReadingEntity): Long

    @Query("SELECT * FROM readings_buffer WHERE isSynced = 0 ORDER BY createdAt ASC LIMIT :limit")
    suspend fun getUnsyncedReadings(limit: Int = 500): List<ReadingEntity>

    @Query("UPDATE readings_buffer SET isSynced = 1 WHERE id IN (:ids)")
    suspend fun markAsSynced(ids: List<Long>)

    @Query("DELETE FROM readings_buffer WHERE isSynced = 1 AND createdAt < :thresholdMs")
    suspend fun deleteOldSynced(thresholdMs: Long)

    @Query("SELECT COUNT(*) FROM readings_buffer WHERE isSynced = 0")
    fun getUnsyncedCountFlow(): Flow<Int>

    @Query("SELECT * FROM readings_buffer ORDER BY createdAt DESC LIMIT 1")
    fun getLatestReadingFlow(): Flow<ReadingEntity?>
}
