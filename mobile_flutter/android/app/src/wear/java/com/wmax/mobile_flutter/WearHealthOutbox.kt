package com.wmax.mobile_flutter

import android.content.Context
import android.content.SharedPreferences
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.PutDataMapRequest
import com.google.android.gms.wearable.Wearable
import org.json.JSONObject
import java.util.HashSet
import java.util.concurrent.TimeUnit

object WearHealthOutbox {
    private const val PREFS = "wmax_health_outbox"
    private const val PAYLOADS = "payloads"
    private val lock = Any()

    fun enqueue(context: Context, payload: String): Boolean = synchronized(lock) {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val queued = HashSet(prefs.getStringSet(PAYLOADS, emptySet()) ?: emptySet())
        queued.add(payload)
        prefs.edit().putStringSet(PAYLOADS, queued).commit()
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
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val payloads = synchronized(lock) {
            ArrayList(prefs.getStringSet(PAYLOADS, emptySet()) ?: emptySet())
        }
        var completed = true
        for (payload in payloads) {
            try {
                val batchId = JSONObject(payload).getString("batch_id")
                val request = PutDataMapRequest.create("/wmax/health-data/$batchId")
                    .apply { dataMap.putString("payload", payload) }
                    .asPutDataRequest()
                    .setUrgent()
                Tasks.await(Wearable.getDataClient(context).putDataItem(request), 20, TimeUnit.SECONDS)
                synchronized(lock) {
                    val current = HashSet(prefs.getStringSet(PAYLOADS, emptySet()) ?: emptySet())
                    current.remove(payload)
                    prefs.edit().putStringSet(PAYLOADS, current).commit()
                }
            } catch (_: Exception) {
                completed = false
            }
        }
        return completed
    }
}
