package uz.wmax.watch.presentation

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.BatteryManager
import android.os.Bundle
import android.view.KeyEvent
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
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
import uz.wmax.watch.BuildConfig
import uz.wmax.watch.data.RawSensorSample
import uz.wmax.watch.datalayer.DataLayerSender
import uz.wmax.watch.network.WatchApiService
import uz.wmax.watch.network.WatchIngestBatchRequest
import uz.wmax.watch.network.WatchSosRaisePayload
import uz.wmax.watch.sensor.HealthServicesManager
import uz.wmax.watch.sensor.MeasureEvent
import uz.wmax.watch.sensor.SensorAggregator

class MainActivity : ComponentActivity() {

    private lateinit var healthServicesManager: HealthServicesManager
    private lateinit var aggregator: SensorAggregator
    private lateinit var dataSender: DataLayerSender
    private lateinit var watchApiService: WatchApiService
    private var collectionStarted = false

    // Hardware Side Button SOS Trigger listener
    private var onHardwareSosTriggered: (() -> Unit)? = null

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

        window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        healthServicesManager = HealthServicesManager(this)
        aggregator = SensorAggregator(this)
        dataSender = DataLayerSender(this)
        watchApiService = WatchApiService.create()

        checkAndRequestPermissions()

        setContent {
            MaterialTheme {
                WatchApp(
                    healthServicesManager = healthServicesManager,
                    dataSender = dataSender,
                    apiService = watchApiService,
                    registerHardwareSosCallback = { cb -> onHardwareSosTriggered = cb }
                )
            }
        }
    }

    /**
     * Intercept physical hardware side buttons on Samsung Galaxy Watch.
     * Back button / Bottom stem button acts as physical Hardware SOS trigger!
     */
    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK ||
            keyCode == KeyEvent.KEYCODE_STEM_1 ||
            keyCode == KeyEvent.KEYCODE_STEM_PRIMARY ||
            keyCode == KeyEvent.KEYCODE_STEM_2) {
            event?.startTracking()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun onKeyLongPress(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK ||
            keyCode == KeyEvent.KEYCODE_STEM_1 ||
            keyCode == KeyEvent.KEYCODE_STEM_PRIMARY ||
            keyCode == KeyEvent.KEYCODE_STEM_2) {
            vibrateDevice(this, 250)
            onHardwareSosTriggered?.invoke()
            return true
        }
        return super.onKeyLongPress(keyCode, event)
    }

    override fun onKeyUp(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK ||
            keyCode == KeyEvent.KEYCODE_STEM_1 ||
            keyCode == KeyEvent.KEYCODE_STEM_PRIMARY ||
            keyCode == KeyEvent.KEYCODE_STEM_2) {
            if (event?.isTracking == true && !event.isCanceled) {
                vibrateDevice(this, 120)
                onHardwareSosTriggered?.invoke()
                return true
            }
        }
        return super.onKeyUp(keyCode, event)
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

        var currentWornState = true

        // 1. Collect live stream from PPG, SpO2, and Hardware Off-Body sensors
        lifecycleScope.launch {
            try {
                healthServicesManager.sensorEventFlow().collect { event ->
                    when (event) {
                        is MeasureEvent.HeartRate -> {
                            aggregator.addSample(
                                RawSensorSample(
                                    timestampMs = System.currentTimeMillis(),
                                    hrBpm = if (currentWornState) event.bpm else null,
                                    rrIntervalMs = null,
                                    spo2Percent = null,
                                    skinTempCelsius = null,
                                    steps = 0,
                                    isWorn = currentWornState
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
                                    isWorn = currentWornState
                                )
                            )
                        }
                        is MeasureEvent.WornStatus -> {
                            currentWornState = event.isWorn
                        }
                        else -> Unit
                    }
                }
            } catch (e: Exception) {
                // Graceful fallback
            }
        }

        // 2. 5-minute aggregation window loop (Dispatches to companion phone & direct backend)
        lifecycleScope.launch {
            var firstWindow = true
            while (true) {
                // Flush the first window quickly after launch so pairing/configuration
                // can be verified immediately; subsequent windows remain five minutes.
                delay(if (firstWindow) 30 * 1000L else 5 * 60 * 1000L)
                firstWindow = false
                val reading = aggregator.computeAndDrainWindow() ?: continue
                android.util.Log.i("WmaxTelemetry", "Flushing reading to backend: ${reading.ts}")

                // 1st channel: Companion Phone via Google Play Data Layer
                launch {
                    dataSender.sendReading(reading)
                }

                // 2nd channel: Direct Wi-Fi/LTE ingestion to https://wmax.boos.uz/api/v1/ingest
                launch {
                    try {
                        val response = watchApiService.ingestBatch(
                            WatchIngestBatchRequest(
                                patientId = BuildConfig.WMAX_PATIENT_ID,
                                readings = listOf(reading)
                            )
                        )
                        android.util.Log.i("WmaxTelemetry", "Backend ingest response: ${response.code()}")
                    } catch (_: Exception) {}
                }
            }
        }
    }
}

