package uz.wmax.phone.network

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import uz.wmax.phone.data.model.IngestBatchRequest
import uz.wmax.phone.data.model.IngestResponse
import java.util.concurrent.TimeUnit

data class SosRaisePayload(
    val patient_id: String,
    val source: String = "watch_button",
    val device_lat: Double? = null,
    val device_lon: Double? = null,
    val device_accuracy_m: Double? = null
)

data class PatientLoginPayload(val phone: String, val pin: String)
data class TokenPairResponse(
    val access_token: String,
    val refresh_token: String,
    val expires_in: Int,
    val role: String,
    val full_name: String
)
data class CurrentUserResponse(val id: String, val full_name: String, val role: String)

interface WmaxApiService {

    @POST("api/v1/auth/patient/login")
    suspend fun patientLogin(@Body req: PatientLoginPayload): Response<TokenPairResponse>

    @GET("api/v1/auth/me")
    suspend fun getMe(@Header("Authorization") authorization: String): Response<CurrentUserResponse>

    @POST("api/v1/ingest")
    suspend fun ingestBatch(
        @Body batch: IngestBatchRequest
    ): Response<IngestResponse>

    @POST("api/v1/sos")
    suspend fun raiseSos(
        @Header("Authorization") authorization: String,
        @Body req: SosRaisePayload
    ): Response<Map<String, Any>>

    companion object {
        const val DEFAULT_BASE_URL = "https://wmax.boos.uz/"
        const val DEFAULT_INGEST_KEY = "dev_ingest_secret_key_wmax"

        fun create(baseUrl: String = DEFAULT_BASE_URL, apiKey: String? = DEFAULT_INGEST_KEY): WmaxApiService {
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
            }

            val effectiveKey = if (!apiKey.isNullOrBlank()) apiKey else DEFAULT_INGEST_KEY

            val clientBuilder = OkHttpClient.Builder()
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(15, TimeUnit.SECONDS)
                .writeTimeout(15, TimeUnit.SECONDS)
                .addInterceptor(logging)

            if (!effectiveKey.isNullOrBlank()) {
                clientBuilder.addInterceptor { chain ->
                    val req = chain.request().newBuilder()
                        .addHeader("X-Ingest-Key", effectiveKey)
                        .build()
                    chain.proceed(req)
                }
            }

            val client = clientBuilder.build()
            val normalizedUrl = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"

            return Retrofit.Builder()
                .baseUrl(normalizedUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(WmaxApiService::class.java)
        }
    }
}
