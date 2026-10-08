package com.wmax.mobile_flutter

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.content.pm.ServiceInfo
import androidx.health.services.client.ExerciseUpdateCallback
import androidx.health.services.client.HealthServices
import androidx.health.services.client.data.DataPointContainer
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.ExerciseConfig
import androidx.health.services.client.data.ExerciseState
import androidx.health.services.client.data.ExerciseTrackedStatus
import androidx.health.services.client.data.ExerciseType
import androidx.health.services.client.data.ExerciseUpdate
import androidx.health.services.client.data.ExerciseLapSummary
import androidx.health.services.client.data.Availability
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant
import java.util.UUID
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class WearExerciseService : Service() {
    private val client by lazy { HealthServices.getClient(this).exerciseClient }
    private val prefs by lazy { getSharedPreferences(PREFS, MODE_PRIVATE) }
    private val callbackExecutor = Executors.newSingleThreadExecutor()
    private var finalized = false
    private var startTime: Instant? = null
    private var exerciseName: String? = null
    private var sessionId: String? = null
    private var minHr: Double? = null
    private var maxHr: Double? = null
    private var hrTotal = 0.0
    private var hrCount = 0
    private var latestHr: Double? = null
    private var distanceMeters: Double? = null
    private var steps: Long? = null
    private var calories: Double? = null

    private val updateCallback = object : ExerciseUpdateCallback {
        override fun onRegistered() = Unit

        override fun onRegistrationFailed(throwable: Throwable) {
            setError(throwable.message ?: "EXERCISE_CALLBACK_REGISTRATION_FAILED")
            stopSelf()
        }

        override fun onExerciseUpdateReceived(update: ExerciseUpdate) {
            consumeMetrics(update.latestMetrics)
            val state = update.exerciseStateInfo.state
            if (state == ExerciseState.ENDED) {
                finishSession("health_services_ended")
                stopSelf()
            } else {
                persistActiveState(state.toString())
            }
        }

        override fun onLapSummaryReceived(lapSummary: ExerciseLapSummary) = Unit

        override fun onAvailabilityChanged(
            dataType: DataType<*, *>,
            availability: Availability,
        ) = Unit
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(
                NOTIFICATION_ID,
                notification(),
                ServiceInfo.FOREGROUND_SERVICE_TYPE_HEALTH,
            )
        } else {
            startForeground(NOTIFICATION_ID, notification())
        }
        when (intent?.action) {
            ACTION_START -> startExercise(intent.getStringExtra(EXTRA_EXERCISE_TYPE) ?: "WALKING")
            ACTION_STOP -> endExercise()
            null -> recoverExercise()
            else -> stopSelf(startId)
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        client.clearUpdateCallbackAsync(updateCallback)
        callbackExecutor.shutdown()
        super.onDestroy()
    }

    private fun startExercise(requestedType: String) {
        Thread {
            try {
                if (prefs.getBoolean(KEY_ACTIVE, false)) {
                    attachToCurrentExercise()
                    return@Thread
                }
                resetSessionState()
                val type = exerciseType(requestedType)
                val capabilities = client.getCapabilitiesAsync().get(20, TimeUnit.SECONDS)
                if (type !in capabilities.supportedExerciseTypes) {
                    setError("EXERCISE_TYPE_UNSUPPORTED")
                    stopSelf()
                    return@Thread
                }
                val supported = capabilities.getExerciseTypeCapabilities(type).supportedDataTypes
                val requested = mutableSetOf<DataType<*, *>>()
                if (DataType.HEART_RATE_BPM in supported) requested.add(DataType.HEART_RATE_BPM)
                if (DataType.DISTANCE_TOTAL in supported) requested.add(DataType.DISTANCE_TOTAL)
                if (DataType.STEPS_TOTAL in supported) requested.add(DataType.STEPS_TOTAL)
                if (DataType.CALORIES_TOTAL in supported) requested.add(DataType.CALORIES_TOTAL)
                if (requested.isEmpty()) {
                    setError("NO_EXERCISE_METRICS_SUPPORTED")
                    stopSelf()
                    return@Thread
                }
                startTime = Instant.now()
                exerciseName = type.name
                sessionId = UUID.randomUUID().toString()
                client.setUpdateCallback(callbackExecutor, updateCallback)
                val config = ExerciseConfig.Builder(type)
                    .setDataTypes(requested)
                    .setIsAutoPauseAndResumeEnabled(
                        capabilities.getExerciseTypeCapabilities(type).supportsAutoPauseAndResume,
                    )
                    .build()
                persistActiveState("starting")
                client.startExerciseAsync(config).get(20, TimeUnit.SECONDS)
            } catch (error: Exception) {
                setError(error.message ?: "EXERCISE_START_FAILED")
                stopSelf()
            }
        }.start()
    }

    private fun recoverExercise() {
        if (!enqueuePendingSession(this)) {
            stopSelf()
            return
        }
        if (!prefs.getBoolean(KEY_ACTIVE, false)) {
            stopSelf()
            return
        }
        Thread { attachToCurrentExercise() }.start()
    }

    private fun attachToCurrentExercise() {
        try {
            startTime = Instant.parse(prefs.getString(KEY_START, Instant.now().toString()))
            exerciseName = prefs.getString(KEY_TYPE, null)
            sessionId = prefs.getString(KEY_SESSION_ID, UUID.randomUUID().toString())
            minHr = prefs.getString(KEY_MIN_HR, null)?.toDoubleOrNull()
            maxHr = prefs.getString(KEY_MAX_HR, null)?.toDoubleOrNull()
            hrTotal = prefs.getString(KEY_HR_TOTAL, "0")?.toDoubleOrNull() ?: 0.0
            hrCount = prefs.getInt(KEY_HR_COUNT, 0)
            latestHr = prefs.getString(KEY_LATEST_HR, null)?.toDoubleOrNull()
            distanceMeters = prefs.getString(KEY_DISTANCE, null)?.toDoubleOrNull()
            steps = prefs.getString(KEY_STEPS, null)?.toLongOrNull()
            calories = prefs.getString(KEY_CALORIES, null)?.toDoubleOrNull()
            client.setUpdateCallback(callbackExecutor, updateCallback)
            val current = client.getCurrentExerciseInfoAsync().get(15, TimeUnit.SECONDS)
            if (current.exerciseTrackedStatus != ExerciseTrackedStatus.OWNED_EXERCISE_IN_PROGRESS ||
                current.exerciseType.name != prefs.getString(KEY_TYPE, null)
            ) {
                finishSession("exercise_interrupted_by_system")
                stopSelf()
                return
            }
            exerciseName = current.exerciseType.name
        } catch (_: Exception) {
            finishSession("exercise_interrupted_by_system")
            stopSelf()
        }
    }

    private fun endExercise() {
        prefs.edit().putString(KEY_STATUS, "stopping").commit()
        Thread {
            try {
                client.endExerciseAsync().get(20, TimeUnit.SECONDS)
                client.flushAsync().get(10, TimeUnit.SECONDS)
                Thread.sleep(300)
                finishSession("user_ended")
            } catch (error: Exception) {
                setError(error.message ?: "EXERCISE_END_FAILED")
            } finally {
                stopSelf()
            }
        }.start()
    }

    private fun consumeMetrics(container: DataPointContainer) {
        val bootInstant = Instant.ofEpochMilli(System.currentTimeMillis() - android.os.SystemClock.elapsedRealtime())
        for (point in container.getData(DataType.HEART_RATE_BPM)) {
            val bpm = point.value
            latestHr = bpm
            minHr = minHr?.let { minOf(it, bpm) } ?: bpm
            maxHr = maxHr?.let { maxOf(it, bpm) } ?: bpm
            hrTotal += bpm
            hrCount++
            val recordedAt = point.getTimeInstant(bootInstant)
            prefs.edit()
                .putFloat(KEY_LATEST_HR_VALUE, bpm.toFloat())
                .putString(KEY_LATEST_HR_AT, recordedAt.toString())
                .apply()
        }
        container.getData(DataType.DISTANCE_TOTAL)?.let { distanceMeters = it.total }
        container.getData(DataType.STEPS_TOTAL)?.let { steps = it.total }
        container.getData(DataType.CALORIES_TOTAL)?.let { calories = it.total }
        persistActiveState("active")
    }

    private fun resetSessionState() {
        finalized = false
        startTime = null
        exerciseName = null
        sessionId = null
        minHr = null
        maxHr = null
        hrTotal = 0.0
        hrCount = 0
        latestHr = null
        distanceMeters = null
        steps = null
        calories = null
        prefs.edit()
            .putBoolean(KEY_ACTIVE, false)
            .putString(KEY_STATUS, "starting")
            .remove(KEY_ERROR)
            .remove(KEY_LATEST_HR_VALUE)
            .remove(KEY_LATEST_HR_AT)
            .commit()
    }

    @Synchronized
    private fun finishSession(reason: String) {
        if (finalized || !prefs.getBoolean(KEY_ACTIVE, false)) return
        finalized = true
        val start = startTime ?: prefs.getString(KEY_START, null)?.let(Instant::parse) ?: return
        val end = Instant.now().coerceAtLeast(start.plusMillis(1))
        val type = exerciseName ?: prefs.getString(KEY_TYPE, "WORKOUT") ?: "WORKOUT"
        val id = sessionId ?: prefs.getString(KEY_SESSION_ID, UUID.randomUUID().toString())!!
        val metrics = JSONObject()
            .put("duration_seconds", java.time.Duration.between(start, end).seconds)
            .put("heart_rate_samples", hrCount)
        latestHr?.let { metrics.put("latest_heart_rate_bpm", it) }
        minHr?.let { metrics.put("min_heart_rate_bpm", it) }
        maxHr?.let { metrics.put("max_heart_rate_bpm", it) }
        if (hrCount > 0) metrics.put("avg_heart_rate_bpm", hrTotal / hrCount)
        distanceMeters?.let { metrics.put("distance_m", it) }
        steps?.let { metrics.put("steps", it) }
        calories?.let { metrics.put("calories_kcal", it) }
        val session = JSONArray().put(
            JSONObject()
                .put("exercise_type", type)
                .put("start_time", start.toString())
                .put("end_time", end.toString())
                .put("source_record_id", id)
                .put("metrics", metrics)
                .put("metadata", JSONObject().put("end_reason", reason)),
        )
        if (!prefs.edit().putString(KEY_PENDING_SESSION, session.toString()).commit()) {
            finalized = false
            return
        }
        prefs.edit().putBoolean(KEY_ACTIVE, false).putString(KEY_STATUS, "pending_upload").commit()
        if (enqueuePendingSession(this)) {
            prefs.edit()
                .putString(KEY_STATUS, "ended")
                .putString(KEY_LAST_SESSION_ID, id)
                .remove(KEY_PENDING_SESSION)
                .remove(KEY_ERROR)
                .commit()
        } else {
            WearHealthOutbox.scheduleFlush(this)
        }
    }

    private fun persistActiveState(state: String) {
        val start = startTime ?: return
        prefs.edit()
            .putBoolean(KEY_ACTIVE, true)
            .putString(KEY_STATUS, state)
            .putString(KEY_TYPE, exerciseName)
            .putString(KEY_START, start.toString())
            .putString(KEY_SESSION_ID, sessionId)
            .putString(KEY_MIN_HR, minHr?.toString())
            .putString(KEY_MAX_HR, maxHr?.toString())
            .putString(KEY_HR_TOTAL, hrTotal.toString())
            .putInt(KEY_HR_COUNT, hrCount)
            .putString(KEY_LATEST_HR, latestHr?.toString())
            .putString(KEY_DISTANCE, distanceMeters?.toString())
            .putString(KEY_STEPS, steps?.toString())
            .putString(KEY_CALORIES, calories?.toString())
            .remove(KEY_ERROR)
            .commit()
    }

    private fun setError(message: String) {
        prefs.edit().putBoolean(KEY_ACTIVE, false).putString(KEY_STATUS, "error")
            .putString(KEY_ERROR, message).commit()
    }

    private fun exerciseType(name: String): ExerciseType = when (name.uppercase()) {
        "RUNNING" -> ExerciseType.RUNNING
        else -> ExerciseType.WALKING
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "WMAX workout",
                NotificationManager.IMPORTANCE_LOW,
            )
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    private fun notification(): Notification {
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
        }
        return builder.setContentTitle("WMAX")
            .setContentText("Workout tracking is active")
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setOngoing(true)
            .build()
    }

    companion object {
        const val ACTION_START = "com.wmax.mobile_flutter.action.START_EXERCISE"
        const val ACTION_STOP = "com.wmax.mobile_flutter.action.STOP_EXERCISE"
        const val EXTRA_EXERCISE_TYPE = "exercise_type"
        const val PREFS = "wmax_exercise_state"
        const val KEY_ACTIVE = "active"
        const val KEY_STATUS = "status"
        const val KEY_TYPE = "type"
        const val KEY_START = "start_time"
        const val KEY_SESSION_ID = "session_id"
        const val KEY_LAST_SESSION_ID = "last_session_id"
        const val KEY_ERROR = "error"
        const val KEY_PENDING_SESSION = "pending_session"
        const val KEY_LATEST_HR = "latest_hr"
        const val KEY_LATEST_HR_VALUE = "latest_hr_value"
        const val KEY_LATEST_HR_AT = "latest_hr_at"
        private const val KEY_MIN_HR = "min_hr"
        private const val KEY_MAX_HR = "max_hr"
        private const val KEY_HR_TOTAL = "hr_total"
        private const val KEY_HR_COUNT = "hr_count"
        private const val KEY_DISTANCE = "distance"
        private const val KEY_STEPS = "steps"
        private const val KEY_CALORIES = "calories"
        private const val CHANNEL_ID = "wmax_exercise"
        private const val NOTIFICATION_ID = 8104

        fun enqueuePendingSession(context: android.content.Context): Boolean {
            val prefs = context.getSharedPreferences(PREFS, android.content.Context.MODE_PRIVATE)
            val pending = prefs.getString(KEY_PENDING_SESSION, null) ?: return true
            val queued = WearHealthOutbox.enqueueHealthBatch(
                context = context,
                source = "wear_health_services",
                samples = JSONArray(),
                exerciseSessions = JSONArray(pending),
                collector = "health_services_exercise",
            )
            if (queued) {
                val sessionId = JSONArray(pending)
                    .optJSONObject(0)
                    ?.optString("source_record_id")
                prefs.edit()
                    .remove(KEY_PENDING_SESSION)
                    .putString(KEY_STATUS, "ended")
                    .putString(KEY_LAST_SESSION_ID, sessionId)
                    .commit()
            }
            return queued
        }
    }
}