/**
 * Main WMAX Wear OS Watch Face View.
 * Supports:
 * 1. AMOLED Circular Screen design with TimeText clearance.
 * 2. Hardware Off-Body Detection analysis ("Soat yechilgan • No Data" vs "Taqilgan • Monitoring faol").
 * 3. Physical Hardware Side Button SOS (distinct from Screen Touch SOS!).
 */
@Composable
fun WatchApp(
    healthServicesManager: HealthServicesManager,
    dataSender: DataLayerSender,
    apiService: WatchApiService,
    registerHardwareSosCallback: ((() -> Unit)) -> Unit
) {
    val context = LocalContext.current
    var heartRate by remember { mutableDoubleStateOf(74.0) }
    var spo2 by remember { mutableDoubleStateOf(98.0) }
    var skinTemp by remember { mutableDoubleStateOf(36.6) }
    var isWorn by remember { mutableStateOf(true) }
    var isPhoneConnected by remember { mutableStateOf(false) }
    var batteryPct by remember { mutableIntStateOf(88) }

    // SOS Stages: "idle", "touch_countdown", "touch_dispatched", "hardware_countdown", "hardware_dispatched"
    var sosStage by remember { mutableStateOf("idle") }
    var dispatchedSosId by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    // Register callback for hardware side button press
    LaunchedEffect(Unit) {
        registerHardwareSosCallback {
            if (sosStage == "idle") {
                sosStage = "hardware_countdown"
            }
        }
    }

    // Battery percentage updater
    LaunchedEffect(Unit) {
        val bm = context.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
        batteryPct = bm?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: 88
    }

    // Check phone connection status periodically
    LaunchedEffect(Unit) {
        while (true) {
            isPhoneConnected = dataSender.isPhoneConnected()
            delay(5000)
        }
    }

    // Live PPG heart rate & off-body observer
    LaunchedEffect(Unit) {
        try {
            healthServicesManager.sensorEventFlow().collect { event ->
                when (event) {
                    is MeasureEvent.HeartRate -> {
                        heartRate = event.bpm
                        isWorn = true
                    }
                    is MeasureEvent.SpO2 -> {
                        spo2 = event.percentage
                    }
                    is MeasureEvent.WornStatus -> {
                        if (!isWorn && event.isWorn) {
                            // Watch put back on wrist: haptic confirmation
                            vibrateDevice(context, 70)
                        }
                        isWorn = event.isWorn
                    }
                    else -> Unit
                }
            }
        } catch (_: Exception) {}
    }

    // ── STAGE 2A: SCREEN TOUCH COUNTDOWN SCREEN ─────────────────────────────
    if (sosStage == "touch_countdown") {
        SosCountdownConfirmScreen(
            onConfirmed = {
                scope.launch {
                    val dt = java.time.Instant.now().toString()
                    dataSender.sendSosImmediate(
                        uz.wmax.watch.data.SosDto(
                            patientId = BuildConfig.WMAX_PATIENT_ID,
                            source = "watch_button",
                            ts = dt
                        )
                    )
                    try {
                        val resp = apiService.raiseSos(
                            payload = WatchSosRaisePayload(
                                patientId = BuildConfig.WMAX_PATIENT_ID,
                                source = "watch_button"
                            )
                        )
                        if (resp.isSuccessful) {
                            dispatchedSosId = resp.body()?.id
                        }
                    } catch (_: Exception) {}
                    sosStage = "touch_dispatched"
                }
            },
            onCancelled = {
                sosStage = "idle"
            }
        )
        return
    }

    // ── STAGE 3A: SCREEN TOUCH DISPATCHED SCREEN ────────────────────────────
    if (sosStage == "touch_dispatched") {
        SosDispatchedScreen(
            onCancelRequested = {
                scope.launch {
                    dispatchedSosId?.let { id ->
                        try {
                            apiService.cancelSos(id)
                        } catch (_: Exception) {}
                    }
                    sosStage = "idle"
                }
            },
            onDone = {
                sosStage = "idle"
            }
        )
        return
    }

    // ── STAGE 2B: DISTINCT HARDWARE SIDE BUTTON COUNTDOWN SCREEN ───────────
    if (sosStage == "hardware_countdown") {
        HardwareSosCountdownScreen(
            currentHr = heartRate,
            currentSpo2 = spo2,
            onConfirmed = {
                scope.launch {
                    val dt = java.time.Instant.now().toString()
                    dataSender.sendSosImmediate(
                        uz.wmax.watch.data.SosDto(
                            patientId = BuildConfig.WMAX_PATIENT_ID,
                            source = "watch_button", // Conforms to openapi literal while distinguished by hardware flow
                            ts = dt
                        )
                    )
                    try {
                        val resp = apiService.raiseSos(
                            payload = WatchSosRaisePayload(
                                patientId = BuildConfig.WMAX_PATIENT_ID,
                                source = "watch_button"
                            )
                        )
                        if (resp.isSuccessful) {
                            dispatchedSosId = resp.body()?.id
                        }
                    } catch (_: Exception) {}
                    sosStage = "hardware_dispatched"
                }
            },
            onCancelled = {
                sosStage = "idle"
            }
        )
        return
    }

    // ── STAGE 3B: DISTINCT HARDWARE SIDE BUTTON DISPATCHED SCREEN ──────────
    if (sosStage == "hardware_dispatched") {
        HardwareSosDispatchedScreen(
            onCancelRequested = {
                scope.launch {
                    dispatchedSosId?.let { id ->
                        try {
                            apiService.cancelSos(id)
                        } catch (_: Exception) {}
                    }
                    sosStage = "idle"
                }
            },
            onDone = {
                sosStage = "idle"
            }
        )
        return
    }

    // ── STAGE 1: MAIN AMOLED CIRCULAR WATCH FACE ───────────────────────────
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.92f,
        targetValue = 1.18f,
        animationSpec = infiniteRepeatable(
            animation = tween(
                durationMillis = (60000 / heartRate.coerceIn(40.0, 180.0)).toInt(),
                easing = FastOutSlowInEasing
            ),
            repeatMode = RepeatMode.Reverse
        ),
        label = "heartPulse"
    )

    val hrColor = when {
        heartRate > 115 || heartRate < 50 -> Color(0xFFEF4444) // Risk red
        heartRate > 95 -> Color(0xFFF59E0B)                    // Attention amber
        else -> Color.White                                    // Crisp white
    }

    Scaffold(
        timeText = { TimeText() },
        modifier = Modifier.background(Color.Black)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black)
                .padding(horizontal = 16.dp, vertical = 12.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
                modifier = Modifier.fillMaxSize()
            ) {
                // Top margin to ensure no overlap with curved TimeText
                Spacer(modifier = Modifier.height(24.dp))

                // 1. TOP STATUS CAPSULE (Connection + Battery)
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center,
                    modifier = Modifier
                        .background(Color(0xFF0F172A), RoundedCornerShape(14.dp))
                        .padding(horizontal = 10.dp, vertical = 3.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(7.dp)
                            .background(
                                if (isPhoneConnected) Color(0xFF10B981) else Color(0xFFF59E0B),
                                CircleShape
                            )
                    )
                    Spacer(modifier = Modifier.width(5.dp))
                    Text(
                        text = if (isPhoneConnected) stringResource(R.string.status_connected)
                        else stringResource(R.string.status_disconnected),
                        fontSize = 11.sp,
                        color = Color(0xFFCBD5E1),
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "•",
                        fontSize = 10.sp,
                        color = Color(0xFF64748B)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "$batteryPct%",
                        fontSize = 11.sp,
                        color = Color(0xFF94A3B8),
                        fontWeight = FontWeight.Bold
                    )
                }

                Spacer(modifier = Modifier.height(6.dp))

                // 2. HERO SECTION: WORN (Live Pulse) VS OFF-BODY (Analysis Alert)
                if (!isWorn) {
                    // ── OFF-BODY DETECTED: CLINICAL NO-DATA VIEW ──
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = stringResource(R.string.watch_removed_title),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Black,
                            color = Color(0xFFFCD34D),
                            letterSpacing = 0.5.sp
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = stringResource(R.string.watch_removed_desc),
                            fontSize = 10.sp,
                            color = Color(0xFFE2E8F0),
                            textAlign = TextAlign.Center
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Box(
                            modifier = Modifier
                                .background(Color(0xFF1E1B1B), RoundedCornerShape(8.dp))
                                .padding(horizontal = 12.dp, vertical = 3.dp)
                        ) {
                            Text(
                                text = "-- bpm",
                                fontSize = 24.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF94A3B8)
                            )
                        }
                    }
                } else {
                    // ── ON-BODY: LIVE CARDIAC PULSE & VITALS ──
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Box(
                            modifier = Modifier
                                .size(30.dp)
                                .scale(pulseScale),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "❤️",
                                fontSize = 20.sp
                            )
                        }
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "%.0f".format(heartRate),
                            fontSize = 52.sp,
                            fontWeight = FontWeight.Black,
                            color = hrColor,
                            letterSpacing = (-1.5).sp
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Column(horizontalAlignment = Alignment.Start) {
                            Text(
                                text = stringResource(R.string.bpm),
                                fontSize = 12.sp,
                                color = Color(0xFFFCA5A5),
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = stringResource(R.string.heart_rate),
                                fontSize = 8.5.sp,
                                color = Color(0xFF94A3B8),
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(4.dp))

                    // Secondary Vitals Row (SpO2 & Skin Temperature Capsules)
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        // SpO2 Capsule
                        Box(
                            modifier = Modifier
                                .background(Color(0xFF0F172A), RoundedCornerShape(10.dp))
                                .padding(horizontal = 8.dp, vertical = 3.5.dp)
                        ) {
                            Text(
                                text = "SpO2 %.0f%%".format(spo2),
                                fontSize = 11.5.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (spo2 < 93) Color(0xFFEF4444) else Color(0xFF38BDF8)
                            )
                        }
                        Spacer(modifier = Modifier.width(6.dp))

                        // Skin Temp Capsule
                        Box(
                            modifier = Modifier
                                .background(Color(0xFF0F172A), RoundedCornerShape(10.dp))
                                .padding(horizontal = 8.dp, vertical = 3.5.dp)
                        ) {
                            Text(
                                text = "%.1f°C".format(skinTemp),
                                fontSize = 11.5.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFFF59E0B)
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                // 3. SENSOR WORN / OFF-BODY STATUS PILL
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center,
                    modifier = Modifier
                        .background(
                            if (isWorn) Color(0xFF141E2E) else Color(0xFF331800),
                            RoundedCornerShape(10.dp)
                        )
                        .padding(horizontal = 8.dp, vertical = 2.5.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(5.dp)
                            .background(
                                if (isWorn) Color(0xFF10B981) else Color(0xFFF59E0B),
                                CircleShape
                            )
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = if (isWorn) "${stringResource(R.string.sensor_worn)} • ${stringResource(R.string.monitoring_active)}"
                        else stringResource(R.string.no_data_warning),
                        fontSize = 9.5.sp,
                        color = if (isWorn) Color(0xFF6EE7B7) else Color(0xFFFCD34D),
                        fontWeight = FontWeight.SemiBold
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                // 4. PROMINENT CIRCULAR TOUCH SOS BUTTON
                SosHoldButton(
                    onTriggerCountdown = {
                        sosStage = "touch_countdown"
                    }
                )
            }
        }
    }
}
