package uz.nazorat.watch.sensor

import android.content.Context
import android.util.Log
import androidx.concurrent.futures.await
import androidx.health.services.client.HealthServices
import androidx.health.services.client.MeasureCallback
import androidx.health.services.client.MeasureClient
import androidx.health.services.client.data.Availability
import androidx.health.services.client.data.DataPointContainer
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.DeltaDataType
import androidx.health.services.client.data.SampleDataPoint
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.runBlocking

/**
 * Manages Wear OS Health Services sensors (Heart Rate, SpO2, Steps, Worn status).
 * Uses androidx.health:health-services-client.
 */
class HealthServicesManager(private val context: Context) {

    private val healthServicesClient = HealthServices.getClient(context)
    private val measureClient: MeasureClient = healthServicesClient.measureClient

    companion object {
        private const val TAG = "HealthServicesManager"
    }

    /**
     * Checks if Heart Rate sensor is supported on this hardware.
     */
    suspend fun isHeartRateSupported(): Boolean {
        return try {
            val capabilities = measureClient.getCapabilitiesAsync().await()
            DataType.HEART_RATE_BPM in capabilities.supportedDataTypesMeasure
        } catch (e: Exception) {
            Log.w(TAG, "Failed to get capabilities: ${e.message}")
            false
        }
    }

    /**
     * Continuous Heart Rate Flow emitting BPM values and availability.
     */
    fun heartRateFlow(): Flow<MeasureEvent> = callbackFlow {
        val callback = object : MeasureCallback {
            override fun onAvailabilityChanged(dataType: DeltaDataType<*, *>, availability: Availability) {
                Log.d(TAG, "Availability changed for $dataType: $availability")
                trySend(MeasureEvent.AvailabilityUpdate(availability.toString()))
            }

            override fun onDataReceived(data: DataPointContainer) {
                val hrPoints = data.getData(DataType.HEART_RATE_BPM)
                for (point in hrPoints) {
                    val bpm = point.value
                    Log.d(TAG, "Heart rate data point: $bpm bpm")
                    trySend(MeasureEvent.HeartRate(bpm))
                }

                // Check for SpO2 if present
                val spo2Points = data.getData(DataType.SPO2)
                for (point in spo2Points) {
                    val spo2 = point.value
                    Log.d(TAG, "SpO2 data point: $spo2 %")
                    trySend(MeasureEvent.SpO2(spo2))
                }
            }
        }

        try {
            measureClient.registerMeasureCallback(DataType.HEART_RATE_BPM, callback)
            Log.i(TAG, "Registered MeasureCallback for HEART_RATE_BPM")
        } catch (e: Exception) {
            Log.e(TAG, "Error registering callback: ${e.message}")
            close(e)
        }

        awaitClose {
            runBlocking {
                try {
                    measureClient.unregisterMeasureCallbackAsync(DataType.HEART_RATE_BPM, callback).await()
                    Log.i(TAG, "Unregistered MeasureCallback")
                } catch (e: Exception) {
                    Log.w(TAG, "Error unregistering: ${e.message}")
                }
            }
        }
    }
}

sealed class MeasureEvent {
    data class HeartRate(val bpm: Double) : MeasureEvent()
    data class SpO2(val percentage: Double) : MeasureEvent()
    data class AvailabilityUpdate(val availability: String) : MeasureEvent()
}
