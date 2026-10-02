package com.wmax.mobile_flutter

import android.content.Context
import android.content.pm.PackageManager
import android.Manifest
import androidx.core.content.ContextCompat
import androidx.health.services.client.HealthServices
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.PassiveListenerConfig
import java.util.concurrent.TimeUnit
import java.util.concurrent.Executor

object WearHealthServices {
    private fun listenerConfig(context: Context, supported: Set<DataType<*, *>>): PassiveListenerConfig {
        val requested: MutableSet<DataType<*, *>> = mutableSetOf(DataType.HEART_RATE_BPM)
        val canReadActivity = ContextCompat.checkSelfPermission(context, Manifest.permission.ACTIVITY_RECOGNITION) ==
            PackageManager.PERMISSION_GRANTED
        if (canReadActivity) {
            requested.addAll(
                setOf(DataType.STEPS, DataType.STEPS_DAILY, DataType.FLOORS, DataType.ELEVATION_GAIN)
                    .filter { it in supported },
            )
        }
        return PassiveListenerConfig.builder()
            .setDataTypes(requested)
            .setShouldUserActivityInfoBeRequested(canReadActivity)
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
            val config = listenerConfig(context, capabilities.supportedDataTypesPassiveMonitoring)
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
                        val config = listenerConfig(context, capabilities.supportedDataTypesPassiveMonitoring)
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
