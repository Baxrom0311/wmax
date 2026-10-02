package com.wmax.mobile_flutter

import android.os.SystemClock
import android.util.Log
import androidx.health.services.client.PassiveListenerService
import androidx.health.services.client.data.DataPointContainer
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.UserActivityInfo
import androidx.health.services.client.data.UserActivityState
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant
import java.util.UUID

class WmaxPassiveHealthService : PassiveListenerService() {
    override fun onUserActivityInfoReceived(info: UserActivityInfo) {
        val state = when (info.userActivityState) {
            UserActivityState.USER_ACTIVITY_ASLEEP -> "asleep"
            UserActivityState.USER_ACTIVITY_EXERCISE -> "exercise"
            UserActivityState.USER_ACTIVITY_PASSIVE -> "passive"
            else -> return
        }
        val changedAt = info.stateChangeTime
        val samples = JSONArray().put(
            JSONObject()
                .put("metric", "activity_state")
                .put("recorded_at", changedAt.toString())
                .put("value_text", state)
                .put("source_record_id", "activity-state-${changedAt.toEpochMilli()}"),
        )
        enqueueBatch(this, samples)
    }

    override fun onNewDataPointsReceived(dataPoints: DataPointContainer) {
        val bootInstant = Instant.ofEpochMilli(
            System.currentTimeMillis() - SystemClock.elapsedRealtime(),
        )
        val samples = JSONArray()
        var latestDailySteps: Long? = null
        var latestDailyStepsAt: Instant? = null
        fun appendInterval(metric: String, value: Number, unit: String, start: Instant, end: Instant) {
            samples.put(
                JSONObject()
                    .put("metric", metric)
                    .put("recorded_at", end.toString())
                    .put("started_at", start.toString())
                    .put("ended_at", end.toString())
                    .put("value_num", value)
                    .put("unit", unit)
                    .put("source_record_id", "$metric-${end.toEpochMilli()}")
                    .put("quality", 1.0),
            )
        }
        var latestHeartRate: Double? = null
        var latestTimestamp: Instant? = null
        for (point in dataPoints.getData(DataType.HEART_RATE_BPM)) {
            val timestamp = point.getTimeInstant(bootInstant)
            if (latestTimestamp == null || timestamp.isAfter(latestTimestamp)) {
                latestHeartRate = point.value
                latestTimestamp = timestamp
            }
            samples.put(
                JSONObject()
                    .put("metric", "heart_rate_bpm")
                    .put("recorded_at", timestamp.toString())
                    .put("value_num", point.value)
                    .put("unit", "bpm")
                    .put("source_record_id", "hr-${timestamp.toEpochMilli()}")
                    .put("quality", 1.0),
            )
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
        if (samples.length() == 0) return

        if ((latestHeartRate != null && latestTimestamp != null) || latestDailySteps != null) {
            val state = getSharedPreferences("wmax_health_state", MODE_PRIVATE).edit()
            if (latestHeartRate != null && latestTimestamp != null) {
                state.putFloat("heart_rate_bpm", latestHeartRate.toFloat())
                    .putString("heart_rate_at", latestTimestamp.toString())
            }
            if (latestDailySteps != null && latestDailyStepsAt != null) {
                state.putLong("daily_steps", latestDailySteps)
                    .putString("daily_steps_at", latestDailyStepsAt.toString())
            }
            state.commit()
        }
        enqueueBatch(this, samples)
    }

    private fun enqueueBatch(context: android.content.Context, samples: JSONArray) {
        for (start in 0 until samples.length() step MAX_SAMPLES_PER_ITEM) {
            val chunk = JSONArray()
            val end = minOf(start + MAX_SAMPLES_PER_ITEM, samples.length())
            for (index in start until end) chunk.put(samples.getJSONObject(index))

            val batchId = UUID.randomUUID().toString()
            val payload = JSONObject()
                .put("batch_id", batchId)
                .put("source", "wear_health_services")
                .put("samples", chunk)
                .put("sleep_sessions", JSONArray())
                .put("exercise_sessions", JSONArray())
                .put("metadata", JSONObject().put("collector", "health_services_passive"))
                .toString()
            if (!WearHealthOutbox.enqueue(context, payload)) {
                Log.e(TAG, "Wear health outbox could not persist a batch")
            }
        }
        WearHealthOutbox.scheduleFlush(context)
    }

    companion object {
        private const val TAG = "WmaxPassiveHealth"
        private const val MAX_SAMPLES_PER_ITEM = 200
    }
}
