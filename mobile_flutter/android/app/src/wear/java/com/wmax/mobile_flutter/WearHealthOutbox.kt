package com.wmax.mobile_flutter

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.PutDataMapRequest
import com.google.android.gms.wearable.Wearable
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID
import java.util.concurrent.TimeUnit

object WearHealthOutbox {
    private val lock = Any()
    private var helper: OutboxDatabase? = null

    fun enqueueHealthBatch(
        context: Context,
        source: String,
        samples: JSONArray,
        exerciseSessions: JSONArray = JSONArray(),
        collector: String,
    ): Boolean {
        val payloads = mutableListOf<String>()
        var chunk = mutableListOf<JSONObject>()
        for (index in 0 until samples.length()) {
            val sample = samples.getJSONObject(index)
            val candidate = chunk + sample
            if (encodedSize(payload(source, candidate, JSONArray(), collector)) > MAX_DATA_ITEM_BYTES) {
                if (chunk.isEmpty()) return false
                payloads += payload(source, chunk, JSONArray(), collector)
                chunk = mutableListOf(sample)
                if (encodedSize(payload(source, chunk, JSONArray(), collector)) > MAX_DATA_ITEM_BYTES) {
                    return false
                }
            } else {
                chunk = candidate.toMutableList()
            }
            if (chunk.size >= MAX_SAMPLES_PER_ITEM) {
                payloads += payload(source, chunk, JSONArray(), collector)
                chunk = mutableListOf()
            }
        }
        if (chunk.isNotEmpty()) payloads += payload(source, chunk, JSONArray(), collector)

        for (index in 0 until exerciseSessions.length()) {
            val session = JSONArray().put(exerciseSessions.getJSONObject(index))
            val encoded = payload(source, emptyList(), session, collector)
            if (encodedSize(encoded) > MAX_DATA_ITEM_BYTES) return false
            payloads += encoded
        }

        if (payloads.isEmpty()) return true
        if (!enqueuePayloads(context, payloads)) return false
        scheduleFlush(context)
        return true
    }

    fun scheduleFlush(context: Context) {
        val request = OneTimeWorkRequestBuilder<WearHealthOutboxWorker>().build()
        WorkManager.getInstance(context).enqueueUniqueWork(
            "flush_wear_health_outbox",
            ExistingWorkPolicy.APPEND_OR_REPLACE,
            request,
        )
    }

    fun flushBlocking(context: Context): Boolean {
        val database = database(context).readableDatabase
        val pending = mutableListOf<Pair<String, String>>()
        database.query(
            TABLE,
            arrayOf(COLUMN_BATCH_ID, COLUMN_PAYLOAD),
            null,
            null,
            null,
            null,
            "$COLUMN_CREATED_AT ASC",
        ).use { cursor ->
            while (cursor.moveToNext()) {
                pending += cursor.getString(0) to cursor.getString(1)
            }
        }

        var completed = true
        for ((batchId, body) in pending) {
            try {
                val request = PutDataMapRequest.create("/wmax/health-data/$batchId")
                    .apply { dataMap.putString("payload", body) }
                    .asPutDataRequest()
                    .setUrgent()
                Tasks.await(Wearable.getDataClient(context).putDataItem(request), 20, TimeUnit.SECONDS)
                database(context).writableDatabase.delete(
                    TABLE,
                    "$COLUMN_BATCH_ID = ?",
                    arrayOf(batchId),
                )
            } catch (_: Exception) {
                completed = false
            }
        }
        return completed
    }

    private fun enqueuePayloads(context: Context, payloads: List<String>): Boolean = synchronized(lock) {
        val db = database(context).writableDatabase
        val bytes = payloads.sumOf(::encodedSize).toLong()
        val queuedBytes = db.rawQuery(
            "SELECT COALESCE(SUM(LENGTH(CAST($COLUMN_PAYLOAD AS BLOB))), 0) FROM $TABLE",
            null,
        ).use { cursor -> if (cursor.moveToFirst()) cursor.getLong(0) else 0L }
        if (queuedBytes + bytes > MAX_QUEUED_BYTES) return false

        db.beginTransaction()
        try {
            for (body in payloads) {
                val values = ContentValues().apply {
                    put(COLUMN_BATCH_ID, JSONObject(body).getString("batch_id"))
                    put(COLUMN_PAYLOAD, body)
                    put(COLUMN_CREATED_AT, System.currentTimeMillis())
                }
                if (db.insertOrThrow(TABLE, null, values) < 0) return false
            }
            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
        true
    }

    private fun payload(
        source: String,
        samples: List<JSONObject>,
        exerciseSessions: JSONArray,
        collector: String,
    ): String {
        val sampleArray = JSONArray().also { array -> samples.forEach(array::put) }
        return JSONObject()
            .put("batch_id", UUID.randomUUID().toString())
            .put("source", source)
            .put("samples", sampleArray)
            .put("sleep_sessions", JSONArray())
            .put("exercise_sessions", exerciseSessions)
            .put("metadata", JSONObject().put("collector", collector))
            .toString()
    }

    private fun encodedSize(value: String): Int = value.toByteArray(Charsets.UTF_8).size

    private fun database(context: Context): OutboxDatabase = synchronized(lock) {
        val instance = helper ?: OutboxDatabase(context.applicationContext).also {
            helper = it
        }
        migrateLegacyQueue(context.applicationContext, instance.writableDatabase)
        instance
    }

    private fun migrateLegacyQueue(context: Context, db: SQLiteDatabase) {
        val prefs = context.getSharedPreferences(LEGACY_PREFS, Context.MODE_PRIVATE)
        if (prefs.getBoolean(LEGACY_MIGRATED, false)) return
        val oldPayloads = prefs.getStringSet(LEGACY_PAYLOADS, emptySet()).orEmpty()
        db.beginTransaction()
        try {
            for (body in oldPayloads) {
                val values = ContentValues().apply {
                    put(COLUMN_BATCH_ID, JSONObject(body).getString("batch_id"))
                    put(COLUMN_PAYLOAD, body)
                    put(COLUMN_CREATED_AT, System.currentTimeMillis())
                }
                db.insertWithOnConflict(TABLE, null, values, SQLiteDatabase.CONFLICT_IGNORE)
            }
            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
        prefs.edit().putBoolean(LEGACY_MIGRATED, true).commit()
    }

    private class OutboxDatabase(context: Context) : SQLiteOpenHelper(
        context,
        "wmax_health_outbox.db",
        null,
        1,
    ) {
        override fun onCreate(db: SQLiteDatabase) {
            db.execSQL(
                "CREATE TABLE $TABLE (" +
                    "$COLUMN_BATCH_ID TEXT PRIMARY KEY, " +
                    "$COLUMN_PAYLOAD TEXT NOT NULL, " +
                    "$COLUMN_CREATED_AT INTEGER NOT NULL)"
            )
        }

        override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit
    }

    private const val TABLE = "health_outbox"
    private const val COLUMN_BATCH_ID = "batch_id"
    private const val COLUMN_PAYLOAD = "payload"
    private const val COLUMN_CREATED_AT = "created_at"
    private const val LEGACY_PREFS = "wmax_health_outbox"
    private const val LEGACY_PAYLOADS = "payloads"
    private const val LEGACY_MIGRATED = "sqlite_migrated"
    private const val MAX_SAMPLES_PER_ITEM = 200
    private const val MAX_DATA_ITEM_BYTES = 80 * 1024
    private const val MAX_QUEUED_BYTES = 16L * 1024 * 1024
}
