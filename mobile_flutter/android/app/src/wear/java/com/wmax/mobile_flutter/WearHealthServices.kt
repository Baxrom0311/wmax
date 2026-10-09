package com.wmax.mobile_flutter

import android.content.Context
import android.content.pm.PackageManager
import android.Manifest
import androidx.core.content.ContextCompat
import androidx.health.services.client.HealthServices
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.ExerciseType
import androidx.health.services.client.data.HealthEvent
import androidx.health.services.client.data.PassiveMonitoringCapabilities
import androidx.health.services.client.data.PassiveListenerConfig
import java.util.concurrent.TimeUnit
import java.util.concurrent.Executor

object WearHealthServices {
    @JvmStatic
    fun capabilitySnapshot(context: Context): Map<String, Any> {
        val healthClient = HealthServices.getClient(context)
        val passive = healthClient.passiveMonitoringClient
            .getCapabilitiesAsync().get(25, TimeUnit.SECONDS)
        val exercise = healthClient.exerciseClient
            .getCapabilitiesAsync().get(25, TimeUnit.SECONDS)
        val exerciseTypes = exercise.supportedExerciseTypes.map { type ->
            val capabilities = exercise.getExerciseTypeCapabilities(type)
            mapOf(
                "type" to type.name,
                "data_types" to capabilities.supportedDataTypes.map { it.toString() },
                "supports_auto_pause" to capabilities.supportsAutoPauseAndResume,
            )
        }
        return mapOf(
            "wear_os" to true,
            "passive_data_types" to passive.supportedDataTypesPassiveMonitoring
                .map { it.toString() },
            "exercise_types" to exerciseTypes,
        )
    }

    private fun listenerConfig(context: Context, capabilities: PassiveMonitoringCapabilities): PassiveListenerConfig {
        val supported = capabilities.supportedDataTypesPassiveMonitoring
        val requested: MutableSet<DataType<*, *>> = mutableSetOf(DataType.HEART_RATE_BPM)
        val canReadActivity = ContextCompat.checkSelfPermission(context, Manifest.permission.ACTIVITY_RECOGNITION) ==
            PackageManager.PERMISSION_GRANTED
        if (canReadActivity) {
            requested.addAll(
                setOf(
                    DataType.STEPS,
                    DataType.STEPS_DAILY,
                    DataType.FLOORS,
                    DataType.ELEVATION_GAIN,
                    DataType.CALORIES_DAILY,
                    DataType.DISTANCE_DAILY,
                    DataType.VO2_MAX,
                ).filter { it in supported },
            )
        }
        val healthEvents = if (
            canReadActivity &&
            HealthEvent.Type.FALL_DETECTED in capabilities.supportedHealthEventTypes
        ) {
            setOf(HealthEvent.Type.FALL_DETECTED)
        } else {
            emptySet()
        }
        return PassiveListenerConfig.builder()
            .setDataTypes(requested)
            .setShouldUserActivityInfoBeRequested(canReadActivity)
            .setHealthEventTypes(healthEvents)
            .build()
    }

    @JvmStatic
    fun registerBlocking(context: Context): String? {
        return try {
            val client = HealthServices.getClient(context).passiveMonitoringClient
            val capabilities = client.getCapabilitiesAsync().get(25, TimeUnit.SECONDS)
            if (DataType.HEART_RATE_BPM !in capabilities.supportedDataTypesPassiveMonitoring) {
                return "HEART_RATE_UNSUPPORTED"
            }
            val config = listenerConfig(context, capabilities)
            client.setPassiveListenerServiceAsync(WmaxPassiveHealthService::class.java, config)
                .get(25, TimeUnit.SECONDS)
            null
        } catch (error: Exception) {
            error.message ?: "HEALTH_SERVICES_REGISTRATION_FAILED"
        }
    }

    @JvmStatic
    fun register(context: Context, callback: WearHealthRegistrationCallback) {
        val client = HealthServices.getClient(context).passiveMonitoringClient
        val capabilitiesFuture = client.getCapabilitiesAsync()
        capabilitiesFuture.addListener(
            {
                try {
                    val capabilities = capabilitiesFuture.get()
                    if (DataType.HEART_RATE_BPM !in capabilities.supportedDataTypesPassiveMonitoring) {
                        callback.onComplete(false, "HEART_RATE_UNSUPPORTED")
                    } else {
                        val config = listenerConfig(context, capabilities)
                        val registration = client.setPassiveListenerServiceAsync(
                            WmaxPassiveHealthService::class.java,
                            config,
                        )
                        registration.addListener(
                            {
                                try {
                                    registration.get()
                                    callback.onComplete(true, null)
                                } catch (error: Exception) {
                                    callback.onComplete(
                                        false,
                                        error.message ?: "HEALTH_SERVICES_REGISTRATION_FAILED",
                                    )
                                }
                            },
                            Executor { command -> command.run() },
                        )
                    }
                } catch (error: Exception) {
                    callback.onComplete(false, error.message ?: "HEALTH_SERVICES_UNAVAILABLE")
                }
            },
            Executor { command -> command.run() },
        )
    }
}
