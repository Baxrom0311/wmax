package uz.wmax.watch.network

import com.google.gson.annotations.SerializedName
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import uz.wmax.watch.data.ReadingDto
import uz.wmax.watch.BuildConfig
import java.util.concurrent.TimeUnit

data class WatchIngestBatchRequest(
    @SerializedName("patient_id")
    val patientId: String,
    @SerializedName("readings")
    val readings: List<ReadingDto>
)

data class WatchIngestResponse(
    @SerializedName("inserted")
    val inserted: Int,
    @SerializedName("duplicates")
    val duplicates: Int = 0,
    @SerializedName("errors")
    val errors: Int = 0,
    @SerializedName("status")
    val status: String = "ok"
)

data class WatchSosRaisePayload(
    @SerializedName("patient_id")
    val patientId: String,
    @SerializedName("source")
    val source: String = "watch_button",
    @SerializedName("device_lat")
    val deviceLat: Double? = 41.5562,
    @SerializedName("device_lon")
    val deviceLon: Double? = 60.6311,
    @SerializedName("device_accuracy_m")
    val deviceAccuracyM: Double? = 10.0
)

data class WatchSosResponse(
    @SerializedName("id")
    val id: String? = null,
    @SerializedName("status")
    val status: String? = null,
    @SerializedName("source")
    val source: String? = null
)

interface WatchApiService {

    @POST("api/v1/ingest")
    suspend fun ingestBatch(
        @Body batch: WatchIngestBatchRequest
    ): Response<WatchIngestResponse>

    @POST("api/v1/sos")
    suspend fun raiseSos(
        @Header("Authorization") authorization: String? = null,
        @Body payload: WatchSosRaisePayload
    ): Response<WatchSosResponse>

    @POST("api/v1/sos/{id}/cancel")
    suspend fun cancelSos(
        @Path("id") sosId: String,
        @Header("Authorization") authorization: String? = null
    ): Response<Map<String, Any>>

    companion object {
        const val DEFAULT_BASE_URL = "https://wmax.boos.uz/"
        const val DEFAULT_INGEST_KEY = ""

        fun create(
            baseUrl: String = DEFAULT_BASE_URL,
            apiKey: String = BuildConfig.WMAX_INGEST_KEY.ifBlank { DEFAULT_INGEST_KEY },
        ): WatchApiService {
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
            }

            val client = OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .writeTimeout(10, TimeUnit.SECONDS)
                .addInterceptor(logging)
                .addInterceptor { chain ->
                    val req = chain.request().newBuilder()
                        .addHeader("X-Ingest-Key", apiKey)
                        .build()
                    chain.proceed(req)
                }
                .build()

            val normalizedUrl = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"

            return Retrofit.Builder()
                .baseUrl(normalizedUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(WatchApiService::class.java)
        }
    }
}
