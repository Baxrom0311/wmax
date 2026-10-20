package com.wmax.mobile_flutter

import android.content.Context
import android.util.Log
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.Worker
import androidx.work.WorkerParameters
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.TimeUnit

/**
 * Uploads the native wearable queue to the server while the Flutter UI is
 * closed. Batches stay queued until the server answers 2xx, so a fall or SOS
 * received from the watch is retried until it is delivered.
 */
class WearQueueUploadWorker(
    context: Context,
    params: WorkerParameters,
) : Worker(context, params) {
    override fun doWork(): Result {
        val token = try {
            DeviceCredentialVault.read(applicationContext)
        } catch (_: Exception) {
            Log.w(TAG, "Device credential could not be read; upload waits for re-pairing")
            null
        }
        // Not paired yet: keep the queue; pairing schedules this worker again.
        if (token.isNullOrBlank()) return Result.success()

        val endpoint = URL("${baseUrl(applicationContext)}/api/v1/ingest/health-data")
        var retry = false
        for (payload in WmaxWearDataListenerService.getQueuedPayloads(applicationContext)) {
            if (isStopped) return Result.retry()
            when (upload(endpoint, token, payload)) {
                Outcome.DELIVERED -> acknowledge(payload)
                Outcome.UNPROCESSABLE -> {
                    // The server will never accept this body; drop it so it does not
                    // keep the radio awake forever.
                    Log.e(TAG, "Dropping health batch the server cannot process")
                    acknowledge(payload)
                }
                Outcome.UNAUTHORIZED -> {
                    Log.w(TAG, "Device token rejected; queue kept until the device is paired again")
                    return Result.success()
                }
                Outcome.RETRY -> retry = true
            }
        }
        return if (retry) Result.retry() else Result.success()
    }

    private fun acknowledge(payload: String) {
        WmaxWearDataListenerService.acknowledgePayloads(applicationContext, arrayListOf(payload))
    }

    private fun upload(endpoint: URL, token: String, payload: String): Outcome {
        val connection = endpoint.openConnection() as HttpURLConnection
        return try {
            connection.requestMethod = "POST"
            connection.connectTimeout = 15_000
            connection.readTimeout = 20_000
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Authorization", "Bearer $token")
            connection.outputStream.use { it.write(payload.toByteArray(Charsets.UTF_8)) }
            classify(connection.responseCode)
        } catch (_: IOException) {
            Outcome.RETRY
        } finally {
            connection.disconnect()
        }
    }

    enum class Outcome { DELIVERED, UNPROCESSABLE, UNAUTHORIZED, RETRY }

    companion object {
        private const val TAG = "WmaxWearUpload"
        private const val ONE_TIME_WORK = "upload_wear_queue"
        private const val PERIODIC_WORK = "upload_wear_queue_periodic"
        private const val DEFAULT_BASE_URL = "https://wmax.boos.uz"

        /**
         * 2xx means the server stored the batch; samples it refused (no device
         * assignment, revoked consent) are its final answer, so they are not resent.
         */
        @JvmStatic
        fun classify(status: Int): Outcome = when (status) {
            in 200..299 -> Outcome.DELIVERED
            401, 403 -> Outcome.UNAUTHORIZED
            400, 413, 422 -> Outcome.UNPROCESSABLE
            else -> Outcome.RETRY
        }

        /** Same rule as SessionService.getBaseUrl on the Dart side. */
        @JvmStatic
        fun normalizeBaseUrl(saved: String?): String {
            val value = saved?.trim().orEmpty()
            if (value.isEmpty() || value.contains("10.0.2.2") || value.contains("127.0.0.1")) {
                return DEFAULT_BASE_URL
            }
            return value.trimEnd('/')
        }

        private fun baseUrl(context: Context): String = normalizeBaseUrl(
            context.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
                .getString("flutter.wmax_base_url", null),
        )

        @JvmStatic
        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()
            val workManager = WorkManager.getInstance(context.applicationContext)
            workManager.enqueueUniqueWork(
                ONE_TIME_WORK,
                ExistingWorkPolicy.APPEND_OR_REPLACE,
                OneTimeWorkRequestBuilder<WearQueueUploadWorker>()
                    .setConstraints(constraints)
                    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                    .build(),
            )
            // Safety net if a one-time run is lost (force stop, reboot).
            workManager.enqueueUniquePeriodicWork(
                PERIODIC_WORK,
                ExistingPeriodicWorkPolicy.KEEP,
                PeriodicWorkRequestBuilder<WearQueueUploadWorker>(15, TimeUnit.MINUTES)
                    .setConstraints(constraints)
                    .build(),
            )
        }
    }
}
