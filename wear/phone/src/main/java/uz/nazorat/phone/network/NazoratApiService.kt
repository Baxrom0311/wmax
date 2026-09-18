package uz.nazorat.phone.network

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST
import uz.nazorat.phone.data.model.IngestBatchRequest
import uz.nazorat.phone.data.model.IngestResponse
import java.util.concurrent.TimeUnit

interface NazoratApiService {

    @POST("api/v1/ingest")
    suspend fun ingestBatch(
        @Body batch: IngestBatchRequest
    ): Response<IngestResponse>

    companion object {
        const val DEFAULT_BASE_URL = "http://10.0.2.2:8000/"

        fun create(baseUrl: String = DEFAULT_BASE_URL): NazoratApiService {
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }

            val client = OkHttpClient.Builder()
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(15, TimeUnit.SECONDS)
                .writeTimeout(15, TimeUnit.SECONDS)
                .addInterceptor(logging)
                .build()

            val normalizedUrl = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"

            return Retrofit.Builder()
                .baseUrl(normalizedUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(NazoratApiService::class.java)
        }
    }
}
