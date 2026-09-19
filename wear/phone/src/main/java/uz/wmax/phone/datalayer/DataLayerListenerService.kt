package uz.wmax.phone.datalayer

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
import uz.wmax.phone.data.db.AppDatabase
import uz.wmax.phone.data.db.ReadingEntity
import uz.wmax.phone.sync.SyncWorker

class DataLayerListenerService : WearableListenerService() {

    private val job = SupervisorJob()
    private val scope = CoroutineScope(Dispatchers.IO + job)
    private val gson = Gson()

    companion object {
        private const val TAG = "DataLayerService"
        const val PATH_READING_BATCH = "/wmax/reading_batch"
        const val PATH_SOS = "/wmax/sos"
        const val DEFAULT_PATIENT_ID = "11111111-1111-1111-1111-111111111111"
    }

    override fun onMessageReceived(messageEvent: MessageEvent) {
        if (messageEvent.path == PATH_SOS) {
            val jsonString = String(messageEvent.data, Charsets.UTF_8)
            Log.w(TAG, "🚨 Received emergency SOS from watch: $jsonString")
            scope.launch {
                try {
                    val jsonObj = JSONObject(jsonString)
                    val prefs = getSharedPreferences("wmax_phone_prefs", Context.MODE_PRIVATE)
                    val configuredPatientId = prefs.getString("patient_id", null)
                        ?: throw IllegalStateException("Patient is not authenticated")
                    val patientId = jsonObj.optString("patient_id").ifBlank { configuredPatientId }
                    val baseUrl = prefs.getString("backend_url", uz.wmax.phone.network.WmaxApiService.DEFAULT_BASE_URL)
                        ?: uz.wmax.phone.network.WmaxApiService.DEFAULT_BASE_URL
                    val accessToken = prefs.getString("access_token", null)
                        ?: throw IllegalStateException("Patient access token is missing")
                    val api = uz.wmax.phone.network.WmaxApiService.create(baseUrl)
                    val response = api.raiseSos(
                        authorization = "Bearer $accessToken",
                        req = uz.wmax.phone.network.SosRaisePayload(
                            patient_id = patientId,
                            source = "watch_button",
                            device_lat = if (jsonObj.has("device_lat")) jsonObj.optDouble("device_lat") else null,
                            device_lon = if (jsonObj.has("device_lon")) jsonObj.optDouble("device_lon") else null
                        )
                    )
                    if (!response.isSuccessful) {
                        throw IllegalStateException("SOS API returned HTTP ${response.code()}")
                    }
                    Log.i(TAG, "🚨 SOS successfully forwarded to WMAX backend API")
                } catch (e: Exception) {
                    Log.e(TAG, "Failed forwarding SOS to backend: ${e.message}", e)
                }
            }
        } else if (messageEvent.path == PATH_READING_BATCH) {
            val jsonString = String(messageEvent.data, Charsets.UTF_8)
            Log.i(TAG, "Received reading batch from watch: $jsonString")

            scope.launch {
                try {
                    val jsonObj = JSONObject(jsonString)
                    val ts = jsonObj.optString("ts", "")
                    val deviceId = "GALAXY-WATCH-" + messageEvent.sourceNodeId.takeLast(6)

                    val prefs = getSharedPreferences("wmax_phone_prefs", Context.MODE_PRIVATE)
                    val patientId = prefs.getString("patient_id", null)
                        ?: throw IllegalStateException("Reading rejected: patient is not authenticated")

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
