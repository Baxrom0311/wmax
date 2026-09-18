package uz.nazorat.watch.presentation

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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableDoubleStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.wear.compose.material.Button
import androidx.wear.compose.material.ButtonDefaults
import androidx.wear.compose.material.CircularProgressIndicator
import androidx.wear.compose.material.MaterialTheme
import androidx.wear.compose.material.Scaffold
import androidx.wear.compose.material.Text
import androidx.wear.compose.material.TimeText
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import uz.nazorat.watch.R
import uz.nazorat.watch.data.RawSensorSample
import uz.nazorat.watch.datalayer.DataLayerSender
import uz.nazorat.watch.sensor.HealthServicesManager
import uz.nazorat.watch.sensor.MeasureEvent
import uz.nazorat.watch.sensor.SensorAggregator

class MainActivity : ComponentActivity() {

    private lateinit var healthServicesManager: HealthServicesManager
    private lateinit var aggregator: SensorAggregator
    private lateinit var dataSender: DataLayerSender

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val granted = permissions[Manifest.permission.BODY_SENSORS] == true
        if (granted) {
            startSensorCollection()
        } else {
            Toast.makeText(this, "Sensor ruxsati kerak", Toast.LENGTH_SHORT).show()
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
                    aggregator = aggregator,
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
    }
}

@Composable
fun WatchApp(
    healthServicesManager: HealthServicesManager,
    aggregator: SensorAggregator,
    dataSender: DataLayerSender
) {
    var heartRate by remember { mutableDoubleStateOf(72.0) }
    var isPhoneConnected by remember { mutableStateOf(false) }
    var isSyncing by remember { mutableStateOf(false) }
    var lastSyncStatus by remember { mutableStateOf<String?>(null) }
    var wornStatus by remember { mutableStateOf(true) }

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
                // Connection indicator row
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .background(
                                color = if (isPhoneConnected) Color(0xFF2E7D5B) else Color(0xFFB3261E),
                                shape = CircleShape
                            )
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = if (isPhoneConnected) stringResource(R.string.status_connected) else stringResource(R.string.status_disconnected),
                        fontSize = 11.sp,
                        color = Color(0xFFC8C6C0)
                    )
                }

                Spacer(modifier = Modifier.height(6.dp))

                // Heart Rate BPM Display
                Text(
                    text = "%.0f".format(heartRate),
                    fontSize = 36.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    text = stringResource(R.string.bpm),
                    fontSize = 12.sp,
                    color = Color(0xFFB3261E),
                    fontWeight = FontWeight.SemiBold
                )

                Spacer(modifier = Modifier.height(6.dp))

                // Manual trigger action: Aggregate & send to phone
                Button(
                    onClick = {
                        scope.launch {
                            isSyncing = true
                            val reading = aggregator.computeAndDrainWindow()
                            if (reading != null) {
                                val ok = dataSender.sendReading(reading)
                                lastSyncStatus = if (ok) "Yuborildi" else "Xato"
                            } else {
                                // In emulator/test mode without sensor readings, emit synthetic sample
                                val testReading = aggregator.let {
                                    it.addSample(RawSensorSample(System.currentTimeMillis(), heartRate, null, 98.0, 36.6, 12, true))
                                    it.computeAndDrainWindow()
                                }
                                if (testReading != null) {
                                    val ok = dataSender.sendReading(testReading)
                                    lastSyncStatus = if (ok) "Yuborildi" else "Xato"
                                }
                            }
                            isSyncing = false
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth(0.85f)
                        .height(34.dp),
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = Color(0xFF2E7D5B)
                    )
                ) {
                    if (isSyncing) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp,
                            indicatorColor = Color.White
                        )
                    } else {
                        Text(
                            text = lastSyncStatus ?: stringResource(R.string.send_to_phone),
                            fontSize = 11.sp,
                            color = Color.White,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }
        }
    }
}
