package uz.nazorat.watch.data

import com.google.gson.annotations.SerializedName

/**
 * 5-minute aggregate biometric reading.
 * Strictly conforms to `ReadingIn` schema in contracts/openapi.yaml.
 */
data class ReadingDto(
    @SerializedName("ts")
    val ts: String, // ISO-8601 UTC format e.g. "2026-09-18T09:00:00Z"

    @SerializedName("hr_mean")
    val hrMean: Double? = null,

    @SerializedName("hr_min")
    val hrMin: Double? = null,

    @SerializedName("hr_max")
    val hrMax: Double? = null,

    @SerializedName("rmssd")
    val rmssd: Double? = null,

    @SerializedName("sdnn")
    val sdnn: Double? = null,

    @SerializedName("spo2")
    val spo2: Double? = null,

    @SerializedName("skin_temp")
    val skinTemp: Double? = null,

    @SerializedName("steps")
    val steps: Int? = null,

    @SerializedName("rr_est")
    val rrEst: Double? = null,

    @SerializedName("sleep_frag")
    val sleepFrag: Double? = null,

    @SerializedName("worn")
    val worn: Boolean = true,

    @SerializedName("battery")
    val battery: Int? = null
)

/**
 * Raw 1-minute measurement sample before 5-minute window aggregation.
 */
data class RawSensorSample(
    val timestampMs: Long,
    val hrBpm: Double?,
    val rrIntervalMs: Double?,
    val spo2Percent: Double?,
    val skinTempCelsius: Double?,
    val steps: Int,
    val isWorn: Boolean
)
