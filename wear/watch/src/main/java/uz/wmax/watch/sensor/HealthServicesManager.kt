package uz.wmax.watch.sensor

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Log
import androidx.health.services.client.HealthServices
import androidx.health.services.client.MeasureCallback
import androidx.health.services.client.MeasureClient
import androidx.health.services.client.data.Availability
import androidx.health.services.client.data.DataPointContainer
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.DeltaDataType
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.guava.await
import kotlinx.coroutines.runBlocking

/**
 * Manages Wear OS Health Services sensors and Android hardware off-body detection.
 * Accurately analyzes whether the watch is on the patient's wrist or removed.
 */
class HealthServicesManager(private val context: Context) {

    private val healthServicesClient = HealthServices.getClient(context)
    private val measureClient: MeasureClient = healthServicesClient.measureClient
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as? SensorManager

    companion object {
        private const val TAG = "HealthServicesManager"
        // Standard Android constant for low-latency off-body detection sensor
        const val SENSOR_TYPE_LOW_LATENCY_OFFBODY = 34
    }

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
     * Combined Sensor Flow: Heart Rate, SpO2, and Hardware Off-Body Detection.
     */
    fun sensorEventFlow(): Flow<MeasureEvent> = callbackFlow {
        // 1. Android Hardware Low-Latency Off-Body Detector
        val offbodySensor = sensorManager?.getDefaultSensor(SENSOR_TYPE_LOW_LATENCY_OFFBODY)
        val heartRateSensor = sensorManager?.getDefaultSensor(Sensor.TYPE_HEART_RATE)

        val sensorListener = object : SensorEventListener {
            override fun onSensorChanged(event: SensorEvent?) {
                if (event == null) return
                if (event.sensor.type == SENSOR_TYPE_LOW_LATENCY_OFFBODY) {
                    val isWorn = event.values[0] == 1.0f
                    Log.d(TAG, "Off-body sensor event: isWorn=$isWorn")
                    trySend(MeasureEvent.WornStatus(isWorn))
                } else if (event.sensor.type == Sensor.TYPE_HEART_RATE) {
                    val bpm = event.values.firstOrNull()?.toDouble()
                    if (bpm != null && bpm > 0.0 && event.accuracy != SensorManager.SENSOR_STATUS_NO_CONTACT) {
                        Log.d(TAG, "Heart-rate sample from SensorManager: $bpm")
                        trySend(MeasureEvent.WornStatus(true))
                        trySend(MeasureEvent.HeartRate(bpm))
                    }
                    if (event.accuracy == SensorManager.SENSOR_STATUS_NO_CONTACT) {
                        trySend(MeasureEvent.WornStatus(false))
                    }
                }
            }

            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
                if (accuracy == SensorManager.SENSOR_STATUS_NO_CONTACT) {
                    trySend(MeasureEvent.WornStatus(false))
                } else if (accuracy >= SensorManager.SENSOR_STATUS_ACCURACY_LOW) {
                    trySend(MeasureEvent.WornStatus(true))
                }
            }
        }

        if (offbodySensor != null) {
            Log.i(TAG, "Registering off-body sensor: ${offbodySensor.name}")
            sensorManager?.registerListener(sensorListener, offbodySensor, SensorManager.SENSOR_DELAY_NORMAL)
        }
        if (heartRateSensor != null && heartRateSensor != offbodySensor) {
            Log.i(TAG, "Registering heart-rate sensor: ${heartRateSensor.name}")
            sensorManager?.registerListener(sensorListener, heartRateSensor, SensorManager.SENSOR_DELAY_FASTEST)
        }

        // 2. Health Services MeasureClient for Heart Rate & Contact Availability
        val callback = object : MeasureCallback {
            override fun onAvailabilityChanged(dataType: DeltaDataType<*, *>, availability: Availability) {
                Log.d(TAG, "Availability changed for $dataType: $availability")
                val availStr = availability.toString().uppercase()
                if (availStr.contains("NO_CONTACT") || availStr.contains("UNAVAILABLE")) {
                    trySend(MeasureEvent.WornStatus(false))
                } else if (availStr.contains("ACQUIRING") || availStr.contains("AVAILABLE")) {
                    trySend(MeasureEvent.WornStatus(true))
                }
                trySend(MeasureEvent.AvailabilityUpdate(availability.toString()))
            }

            override fun onDataReceived(data: DataPointContainer) {
                val hrPoints = data.getData(DataType.HEART_RATE_BPM)
                for (point in hrPoints) {
                    val bpm = point.value
                    trySend(MeasureEvent.WornStatus(true))
                    trySend(MeasureEvent.HeartRate(bpm))
                }
            }
        }

        try {
            measureClient.registerMeasureCallback(DataType.HEART_RATE_BPM, callback)
            Log.i(TAG, "Registered MeasureCallback for HEART_RATE_BPM")
        } catch (e: Exception) {
            Log.e(TAG, "Error registering callback: ${e.message}")
        }

        awaitClose {
            sensorManager?.unregisterListener(sensorListener)
            runBlocking {
                try {
                    measureClient.unregisterMeasureCallbackAsync(DataType.HEART_RATE_BPM, callback).await()
                } catch (e: Exception) {
                    Log.w(TAG, "Error unregistering: ${e.message}")
                }
            }
        }
    }

    fun heartRateFlow(): Flow<MeasureEvent> = sensorEventFlow()
}

sealed class MeasureEvent {
    data class HeartRate(val bpm: Double) : MeasureEvent()
    data class SpO2(val percentage: Double) : MeasureEvent()
    data class WornStatus(val isWorn: Boolean) : MeasureEvent()
    data class AvailabilityUpdate(val availability: String) : MeasureEvent()
}
