package com.wmax.mobile_flutter

import com.google.android.gms.wearable.MessageClient
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.Wearable
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity(), MessageClient.OnMessageReceivedListener {
    companion object {
        private const val CHANNEL = "com.wmax.mobile_flutter/wear"
        private const val TELEMETRY_CHANNEL = "com.wmax.mobile_flutter/wear_telemetry"
        private const val READING_PATH = "/wmax/reading_batch"
        private const val SOS_PATH = "/wmax/sos"
    }

    private var telemetrySink: EventChannel.EventSink? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                if (call.method != "connectedNodes") {
                    result.notImplemented()
                    return@setMethodCallHandler
                }
                Wearable.getNodeClient(this).connectedNodes
                    .addOnSuccessListener { nodes ->
                        result.success(nodes.map { node ->
                            mapOf("id" to node.id, "name" to node.displayName, "nearby" to node.isNearby)
                        })
                    }
                    .addOnFailureListener { error -> result.error("NODES", error.message, null) }
            }
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, TELEMETRY_CHANNEL)
            .setStreamHandler(object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) { telemetrySink = events }
                override fun onCancel(arguments: Any?) { telemetrySink = null }
            })
    }

    override fun onStart() {
        super.onStart()
        Wearable.getMessageClient(this).addListener(this)
    }

    override fun onStop() {
        Wearable.getMessageClient(this).removeListener(this)
        super.onStop()
    }

    override fun onMessageReceived(event: MessageEvent) {
        if (event.path != READING_PATH && event.path != SOS_PATH) return
        runOnUiThread {
            telemetrySink?.success(mapOf(
                "path" to event.path,
                "source_node_id" to event.sourceNodeId,
                "payload" to String(event.data, Charsets.UTF_8),
            ))
        }
    }
}
