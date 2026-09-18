package uz.nazorat.watch.datalayer

import android.content.Context
import android.util.Log
import com.google.android.gms.wearable.Wearable
import com.google.gson.Gson
import kotlinx.coroutines.tasks.await
import uz.nazorat.watch.data.ReadingDto

/**
 * Sends 5-minute aggregate ReadingDto objects to the paired companion Android phone.
 * Uses Google Play Services Wearable MessageClient / DataClient.
 */
class DataLayerSender(private val context: Context) {

    private val messageClient = Wearable.getMessageClient(context)
    private val nodeClient = Wearable.getNodeClient(context)
    private val gson = Gson()

    companion object {
        private const val TAG = "DataLayerSender"
        const val PATH_READING_BATCH = "/nazorat/reading_batch"
        const val PATH_PING = "/nazorat/ping"
    }

    /**
     * Checks if at least one companion phone node is currently connected.
     */
    suspend fun isPhoneConnected(): Boolean {
        return try {
            val nodes = nodeClient.connectedNodes.await()
            nodes.isNotEmpty()
        } catch (e: Exception) {
            Log.w(TAG, "Error checking connected nodes: ${e.message}")
            false
        }
    }

    /**
     * Transmits a 5-minute ReadingDto payload to all connected phone nodes.
     * Returns true if sent successfully to at least one node.
     */
    suspend fun sendReading(reading: ReadingDto): Boolean {
        return try {
            val nodes = nodeClient.connectedNodes.await()
            if (nodes.isEmpty()) {
                Log.w(TAG, "No connected phone nodes found to receive reading")
                return false
            }

            val jsonString = gson.toJson(reading)
            val payloadBytes = jsonString.toByteArray(Charsets.UTF_8)

            var delivered = false
            for (node in nodes) {
                try {
                    messageClient.sendMessage(node.id, PATH_READING_BATCH, payloadBytes).await()
                    Log.i(TAG, "Successfully sent reading to phone node: ${node.displayName} (${node.id})")
                    delivered = true
                } catch (nodeErr: Exception) {
                    Log.e(TAG, "Failed sending to node ${node.id}: ${nodeErr.message}")
                }
            }
            delivered
        } catch (e: Exception) {
            Log.e(TAG, "Failed to dispatch reading over Data Layer: ${e.message}")
            false
        }
    }
}
