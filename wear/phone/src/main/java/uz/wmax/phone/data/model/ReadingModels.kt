package uz.wmax.phone.data.model

import com.google.gson.annotations.SerializedName

/**
 * Corresponds to ReadingIn schema in contracts/openapi.yaml.
 */
data class ReadingInModel(
    @SerializedName("ts")
    val ts: String,

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
 * Corresponds to IngestBatch schema in contracts/openapi.yaml.
 */
data class IngestBatchRequest(
    @SerializedName("patient_id")
    val patientId: String,

    @SerializedName("device_id")
    val deviceId: String? = null,

    @SerializedName("readings")
    val readings: List<ReadingInModel>
)

/**
 * Corresponds to IngestResult schema in contracts/openapi.yaml.
 */
data class IngestResponse(
    @SerializedName("accepted")
    val accepted: Int,

    @SerializedName("duplicates")
    val duplicates: Int,

    @SerializedName("latest_level")
    val latestLevel: String
)
