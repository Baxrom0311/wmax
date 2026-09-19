package uz.wmax.phone.sync

import android.content.Context
import android.util.Log
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.google.gson.Gson
import uz.wmax.phone.data.db.AppDatabase
import uz.wmax.phone.data.model.IngestBatchRequest
import uz.wmax.phone.data.model.ReadingInModel
import uz.wmax.phone.network.WmaxApiService
import java.util.concurrent.TimeUnit

class SyncWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    companion object {
        private const val TAG = "SyncWorker"
        private const val UNIQUE_WORK_NAME = "WmaxIngestSync"

        fun enqueueSync(context: Context, expedited: Boolean = false) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val requestBuilder = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    15,
                    TimeUnit.SECONDS
                )

            WorkManager.getInstance(context).enqueueUniqueWork(
                UNIQUE_WORK_NAME,
                ExistingWorkPolicy.REPLACE,
                requestBuilder.build()
            )
            Log.d(TAG, "Enqueued sync work request")
        }
    }

    override suspend fun doWork(): Result {
        val database = AppDatabase.getInstance(applicationContext)
        val dao = database.readingDao()
        val gson = Gson()

        val unsyncedList = dao.getUnsyncedReadings(limit = 500)
        if (unsyncedList.isEmpty()) {
            Log.i(TAG, "No unsynced readings in buffer.")
            return Result.success()
        }

        Log.i(TAG, "Preparing to send batch of ${unsyncedList.size} readings...")

        val patientId = unsyncedList.first().patientId
        val deviceId = unsyncedList.first().deviceId
        val sameAssignment = unsyncedList.filter {
            it.patientId == patientId && it.deviceId == deviceId
        }

        val readings = mutableListOf<ReadingInModel>()
        val ids = mutableListOf<Long>()

        for (entity in sameAssignment) {
            try {
                val reading = gson.fromJson(entity.payloadJson, ReadingInModel::class.java)
                readings.add(reading)
                ids.add(entity.id)
            } catch (e: Exception) {
                Log.e(TAG, "Failed parsing payload JSON for entity id ${entity.id}: ${e.message}")
            }
        }

        if (readings.isEmpty()) {
            return Result.success()
        }

        val request = IngestBatchRequest(
            patientId = patientId,
            deviceId = deviceId,
            readings = readings
        )

        // Read custom base URL and API key from SharedPreferences if configured by user
        val prefs = applicationContext.getSharedPreferences("wmax_phone_prefs", Context.MODE_PRIVATE)
        val baseUrl = prefs.getString("backend_url", WmaxApiService.DEFAULT_BASE_URL) ?: WmaxApiService.DEFAULT_BASE_URL
        val apiKey = prefs.getString("ingest_api_key", null)
        val apiService = WmaxApiService.create(baseUrl, apiKey)

        return try {
            val response = apiService.ingestBatch(request)
            if (response.isSuccessful && response.body() != null) {
                val result = response.body()!!
                Log.i(
                    TAG,
                    "Batch uploaded successfully: accepted=${result.accepted}, duplicates=${result.duplicates}, level=${result.latestLevel}"
                )
                dao.markAsSynced(ids)
                Result.success()
            } else if (response.code() in 400..499) {
                Log.e(TAG, "Permanent ingest failure HTTP ${response.code()}; check login and device key")
                Result.failure()
            } else {
                Log.w(
                    TAG,
                    "Server responded with error ${response.code()}: ${response.errorBody()?.string()}"
                )
                Result.retry()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Network error during sync: ${e.message}")
            Result.retry()
        }
    }
}
