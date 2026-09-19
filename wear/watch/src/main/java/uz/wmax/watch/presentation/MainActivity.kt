package uz.wmax.watch.presentation

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableDoubleStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.wear.compose.material.MaterialTheme
import androidx.wear.compose.material.Scaffold
import androidx.wear.compose.material.Text
import androidx.wear.compose.material.TimeText
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import uz.wmax.watch.R
import uz.wmax.watch.data.RawSensorSample
import uz.wmax.watch.datalayer.DataLayerSender
import uz.wmax.watch.sensor.HealthServicesManager
import uz.wmax.watch.sensor.MeasureEvent
import uz.wmax.watch.sensor.SensorAggregator

class MainActivity : ComponentActivity() {

    private lateinit var healthServicesManager: HealthServicesManager
    private lateinit var aggregator: SensorAggregator
    private lateinit var dataSender: DataLayerSender
    private var collectionStarted = false

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val granted = permissions[Manifest.permission.BODY_SENSORS] == true
        if (granted) {
            startSensorCollection()
        } else {
            Toast.makeText(this, getString(R.string.sensor_permission_required), Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        healthServicesManager = HealthServicesManager(this)
        aggregator = SensorAggregator(this)
        dataSender = DataLayerSender(this)

        checkAndRequestPermissions()

        setContent {
            MaterialTheme {
                WatchApp(
                    healthServicesManager = healthServicesManager,
                    dataSender = dataSender
                )
            }
        }
    }

    private fun checkAndRequestPermissions() {
        val needed = mutableListOf<String>()
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BODY_SENSORS) != PackageManager.PERMISSION_GRANTED) {
            needed.add(Manifest.permission.BODY_SENSORS)
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACTIVITY_RECOGNITION) != PackageManager.PERMISSION_GRANTED) {
            needed.add(Manifest.permission.ACTIVITY_RECOGNITION)
        }
        if (needed.isNotEmpty()) {
            permissionLauncher.launch(needed.toTypedArray())
        } else {
            startSensorCollection()
        }
    }

    private fun startSensorCollection() {
        if (collectionStarted) return
        collectionStarted = true
        lifecycleScope.launch {
            try {
                healthServicesManager.heartRateFlow().collect { event ->
                    when (event) {
                        is MeasureEvent.HeartRate -> {
                            aggregator.addSample(
                                RawSensorSample(
                                    timestampMs = System.currentTimeMillis(),
                                    hrBpm = event.bpm,
                                    rrIntervalMs = null,
                                    spo2Percent = null,
                                    skinTempCelsius = null,
                                    steps = 0,
                                    isWorn = true
                                )
                            )
                        }
                        is MeasureEvent.SpO2 -> {
                            aggregator.addSample(
                                RawSensorSample(
                                    timestampMs = System.currentTimeMillis(),
                                    hrBpm = null,
                                    rrIntervalMs = null,
                                    spo2Percent = event.percentage,
                                    skinTempCelsius = null,
                                    steps = 0,
                                    isWorn = true
                                )
                            )
                        }
                        else -> Unit
                    }
                }
            } catch (e: Exception) {
                // Log and gracefully handle disconnects
            }
        }
        lifecycleScope.launch {
            while (true) {
                delay(5 * 60 * 1000L)
                val reading = aggregator.computeAndDrainWindow() ?: continue
                val delivered = dataSender.sendReading(reading)
                if (!delivered) {
                    android.util.Log.w("WmaxWatch", "Five-minute window could not reach companion")
                }
            }
        }
    }
}

@Composable
fun WatchApp(
    healthServicesManager: HealthServicesManager,
    dataSender: DataLayerSender
) {
    var heartRate by remember { mutableDoubleStateOf(72.0) }
    var isPhoneConnected by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    // Periodically poll connection status with phone
    LaunchedEffect(Unit) {
        while (true) {
            isPhoneConnected = dataSender.isPhoneConnected()
            delay(5000)
        }
    }

    // Observe live heart rate
    LaunchedEffect(Unit) {
        try {
            healthServicesManager.heartRateFlow().collect { event ->
                if (event is MeasureEvent.HeartRate) {
                    heartRate = event.bpm
                }
            }
        } catch (e: Exception) {
            // Keep default fallback in emulator
        }
    }

    var sosStage by remember { mutableStateOf("idle") }

    if (sosStage == "countdown") {
        SosCountdownConfirmScreen(
            onConfirmed = {
                scope.launch {
                    val delivered = dataSender.sendSosImmediate(
                        uz.wmax.watch.data.SosDto(
                            // The companion resolves the authenticated patient.
                            patientId = "",
                            source = "watch_button",
                            ts = java.time.Instant.now().toString()
                        )
                    )
                    sosStage = if (delivered) "dispatched" else "idle"
                }
            },
            onCancelled = {
                sosStage = "idle"
            }
        )
        return
    }

    if (sosStage == "dispatched") {
        SosDispatchedScreen(
            onCancelRequested = {
                sosStage = "idle"
            },
            onDone = {
                sosStage = "idle"
            }
        )
        return
    }

    Scaffold(
        timeText = { TimeText() },
        modifier = Modifier.background(Color.Black)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = stringResource(R.string.heart_rate),
                    fontSize = 11.sp,
                    color = Color(0xFF9E9E9E),
                    fontWeight = FontWeight.Medium
                )
                Spacer(modifier = Modifier.height(1.dp))
                Text(
                    text = "%.0f".format(heartRate),
                    fontSize = 46.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    text = stringResource(R.string.bpm),
                    fontSize = 11.sp,
                    color = Color(0xFFFF7A70),
                    fontWeight = FontWeight.SemiBold
                )
                Spacer(modifier = Modifier.height(9.dp))
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center,
                    modifier = Modifier
                        .background(Color(0xFF171717), RoundedCornerShape(16.dp))
                        .padding(horizontal = 10.dp, vertical = 5.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(7.dp)
                            .background(
                                if (isPhoneConnected) Color(0xFF62D997) else Color(0xFFFF7A70),
                                CircleShape
                            )
                    )
                    Spacer(modifier = Modifier.size(5.dp))
                    Text(
                        text = if (isPhoneConnected) stringResource(R.string.monitoring_active)
                        else stringResource(R.string.phone_disconnected),
                        fontSize = 10.sp,
                        color = Color(0xFFE7E7E7)
                    )
                }
                Spacer(modifier = Modifier.height(10.dp))
                SosHoldButton(
                    onTriggerCountdown = {
                        sosStage = "countdown"
                    }
                )
            }
        }
    }
}
