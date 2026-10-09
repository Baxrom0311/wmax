package com.wmax.mobile_flutter

import android.content.Context
import android.os.BatteryManager
import android.os.SystemClock
import androidx.health.services.client.PassiveListenerService
import androidx.health.services.client.data.DataPointContainer
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.HealthEvent
import androidx.health.services.client.data.HeartRateAccuracy
import androidx.health.services.client.data.UserActivityInfo
import androidx.health.services.client.data.UserActivityState
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant

class WmaxPassiveHealthService : PassiveListenerService() {
    override fun onHealthEventReceived(event: HealthEvent) {
        if (event.type != HealthEvent.Type.FALL_DETECTED) return
        val at = event.eventTime
        val samples = JSONArray().put(
            JSONObject()
                .put("metric", "fall_detected")
                .put("recorded_at", at.toString())
                .put("value_text", "fall_detected")
                .put("source_record_id", "fall-${at.toEpochMilli()}"),
        )
        enqueueBatch(samples)
    }

    override fun onUserActivityInfoReceived(info: UserActivityInfo) {
        val state = when (info.userActivityState) {
            UserActivityState.USER_ACTIVITY_ASLEEP -> "asleep"
            UserActivityState.USER_ACTIVITY_EXERCISE -> "exercise"
            UserActivityState.USER_ACTIVITY_PASSIVE -> "passive"
            else -> return
        }
        val changedAt = info.stateChangeTime
        val prefs = getSharedPreferences("wmax_health_state", Context.MODE_PRIVATE).edit()
        prefs.putString("activity_state", state)
            .putString("activity_state_at", changedAt.toString())
        if (state == "asleep") {
            prefs.putString("sleep_stage", "asleep")
                .putString("sleep_at", changedAt.toString())
        }
        prefs.apply()

        val samples = JSONArray().put(
            JSONObject()
                .put("metric", "activity_state")
                .put("recorded_at", changedAt.toString())
                .put("value_text", state)
                .put("source_record_id", "activity-state-${changedAt.toEpochMilli()}"),
        )
        enqueueBatch(samples)
    }

