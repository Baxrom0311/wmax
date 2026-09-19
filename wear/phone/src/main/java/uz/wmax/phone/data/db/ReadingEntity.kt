package uz.wmax.phone.data.db

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Local Room DB entity buffering unsent readings.
 * Ensures 0 data loss during network blackouts.
 */
@Entity(
    tableName = "readings_buffer",
    indices = [
        Index(value = ["ts"], unique = true),
        Index(value = ["isSynced"])
    ]
)
data class ReadingEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val ts: String,
    val patientId: String,
    val deviceId: String?,
    val payloadJson: String,
    val isSynced: Boolean = false,
    val createdAt: Long = System.currentTimeMillis()
)
