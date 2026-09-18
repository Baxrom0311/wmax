package uz.nazorat.phone.datalayer

import android.content.Context
import android.util.Log
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.WearableListenerService
import com.google.gson.Gson
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.json.JSONObject
import uz.nazorat.phone.data.db.AppDatabase
import uz.nazorat.phone.data.db.ReadingEntity
import uz.nazorat.phone.sync.SyncWorker

class DataLayerListenerService : WearableListenerService() {

    private val job = SupervisorJob()
    private val scope = CoroutineScope(Dispatchers.IO + job)
    private val gson = Gson()

    companion object {
        private const val TAG = "DataLayerService"
        const val PATH_READING_BATCH = "/nazorat/reading_batch"
        const val DEFAULT_PATIENT_ID = "11111111-1111-1111-1111-111111111111"
    }

    override fun onMessageReceived(messageEvent: MessageEvent) {
        if (messageEvent.path == PATH_READING_BATCH) {
            val jsonString = String(messageEvent.data, Charsets.UTF_8)
            Log.i(TAG, "Received reading batch from watch: $jsonString")

            scope.launch {
                try {
                    val jsonObj = JSONObject(jsonString)
                    val ts = jsonObj.optString("ts", "")
                    val deviceId = "GALAXY-WATCH-" + messageEvent.sourceNodeId.takeLast(6)

                    val prefs = getSharedPreferences("nazorat_phone_prefs", Context.MODE_PRIVATE)
                    val patientId = prefs.getString("patient_id", DEFAULT_PATIENT_ID) ?: DEFAULT_PATIENT_ID

                    val entity = ReadingEntity(
                        ts = ts,
                        patientId = patientId,
                        deviceId = deviceId,
                        payloadJson = jsonString,
                        isSynced = false
                    )

                    val dao = AppDatabase.getInstance(applicationContext).readingDao()
                    dao.insertReading(entity)
                    Log.d(TAG, "Buffered reading in Room DB for patient $patientId at $ts")

                    // Trigger expedited background sync
                    SyncWorker.enqueueSync(applicationContext, expedited = true)
                } catch (e: Exception) {
                    Log.e(TAG, "Error handling incoming reading message: ${e.message}", e)
                }
            }
        } else {
            super.onMessageReceived(messageEvent)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        job.cancel()
    }
}
