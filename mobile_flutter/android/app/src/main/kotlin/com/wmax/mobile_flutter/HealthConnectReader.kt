package com.wmax.mobile_flutter

import android.content.Context
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.records.ActiveCaloriesBurnedRecord
import androidx.health.connect.client.records.BloodGlucoseRecord
import androidx.health.connect.client.records.BloodPressureRecord
import androidx.health.connect.client.records.BodyFatRecord
import androidx.health.connect.client.records.BodyTemperatureRecord
import androidx.health.connect.client.records.DistanceRecord
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.records.HeartRateRecord
import androidx.health.connect.client.records.HeartRateVariabilityRmssdRecord
import androidx.health.connect.client.records.OxygenSaturationRecord
import androidx.health.connect.client.records.RespiratoryRateRecord
import androidx.health.connect.client.records.RestingHeartRateRecord
import androidx.health.connect.client.records.SkinTemperatureRecord
import androidx.health.connect.client.records.SleepSessionRecord
import androidx.health.connect.client.records.SpeedRecord
import androidx.health.connect.client.records.StepsRecord
import androidx.health.connect.client.records.TotalCaloriesBurnedRecord
import androidx.health.connect.client.records.Vo2MaxRecord
import androidx.health.connect.client.records.WeightRecord
import androidx.health.connect.client.records.metadata.Metadata
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.time.Duration
import java.time.Instant
import java.util.UUID

interface HealthConnectResultCallback {
    fun onSuccess(payload: Map<String, Any?>)
    fun onError(code: String, message: String)
}

object HealthConnectReader {
    @JvmStatic
    fun readRecent(context: Context, hours: Long, callback: HealthConnectResultCallback) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val sdkStatus = HealthConnectClient.getSdkStatus(context)
                if (sdkStatus != HealthConnectClient.SDK_AVAILABLE) {
                    callback.onError("HEALTH_CONNECT_UNAVAILABLE", "Health Connect is not available: $sdkStatus")
                    return@launch
                }

                val client = HealthConnectClient.getOrCreate(context)
                val now = Instant.now()
                val start = now.minus(Duration.ofHours(hours.coerceIn(1, 24 * 30)))
                val range = TimeRangeFilter.between(start, now)
                val samples = mutableListOf<Map<String, Any?>>()
                val sleepSessions = mutableListOf<Map<String, Any?>>()
                val exerciseSessions = mutableListOf<Map<String, Any?>>()

                readHeartRate(client, range, samples)
                readHeartRateVariability(client, range, samples)
                readSteps(client, range, samples)
                readRespiratoryRate(client, range, samples)
                readOxygenSaturation(client, range, samples)
                readRestingHeartRate(client, range, samples)
                readSkinTemperature(client, range, samples)
                readBodyTemperature(client, range, samples)
                readBloodPressure(client, range, samples)
                readBloodGlucose(client, range, samples)
                readWeight(client, range, samples)
                readBodyFat(client, range, samples)
                readVo2Max(client, range, samples)
                readDistance(client, range, samples)
                readActiveCalories(client, range, samples)
                readTotalCalories(client, range, samples)
                readSpeed(client, range, samples)
                readSleep(client, range, sleepSessions)
                readExercise(client, range, exerciseSessions)