    override fun onNewDataPointsReceived(dataPoints: DataPointContainer) {
        val bootInstant = Instant.ofEpochMilli(
            System.currentTimeMillis() - SystemClock.elapsedRealtime(),
        )
        val samples = JSONArray()
        var latestDailySteps: Long? = null
        var latestDailyStepsAt: Instant? = null
        fun appendInterval(
            metric: String,
            value: Number,
            unit: String,
            start: Instant,
            end: Instant,
            dailyCumulative: Boolean = false,
        ) {
            val sample = JSONObject()
                .put("metric", metric)
                .put("recorded_at", end.toString())
                .put("started_at", start.toString())
                .put("ended_at", end.toString())
                .put("value_num", value)
                .put("unit", unit)
                .put("source_record_id", "$metric-${end.toEpochMilli()}")
                .put("quality", 1.0)
            if (dailyCumulative) {
                // *_DAILY types are running totals since midnight, not deltas.
                sample.put("metadata", JSONObject().put("aggregation", "daily_cumulative"))
            }
            samples.put(sample)
        }
        var latestHeartRate: Double? = null
        var latestTimestamp: Instant? = null
        for (point in dataPoints.getData(DataType.HEART_RATE_BPM)) {
            val timestamp = point.getTimeInstant(bootInstant)
            val sensorStatus = (point.accuracy as? HeartRateAccuracy)?.sensorStatus
            val quality = heartRateQuality(sensorStatus)
            if (sensorStatus == HeartRateAccuracy.SensorStatus.NO_CONTACT) {
                // The watch is off the wrist; report that instead of a 0 bpm reading.
                samples.put(
                    JSONObject()
                        .put("metric", "worn_state")
                        .put("recorded_at", timestamp.toString())
                        .put("value_text", "not_worn")
                        .put("source_record_id", "worn-${timestamp.toEpochMilli()}"),
                )
                continue
            }
            if ((quality == null || quality >= 0.5) &&
                (latestTimestamp == null || timestamp.isAfter(latestTimestamp))
            ) {
                latestHeartRate = point.value
                latestTimestamp = timestamp
            }
            val sample = JSONObject()
                .put("metric", "heart_rate_bpm")
                .put("recorded_at", timestamp.toString())
                .put("value_num", point.value)
                .put("unit", "bpm")
                .put("source_record_id", "hr-${timestamp.toEpochMilli()}")
            if (quality != null) sample.put("quality", quality)
            if (sensorStatus != null) {
                sample.put("metadata", JSONObject().put("sensor_status", sensorStatus.toString()))
            }
            samples.put(sample)
        }
        for (point in dataPoints.getData(DataType.STEPS)) {
            appendInterval(
                "steps",
                point.value,
                "steps",
                point.getStartInstant(bootInstant),
                point.getEndInstant(bootInstant),
            )
        }
        for (point in dataPoints.getData(DataType.STEPS_DAILY)) {
            val end = point.getEndInstant(bootInstant)
            if (latestDailyStepsAt == null || end.isAfter(latestDailyStepsAt)) {
                latestDailySteps = point.value
                latestDailyStepsAt = end
            }
            appendInterval(
                "daily_steps",
                point.value,
                "steps",
                point.getStartInstant(bootInstant),
                end,
                dailyCumulative = true,
            )
        }
        for (point in dataPoints.getData(DataType.FLOORS)) {
            appendInterval(
                "floors",
                point.value,
                "floors",
                point.getStartInstant(bootInstant),
                point.getEndInstant(bootInstant),
            )
        }
        for (point in dataPoints.getData(DataType.ELEVATION_GAIN)) {
            appendInterval(
                "elevation_gain_m",
                point.value,
                "m",
                point.getStartInstant(bootInstant),
                point.getEndInstant(bootInstant),
            )
        }
        for (point in dataPoints.getData(DataType.CALORIES_DAILY)) {
            appendInterval(
                "total_calories_kcal",
                point.value,
                "kcal",
                point.getStartInstant(bootInstant),
                point.getEndInstant(bootInstant),
                dailyCumulative = true,
            )
        }
        for (point in dataPoints.getData(DataType.DISTANCE_DAILY)) {
            appendInterval(
                "distance_m",
                point.value,
                "m",
                point.getStartInstant(bootInstant),
                point.getEndInstant(bootInstant),
                dailyCumulative = true,
            )
        }
        var latestVo2: Double? = null
        var latestVo2At: Instant? = null
        for (point in dataPoints.getData(DataType.VO2_MAX)) {
            val timestamp = point.getTimeInstant(bootInstant)
            latestVo2 = point.value
            latestVo2At = timestamp
            samples.put(
                JSONObject()
                    .put("metric", "vo2_max_ml_kg_min")
                    .put("recorded_at", timestamp.toString())
                    .put("value_num", point.value)
                    .put("unit", "mL/kg/min")
                    .put("source_record_id", "vo2-${timestamp.toEpochMilli()}")
                    .put("quality", 1.0),
            )
        }
        val batteryManager = getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
        val batteryPct = batteryManager?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: -1
        if (batteryPct in 0..100) {
            samples.put(
                JSONObject()
                    .put("metric", "battery_pct")
                    .put("recorded_at", Instant.now().toString())
                    .put("value_num", batteryPct)
                    .put("unit", "%")
                    .put("source_record_id", "battery-${System.currentTimeMillis()}")
                    .put("quality", 1.0),
            )
        }
        if (samples.length() == 0) return

        val state = getSharedPreferences("wmax_health_state", MODE_PRIVATE).edit()
        if (latestHeartRate != null && latestTimestamp != null) {
            state.putFloat("heart_rate_bpm", latestHeartRate.toFloat())
                .putString("heart_rate_at", latestTimestamp.toString())
        }
        if (latestDailySteps != null && latestDailyStepsAt != null) {
            state.putLong("daily_steps", latestDailySteps)
                .putString("daily_steps_at", latestDailyStepsAt.toString())
        }
        if (latestVo2 != null && latestVo2At != null) {
            state.putFloat("vo2_max", latestVo2.toFloat())
                .putString("vo2_max_at", latestVo2At.toString())
        }
        if (batteryPct in 0..100) {
            state.putInt("battery_pct", batteryPct)
        }
        state.commit()
        enqueueBatch(samples)
    }

    private fun heartRateQuality(status: HeartRateAccuracy.SensorStatus?): Double? = when (status) {
        HeartRateAccuracy.SensorStatus.ACCURACY_HIGH -> 1.0
        HeartRateAccuracy.SensorStatus.ACCURACY_MEDIUM -> 0.8
        HeartRateAccuracy.SensorStatus.ACCURACY_LOW -> 0.5
        HeartRateAccuracy.SensorStatus.UNRELIABLE -> 0.2
        HeartRateAccuracy.SensorStatus.NO_CONTACT -> 0.0
        else -> null
    }

    private fun enqueueBatch(samples: JSONArray) {
        WearHealthOutbox.enqueueHealthBatch(
            context = this,
            source = "wear_health_services",
            samples = samples,
            collector = "health_services_passive",
        )
    }
}