                callback.onSuccess(
                    mapOf(
                        "batch_id" to UUID.randomUUID().toString(),
                        "source" to "health_connect",
                        "samples" to samples,
                        "sleep_sessions" to sleepSessions,
                        "exercise_sessions" to exerciseSessions,
                        "metadata" to mapOf(
                            "reader" to "health_connect",
                            "window_hours" to hours,
                            "start_time" to start.toString(),
                            "end_time" to now.toString(),
                        ),
                    ),
                )
            } catch (security: SecurityException) {
                callback.onError("HEALTH_CONNECT_PERMISSION_DENIED", security.message ?: "Health Connect permission denied")
            } catch (error: Throwable) {
                callback.onError("HEALTH_CONNECT_READ_FAILED", error.message ?: error.javaClass.simpleName)
            }
        }
    }

    private suspend fun readHeartRate(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        for (record in client.readRecords(ReadRecordsRequest(HeartRateRecord::class, range)).records) {
            for (sample in record.samples) {
                out.add(
                    sampleMap(
                        metric = "heart_rate_bpm",
                        recordedAt = sample.time,
                        value = sample.beatsPerMinute.toDouble(),
                        unit = "bpm",
                        sourceRecordId = record.metadata.safeId(),
                        metadata = sourceMetadata(record.metadata),
                    ),
                )
            }
        }
    }

    private suspend fun readSteps(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        for (record in client.readRecords(ReadRecordsRequest(StepsRecord::class, range)).records) {
            out.add(
                sampleMap(
                    metric = "steps",
                    recordedAt = record.endTime,
                    value = record.count.toDouble(),
                    unit = "count",
                    startedAt = record.startTime,
                    endedAt = record.endTime,
                    sourceRecordId = record.metadata.safeId(),
                    metadata = sourceMetadata(record.metadata),
                ),
            )
        }
    }

    private suspend fun readHeartRateVariability(client: HealthConnectClient, range: TimeRangeFilter, out: MutableList<Map<String, Any?>>) {
        for (record in client.readRecords(ReadRecordsRequest(HeartRateVariabilityRmssdRecord::class, range)).records) {
            out.add(sampleMap("heart_rate_variability_rmssd_ms", record.time, record.heartRateVariabilityMillis, "ms", sourceRecordId = record.metadata.safeId(), metadata = sourceMetadata(record.metadata)))
        }
    }

    private suspend fun readBodyTemperature(client: HealthConnectClient, range: TimeRangeFilter, out: MutableList<Map<String, Any?>>) {
        for (record in client.readRecords(ReadRecordsRequest(BodyTemperatureRecord::class, range)).records) {
            out.add(sampleMap("body_temperature_c", record.time, doubleFromUnit(record.temperature, "getCelsius"), "celsius", sourceRecordId = record.metadata.safeId(), metadata = sourceMetadata(record.metadata) + mapOf("measurement_location" to record.measurementLocation)))
        }
    }

    private suspend fun readBloodPressure(client: HealthConnectClient, range: TimeRangeFilter, out: MutableList<Map<String, Any?>>) {
        for (record in client.readRecords(ReadRecordsRequest(BloodPressureRecord::class, range)).records) {
            val sourceId = record.metadata.safeId()
            val metadata = sourceMetadata(record.metadata) + mapOf("body_position" to record.bodyPosition, "measurement_location" to record.measurementLocation)
            out.add(sampleMap("blood_pressure_systolic_mmhg", record.time, doubleFromUnit(record.systolic, "getMillimetersOfMercury"), "mmHg", sourceRecordId = sourceId, metadata = metadata))
            out.add(sampleMap("blood_pressure_diastolic_mmhg", record.time, doubleFromUnit(record.diastolic, "getMillimetersOfMercury"), "mmHg", sourceRecordId = sourceId, metadata = metadata))
        }
    }

    private suspend fun readBloodGlucose(client: HealthConnectClient, range: TimeRangeFilter, out: MutableList<Map<String, Any?>>) {
        for (record in client.readRecords(ReadRecordsRequest(BloodGlucoseRecord::class, range)).records) {
            out.add(sampleMap("blood_glucose_mmol_l", record.time, doubleFromUnit(record.level, "getInMillimolesPerLiter"), "mmol/L", sourceRecordId = record.metadata.safeId(), metadata = sourceMetadata(record.metadata) + mapOf("meal_type" to record.mealType, "relation_to_meal" to record.relationToMeal, "specimen_source" to record.specimenSource)))
        }
    }

    private suspend fun readWeight(client: HealthConnectClient, range: TimeRangeFilter, out: MutableList<Map<String, Any?>>) {
        for (record in client.readRecords(ReadRecordsRequest(WeightRecord::class, range)).records) {
            out.add(sampleMap("weight_kg", record.time, doubleFromUnit(record.weight, "getKilograms"), "kg", sourceRecordId = record.metadata.safeId(), metadata = sourceMetadata(record.metadata)))
        }
    }

    private suspend fun readBodyFat(client: HealthConnectClient, range: TimeRangeFilter, out: MutableList<Map<String, Any?>>) {
        for (record in client.readRecords(ReadRecordsRequest(BodyFatRecord::class, range)).records) {
            out.add(sampleMap("body_fat_pct", record.time, record.percentage.value, "%", sourceRecordId = record.metadata.safeId(), metadata = sourceMetadata(record.metadata)))
        }
    }

    private suspend fun readVo2Max(client: HealthConnectClient, range: TimeRangeFilter, out: MutableList<Map<String, Any?>>) {
        for (record in client.readRecords(ReadRecordsRequest(Vo2MaxRecord::class, range)).records) {
            out.add(sampleMap("vo2_max_ml_kg_min", record.time, record.vo2MillilitersPerMinuteKilogram, "mL/kg/min", sourceRecordId = record.metadata.safeId(), metadata = sourceMetadata(record.metadata) + mapOf("measurement_method" to record.measurementMethod)))
        }
    }

    private suspend fun readRespiratoryRate(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        for (record in client.readRecords(ReadRecordsRequest(RespiratoryRateRecord::class, range)).records) {
            out.add(
                sampleMap(
                    metric = "respiratory_rate_bpm",
                    recordedAt = record.time,
                    value = record.rate,
                    unit = "breaths/min",
                    sourceRecordId = record.metadata.safeId(),
                    metadata = sourceMetadata(record.metadata),
                ),
            )
        }
    }

    private suspend fun readOxygenSaturation(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        for (record in client.readRecords(ReadRecordsRequest(OxygenSaturationRecord::class, range)).records) {
            out.add(
                sampleMap(
                    metric = "oxygen_saturation_pct",
                    recordedAt = record.time,
                    value = record.percentage.value,
                    unit = "%",
                    sourceRecordId = record.metadata.safeId(),
                    metadata = sourceMetadata(record.metadata),
                ),
            )
        }
    }

    private suspend fun readRestingHeartRate(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        for (record in client.readRecords(ReadRecordsRequest(RestingHeartRateRecord::class, range)).records) {
            out.add(
                sampleMap(
                    metric = "resting_heart_rate_bpm",
                    recordedAt = record.time,
                    value = record.beatsPerMinute.toDouble(),
                    unit = "bpm",
                    sourceRecordId = record.metadata.safeId(),
                    metadata = sourceMetadata(record.metadata),
                ),
            )
        }
    }

    private suspend fun readSkinTemperature(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        for (record in client.readRecords(ReadRecordsRequest(SkinTemperatureRecord::class, range)).records) {
            record.baseline?.let { baseline ->
                out.add(
                    sampleMap(
                        metric = "skin_temperature_baseline_c",
                        recordedAt = record.endTime,
                        value = doubleFromUnit(baseline, "getCelsius"),
                        unit = "celsius",
                        startedAt = record.startTime,
                        endedAt = record.endTime,
                        sourceRecordId = record.metadata.safeId(),
                        metadata = sourceMetadata(record.metadata) + mapOf("measurement_location" to record.measurementLocation),
                    ),
                )
            }
            for (delta in record.deltas) {
                out.add(
                    sampleMap(
                        metric = "skin_temperature_delta_c",
                        recordedAt = delta.time,
                        value = doubleFromUnit(delta.delta, "getCelsius"),
                        unit = "celsius",
                        sourceRecordId = record.metadata.safeId(),
                        metadata = sourceMetadata(record.metadata) + mapOf("measurement_location" to record.measurementLocation),
                    ),
                )
            }
        }
    }

    private suspend fun readDistance(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        for (record in client.readRecords(ReadRecordsRequest(DistanceRecord::class, range)).records) {
            out.add(
                sampleMap(
                    metric = "distance_m",
                    recordedAt = record.endTime,
                    value = doubleFromUnit(record.distance, "getMeters"),
                    unit = "m",
                    startedAt = record.startTime,
                    endedAt = record.endTime,
                    sourceRecordId = record.metadata.safeId(),
                    metadata = sourceMetadata(record.metadata),
                ),
            )
        }
    }

    private suspend fun readActiveCalories(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        for (record in client.readRecords(ReadRecordsRequest(ActiveCaloriesBurnedRecord::class, range)).records) {
            out.add(
                sampleMap(
                    metric = "active_calories_kcal",
                    recordedAt = record.endTime,
                    value = doubleFromUnit(record.energy, "getKilocalories"),
                    unit = "kcal",
                    startedAt = record.startTime,
                    endedAt = record.endTime,
                    sourceRecordId = record.metadata.safeId(),
                    metadata = sourceMetadata(record.metadata),
                ),
            )
        }
    }

    private suspend fun readSpeed(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        for (record in client.readRecords(ReadRecordsRequest(SpeedRecord::class, range)).records) {
            for (sample in record.samples) {
                out.add(
                    sampleMap(
                        metric = "speed_mps",
                        recordedAt = sample.time,
                        value = doubleFromUnit(sample.speed, "getMetersPerSecond"),
                        unit = "m/s",
                        sourceRecordId = record.metadata.safeId(),
                        metadata = sourceMetadata(record.metadata),
                    ),
                )
            }
        }
    }

    private suspend fun readTotalCalories(client: HealthConnectClient, range: TimeRangeFilter, out: MutableList<Map<String, Any?>>) {
        for (record in client.readRecords(ReadRecordsRequest(TotalCaloriesBurnedRecord::class, range)).records) {
            out.add(sampleMap("total_calories_kcal", record.endTime, doubleFromUnit(record.energy, "getKilocalories"), "kcal", startedAt = record.startTime, endedAt = record.endTime, sourceRecordId = record.metadata.safeId(), metadata = sourceMetadata(record.metadata)))
        }
    }

    private suspend fun readSleep(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        val stageNames = SleepSessionRecord.STAGE_TYPE_INT_TO_STRING_MAP
        for (record in client.readRecords(ReadRecordsRequest(SleepSessionRecord::class, range)).records) {
            out.add(
                mapOf(
                    "start_time" to record.startTime.toString(),
                    "end_time" to record.endTime.toString(),
                    "source_record_id" to record.metadata.safeId(),
                    "stages" to record.stages.map { stage ->
                        mapOf(
                            "stage" to (stageNames[stage.stage] ?: "unknown"),
                            "start_time" to stage.startTime.toString(),
                            "end_time" to stage.endTime.toString(),
                        )
                    },
                    "metrics" to emptyMap<String, Any?>(),
                    "metadata" to sourceMetadata(record.metadata) + mapOf(
                        "title" to record.title,
                        "notes" to record.notes,
                    ).filterValues { it != null },
                ),
            )
        }
    }

    private suspend fun readExercise(
        client: HealthConnectClient,
        range: TimeRangeFilter,
        out: MutableList<Map<String, Any?>>,
    ) {
        val exerciseNames = ExerciseSessionRecord.EXERCISE_TYPE_INT_TO_STRING_MAP
        for (record in client.readRecords(ReadRecordsRequest(ExerciseSessionRecord::class, range)).records) {
            out.add(
                mapOf(
                    "exercise_type" to (exerciseNames[record.exerciseType] ?: "unknown"),
                    "start_time" to record.startTime.toString(),
                    "end_time" to record.endTime.toString(),
                    "source_record_id" to record.metadata.safeId(),
                    "metrics" to mapOf(
                        "segment_count" to record.segments.size,
                        "lap_count" to record.laps.size,
                    ),
                    "route" to null,
                    "metadata" to sourceMetadata(record.metadata) + mapOf(
                        "title" to record.title,
                        "notes" to record.notes,
                    ).filterValues { it != null },
                ),
            )
        }
    }

    private fun sampleMap(
        metric: String,
        recordedAt: Instant,
        value: Double,
        unit: String,
        startedAt: Instant? = null,
        endedAt: Instant? = null,
        sourceRecordId: String? = null,
        metadata: Map<String, Any?> = emptyMap(),
    ): Map<String, Any?> =
        mapOf(
            "metric" to metric,
            "recorded_at" to recordedAt.toString(),
            "value_num" to value,
            "unit" to unit,
            "started_at" to startedAt?.toString(),
            "ended_at" to endedAt?.toString(),
            "source_record_id" to sourceRecordId,
            "metadata" to metadata,
        ).filterValues { it != null }

    private fun Metadata.safeId(): String? = id.takeIf { it.isNotBlank() }

    private fun doubleFromUnit(unit: Any, getterName: String): Double =
        (unit.javaClass.getMethod(getterName).invoke(unit) as Number).toDouble()

    private fun sourceMetadata(metadata: Metadata): Map<String, Any?> =
        mapOf(
            "data_origin_package" to metadata.dataOrigin.packageName,
            "recording_method" to metadata.recordingMethod,
            "last_modified_time" to metadata.lastModifiedTime.toString(),
            "client_record_id" to metadata.clientRecordId,
        ).filterValues { it != null }
}
