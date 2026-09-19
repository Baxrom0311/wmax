package uz.wmax.phone.presentation

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.android.gms.wearable.Wearable
import com.google.gson.Gson
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import uz.wmax.phone.R
import uz.wmax.phone.data.db.AppDatabase
import uz.wmax.phone.data.model.ReadingInModel
import uz.wmax.phone.network.PatientLoginPayload
import uz.wmax.phone.network.SosRaisePayload
import uz.wmax.phone.network.WmaxApiService
import uz.wmax.phone.sync.SyncWorker

// ── Design tokens ─────────────────────────────────────────────────────────────
private val WmaxGreen    = Color(0xFF2E7D5B)
private val WmaxGreenBg  = Color(0xFFECFDF5)
private val WmaxAmber    = Color(0xFFC77A0A)
private val WmaxAmberBg  = Color(0xFFFFFBEB)
private val WmaxRed      = Color(0xFFB3261E)
private val WmaxRedBg    = Color(0xFFFFF1F0)
private val WmaxSky      = Color(0xFF0EA5E9)
private val WmaxSkyBg    = Color(0xFFE0F2FE)
private val WmaxPurple   = Color(0xFF7C3AED)
private val WmaxPurpleBg = Color(0xFFF3E8FF)
private val BgPage       = Color(0xFFF4F6F8)
private val SurfaceCard  = Color(0xFFFFFFFF)
private val TextPri      = Color(0xFF0F172A)
private val TextSec      = Color(0xFF64748B)
private val TextMuted    = Color(0xFF94A3B8)
private val BorderLine   = Color(0xFFE2E8F0)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val database   = AppDatabase.getInstance(this)
        val readingDao = database.readingDao()
        setContent {
            MaterialTheme {
                PhoneApp(readingDao = readingDao)
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PhoneApp(readingDao: uz.wmax.phone.data.db.ReadingDao) {
    val context = LocalContext.current
    val prefs   = remember { context.getSharedPreferences("wmax_phone_prefs", Context.MODE_PRIVATE) }
    var backendUrl by remember {
        mutableStateOf(prefs.getString("backend_url", WmaxApiService.DEFAULT_BASE_URL) ?: WmaxApiService.DEFAULT_BASE_URL)
    }

    var patientId    by remember { mutableStateOf(prefs.getString("patient_id", null)) }
    var patientName  by remember { mutableStateOf(prefs.getString("patient_name", null)) }
    var accessToken  by remember { mutableStateOf(prefs.getString("access_token", null)) }

    val isLoggedIn = !patientId.isNullOrBlank()

    var phone        by remember { mutableStateOf("") }
    var pin          by remember { mutableStateOf("") }
    var authStatus   by remember { mutableStateOf<String?>(null) }
    var authError    by remember { mutableStateOf(false) }
    var isLoggingIn  by remember { mutableStateOf(false) }
    val scope        = rememberCoroutineScope()

    var showLogoutDialog by remember { mutableStateOf(false) }
    var showSosDialog    by remember { mutableStateOf(false) }
    var isSendingSos     by remember { mutableStateOf(false) }
    var sosFeedback      by remember { mutableStateOf<Pair<String, Boolean>?>(null) }

    var connectedWatchName by remember { mutableStateOf<String?>(null) }
    var isSyncing          by remember { mutableStateOf(false) }

    val unsyncedCount    by readingDao.getUnsyncedCountFlow().collectAsState(initial = 0)
    val latestReadingEnt by readingDao.getLatestReadingFlow().collectAsState(initial = null)
    val gson             = remember { Gson() }
    val latestReading: ReadingInModel? = remember(latestReadingEnt) {
        latestReadingEnt?.let { runCatching { gson.fromJson(it.payloadJson, ReadingInModel::class.java) }.getOrNull() }
    }

    // Monitor connected watch nodes only when logged in
    LaunchedEffect(isLoggedIn) {
        if (!isLoggedIn) {
            connectedWatchName = null
            return@LaunchedEffect
        }
        while (true) {
            runCatching {
                val nodes = Wearable.getNodeClient(context).connectedNodes.await()
                connectedWatchName = nodes.firstOrNull()?.displayName
            }.onFailure { connectedWatchName = null }
            delay(5_000)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .background(
                                    brush = Brush.horizontalGradient(listOf(WmaxGreen, Color(0xFF059669))),
                                    shape = RoundedCornerShape(6.dp)
                                )
                                .padding(horizontal = 8.dp, vertical = 3.dp)
                        ) {
                            Text("W", color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp)
                        }
                        Spacer(Modifier.width(8.dp))
                        Text(
                            stringResource(R.string.app_name),
                            fontWeight = FontWeight.Bold,
                            color = TextPri,
                            fontSize = 18.sp
                        )
                    }
                },
                actions = {
                    if (isLoggedIn) {
                        TextButton(
                            onClick = { showLogoutDialog = true },
                            colors = ButtonDefaults.textButtonColors(contentColor = WmaxRed)
                        ) {
                            Text(
                                stringResource(R.string.btn_logout),
                                fontWeight = FontWeight.SemiBold,
                                fontSize = 13.sp
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = SurfaceCard,
                    titleContentColor = TextPri
                )
            )
        },
        containerColor = BgPage
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            if (!isLoggedIn) {
                // ── SCREEN 1: ONLY Promo (Watch capabilities) & Login Form ──
                // ZERO watch connection, ZERO vitals, ZERO queue!
                OnboardingAndLoginScreen(
                    backendUrl     = backendUrl,
                    onUrlChange    = { newUrl ->
                        backendUrl = newUrl
                        prefs.edit().putString("backend_url", newUrl).apply()
                    },
                    phone          = phone,
                    onPhoneChange  = { phone = it },
                    pin            = pin,
                    onPinChange    = { pin = it },
                    isLoggingIn    = isLoggingIn,
                    authStatus     = authStatus,
                    authError      = authError,
                    onLogin        = {
                        scope.launch {
                            isLoggingIn = true
                            authStatus  = null
                            authError   = false
                            try {
                                val api    = WmaxApiService.create(backendUrl)
                                val resp   = api.patientLogin(PatientLoginPayload(phone.trim(), pin.trim()))
                                val tokens = resp.body()
                                if (!resp.isSuccessful || tokens == null || tokens.role != "patient") {
                                    throw IllegalStateException("HTTP ${resp.code()}")
                                }
                                val me = api.getMe("Bearer ${tokens.access_token}")
                                val p  = me.body()
                                if (!me.isSuccessful || p == null || p.role != "patient") {
                                    throw IllegalStateException("Profile unavailable")
                                }
                                patientId   = p.id
                                patientName = p.full_name
                                accessToken = tokens.access_token

                                prefs.edit()
                                    .putString("backend_url",    backendUrl)
                                    .putString("patient_id",     p.id)
                                    .putString("patient_name",   p.full_name)
                                    .putString("access_token",   tokens.access_token)
                                    .putString("refresh_token",  tokens.refresh_token)
                                    .apply()
                                pin        = ""
                                authStatus = context.getString(R.string.login_success, p.full_name)
                            } catch (e: Exception) {
                                authError  = true
                                authStatus = context.getString(R.string.login_failed)
                            } finally {
                                isLoggingIn = false
                            }
                        }
                    }
                )
            } else {
                // ── SCREEN 2: Dashboard ONLY after login ──
                // Watch status, latest vitals, queue buffer, SOS
                AuthenticatedDashboard(
                    patientId          = patientId ?: "",
                    patientName        = patientName ?: "",
                    connectedWatchName = connectedWatchName,
                    latestReading      = latestReading,
                    unsyncedCount      = unsyncedCount,
                    isSyncing          = isSyncing,
                    onSyncRequested    = {
                        isSyncing = true
                        SyncWorker.enqueueSync(context, expedited = true)
                        scope.launch {
                            delay(1000)
                            isSyncing = false
                        }
                    },
                    onLogoutClicked    = { showLogoutDialog = true },
                    onSosClicked       = { showSosDialog = true },
                    sosFeedback        = sosFeedback
                )
            }
        }
    }

    // ── Logout confirmation dialog ───────────────────────────────────────────
    if (showLogoutDialog) {
        AlertDialog(
            onDismissRequest = { showLogoutDialog = false },
            title = { Text(stringResource(R.string.logout_dialog_title), fontWeight = FontWeight.Bold) },
            text  = { Text(stringResource(R.string.logout_dialog_msg), color = TextSec) },
            confirmButton = {
                Button(
                    onClick = {
                        showLogoutDialog = false
                        patientId   = null
                        patientName = null
                        accessToken = null
                        prefs.edit()
                            .remove("patient_id")
                            .remove("patient_name")
                            .remove("access_token")
                            .remove("refresh_token")
                            .apply()
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = WmaxRed)
                ) {
                    Text(stringResource(R.string.btn_logout))
                }
            },
            dismissButton = {
                TextButton(onClick = { showLogoutDialog = false }) {
                    Text(stringResource(R.string.btn_cancel), color = TextSec)
                }
            }
        )
    }

    // ── Emergency SOS confirmation dialog ────────────────────────────────────
    if (showSosDialog) {
        AlertDialog(
            onDismissRequest = { if (!isSendingSos) showSosDialog = false },
            title = { Text(stringResource(R.string.sos_dialog_title), fontWeight = FontWeight.Bold, color = WmaxRed) },
            text  = { Text(stringResource(R.string.sos_dialog_msg), color = TextSec) },
            confirmButton = {
                Button(
                    enabled = !isSendingSos,
                    onClick = {
                        scope.launch {
                            isSendingSos = true
                            try {
                                val api = WmaxApiService.create(backendUrl)
                                val authHeader = if (!accessToken.isNullOrBlank()) "Bearer $accessToken" else ""
                                val resp = api.raiseSos(
                                    authorization = authHeader,
                                    req = SosRaisePayload(
                                        patient_id = patientId ?: "",
                                        source = "phone_app"
                                    )
                                )
                                if (resp.isSuccessful) {
                                    sosFeedback = Pair(context.getString(R.string.sos_success), true)
                                } else {
                                    sosFeedback = Pair(context.getString(R.string.sos_failed), false)
                                }
                            } catch (e: Exception) {
                                sosFeedback = Pair(context.getString(R.string.sos_failed), false)
                            } finally {
                                isSendingSos = false
                                showSosDialog = false
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = WmaxRed)
                ) {
                    if (isSendingSos) {
                        CircularProgressIndicator(Modifier.size(16.dp), color = Color.White, strokeWidth = 2.dp)
                        Spacer(Modifier.width(8.dp))
                        Text(stringResource(R.string.sos_sending))
                    } else {
                        Text(stringResource(R.string.btn_confirm))
                    }
                }
            },
            dismissButton = {
                TextButton(
                    enabled = !isSendingSos,
                    onClick = { showSosDialog = false }
                ) {
                    Text(stringResource(R.string.btn_cancel), color = TextSec)
                }
            }
        )
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// ONBOARDING & PROMO SCREEN (Seen before login)
// Shows full capabilities of the smartwatch and system, then Login form.
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun OnboardingAndLoginScreen(
    backendUrl:     String,
    onUrlChange:    (String) -> Unit,
    phone:          String,
    onPhoneChange:  (String) -> Unit,
    pin:            String,
    onPinChange:    (String) -> Unit,
    isLoggingIn:    Boolean,
    authStatus:     String?,
    authError:      Boolean,
    onLogin:        () -> Unit
) {
    var showSettings by remember { mutableStateOf(false) }
    var tempUrl by remember(backendUrl) { mutableStateOf(backendUrl) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // ── 1. Hero Promo Banner ─────────────────────────────────────────────
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape    = RoundedCornerShape(20.dp),
            colors   = CardDefaults.cardColors(containerColor = SurfaceCard),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(
                        brush = Brush.verticalGradient(
                            listOf(WmaxGreenBg, Color.White)
                        )
                    )
                    .padding(20.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text       = stringResource(R.string.onboarding_title),
                        fontSize   = 20.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color      = TextPri,
                        lineHeight = 26.sp
                    )
                    Text(
                        text       = stringResource(R.string.onboarding_desc),
                        fontSize   = 13.sp,
                        color      = TextSec,
                        lineHeight = 18.sp
                    )
                }
            }
        }

        // ── 2. "Aqlli soat nima qila oladi?" (8 ta to'liq imkoniyat) ─────────
        Text(
            text       = stringResource(R.string.features_section_title).uppercase(),
            fontSize   = 12.sp,
            fontWeight = FontWeight.ExtraBold,
            color      = WmaxGreen,
            letterSpacing = 1.sp,
            modifier   = Modifier.padding(start = 4.dp, top = 4.dp)
        )

        // 1. Ixtiyoriy Wear OS soat
        FeatureCard(
            icon        = "⌚",
            iconBg      = WmaxGreenBg,
            title       = stringResource(R.string.watch_cap_universal_title),
            description = stringResource(R.string.watch_cap_universal_desc)
        )

        // 2. Doimiy Puls va Aritmiya
        FeatureCard(
            icon        = "❤️",
            iconBg      = WmaxRedBg,
            title       = stringResource(R.string.watch_cap_hr_title),
            description = stringResource(R.string.watch_cap_hr_desc)
        )

        // 3. SpO2 — Qondagi kislorod
        FeatureCard(
            icon        = "🫁",
            iconBg      = WmaxSkyBg,
            title       = stringResource(R.string.watch_cap_spo2_title),
            description = stringResource(R.string.watch_cap_spo2_desc)
        )

        // 4. HRV va Stress / Charchoq indeksi
        FeatureCard(
            icon        = "📊",
            iconBg      = WmaxPurpleBg,
            title       = stringResource(R.string.watch_cap_hrv_title),
            description = stringResource(R.string.watch_cap_hrv_desc)
        )

        // 5. Harorat va Nafas chastotasi
        FeatureCard(
            icon        = "🌡️",
            iconBg      = WmaxAmberBg,
            title       = stringResource(R.string.watch_cap_temp_title),
            description = stringResource(R.string.watch_cap_temp_desc)
        )

        // 6. AI Erta Ogohlantirish (DekomMode)
        FeatureCard(
            icon        = "🧠",
            iconBg      = WmaxGreenBg,
            title       = stringResource(R.string.watch_cap_ai_title),
            description = stringResource(R.string.watch_cap_ai_desc)
        )

        // 7. Bir bosishda SOS chaqiruv
        FeatureCard(
            icon        = "🚨",
            iconBg      = WmaxRedBg,
            title       = stringResource(R.string.watch_cap_sos_title),
            description = stringResource(R.string.watch_cap_sos_desc)
        )

        // 8. Oflayn rejim
        FeatureCard(
            icon        = "🛡️",
            iconBg      = WmaxSkyBg,
            title       = stringResource(R.string.watch_cap_offline_title),
            description = stringResource(R.string.watch_cap_offline_desc)
        )

        // ── 3. Login Section ─────────────────────────────────────────────────
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape    = RoundedCornerShape(18.dp),
            colors   = CardDefaults.cardColors(containerColor = SurfaceCard),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text       = stringResource(R.string.login_section_title),
                        fontSize   = 17.sp,
                        fontWeight = FontWeight.Bold,
                        color      = TextPri
                    )
                    Text(
                        text       = stringResource(R.string.login_section_subtitle),
                        fontSize   = 12.sp,
                        color      = TextSec
                    )
                }

                OutlinedTextField(
                    value        = phone,
                    onValueChange = onPhoneChange,
                    label        = { Text(stringResource(R.string.phone_label), fontSize = 13.sp) },
                    placeholder  = { Text("+998 -- --- -- --", color = TextMuted) },
                    modifier     = Modifier.fillMaxWidth(),
                    singleLine   = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                    colors       = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor   = WmaxGreen,
                        unfocusedBorderColor = BorderLine,
                        focusedLabelColor    = WmaxGreen
                    ),
                    shape = RoundedCornerShape(12.dp)
                )

                OutlinedTextField(
                    value        = pin,
                    onValueChange = onPinChange,
                    label        = { Text(stringResource(R.string.pin_label), fontSize = 13.sp) },
                    placeholder  = { Text("• • • • • •", color = TextMuted) },
                    modifier     = Modifier.fillMaxWidth(),
                    singleLine   = true,
                    keyboardOptions      = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    visualTransformation = PasswordVisualTransformation(),
                    colors       = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor   = WmaxGreen,
                        unfocusedBorderColor = BorderLine,
                        focusedLabelColor    = WmaxGreen
                    ),
                    shape = RoundedCornerShape(12.dp)
                )

                Button(
                    onClick  = onLogin,
                    enabled  = !isLoggingIn && phone.isNotBlank() && pin.isNotBlank(),
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                    colors   = ButtonDefaults.buttonColors(
                        containerColor = WmaxGreen,
                        disabledContainerColor = BorderLine
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    if (isLoggingIn) {
                        CircularProgressIndicator(Modifier.size(18.dp), color = Color.White, strokeWidth = 2.dp)
                        Spacer(Modifier.width(10.dp))
                        Text(stringResource(R.string.btn_logging_in), fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                    } else {
                        Text(stringResource(R.string.login_action), fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                    }
                }

                authStatus?.let {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(if (authError) WmaxRedBg else WmaxGreenBg)
                            .padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text       = it,
                            fontSize   = 13.sp,
                            color      = if (authError) WmaxRed else WmaxGreen,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }

                // Server settings toggle
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { showSettings = !showSettings }
                        .padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        stringResource(R.string.advanced_settings_title),
                        fontSize = 12.sp,
                        color = TextSec
                    )
                    Text(
                        if (showSettings) "▲" else "▼",
                        fontSize = 10.sp,
                        color = TextMuted
                    )
                }

                if (showSettings) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(BgPage)
                            .padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        OutlinedTextField(
                            value = tempUrl,
                            onValueChange = { tempUrl = it },
                            label = { Text(stringResource(R.string.backend_url_label), fontSize = 11.sp) },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = WmaxGreen,
                                unfocusedBorderColor = BorderLine
                            ),
                            shape = RoundedCornerShape(8.dp)
                        )
                        Button(
                            onClick = {
                                onUrlChange(tempUrl.trim())
                                showSettings = false
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = WmaxGreen),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.align(Alignment.End)
                        ) {
                            Text(stringResource(R.string.btn_save_url), fontSize = 12.sp)
                        }
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))
    }
}

@Composable
private fun FeatureCard(
    icon:        String,
    iconBg:      Color,
    title:       String,
    description: String
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape    = RoundedCornerShape(16.dp),
        colors   = CardDefaults.cardColors(containerColor = SurfaceCard),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.Top,
            horizontalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(iconBg),
                contentAlignment = Alignment.Center
            ) {
                Text(icon, fontSize = 22.sp)
            }
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text(
                    text       = title,
                    fontSize   = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color      = TextPri
                )
                Text(
                    text       = description,
                    fontSize   = 12.sp,
                    color      = TextSec,
                    lineHeight = 17.sp
                )
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// AUTHENTICATED DASHBOARD (Seen ONLY after login)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun AuthenticatedDashboard(
    patientId:          String,
    patientName:        String,
    connectedWatchName: String?,
    latestReading:      ReadingInModel?,
    unsyncedCount:      Int,
    isSyncing:          Boolean,
    onSyncRequested:    () -> Unit,
    onLogoutClicked:    () -> Unit,
    onSosClicked:       () -> Unit,
    sosFeedback:        Pair<String, Boolean>?
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // ── 1. Patient Profile Header (Clean, no useless indicators!) ────────
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape    = RoundedCornerShape(16.dp),
            colors   = CardDefaults.cardColors(containerColor = SurfaceCard),
            elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
        ) {
            Row(
                modifier = Modifier.padding(16.dp).fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(46.dp)
                        .clip(CircleShape)
                        .background(WmaxGreen),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = patientName.firstOrNull()?.uppercase() ?: "P",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 20.sp
                    )
                }
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = patientName,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextPri
                    )
                    Text(
                        text = stringResource(R.string.patient_id_label, patientId.take(13) + "…"),
                        fontSize = 12.sp,
                        color = TextMuted
                    )
                }
                OutlinedButton(
                    onClick = onLogoutClicked,
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                ) {
                    Text(
                        stringResource(R.string.btn_logout),
                        fontSize = 12.sp,
                        color = WmaxRed
                    )
                }
            }
        }

        // ── 2. SOS feedback notification if any ──────────────────────────────
        sosFeedback?.let { (msg, isSuccess) ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(if (isSuccess) WmaxGreenBg else WmaxRedBg)
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text       = msg,
                    fontSize   = 13.sp,
                    fontWeight = FontWeight.SemiBold,
                    color      = if (isSuccess) WmaxGreen else WmaxRed
                )
            }
        }

        // ── 3. Watch Status Card (After login!) ──────────────────────────────
        WatchStatusCard(connectedWatchName)

        // ── 4. Latest Vitals Card (After login!) ─────────────────────────────
        VitalsCard(latestReading)

        // ── 5. Unsynced Queue Buffer Card (After login!) ─────────────────────
        QueueCard(unsyncedCount, isSyncing, onSyncRequested)

        // ── 6. Emergency SOS Call Card (After login!) ────────────────────────
        SosActionCard(onSosClicked = onSosClicked)

        Spacer(Modifier.height(20.dp))
    }
}

// ── Section Container ────────────────────────────────────────────────────────
@Composable
private fun SectionCard(
    label: String,
    labelColor: Color = WmaxGreen,
    content: @Composable ColumnScope.() -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape    = RoundedCornerShape(16.dp),
        colors   = CardDefaults.cardColors(containerColor = SurfaceCard),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Column(modifier = Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(
                text       = label.uppercase(),
                fontSize   = 10.sp,
                fontWeight = FontWeight.Bold,
                color      = labelColor,
                letterSpacing = 1.sp
            )
            content()
        }
    }
}

// ── Card 1: Watch Status (Clean, no dummy blinking dots!) ────────────────────
@Composable
private fun WatchStatusCard(connectedWatchName: String?) {
    val isConnected = connectedWatchName != null

    Card(
        modifier  = Modifier.fillMaxWidth(),
        shape     = RoundedCornerShape(16.dp),
        colors    = CardDefaults.cardColors(containerColor = if (isConnected) WmaxGreenBg else WmaxRedBg),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Row(
            modifier            = Modifier.padding(18.dp).fillMaxWidth(),
            verticalAlignment   = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text       = stringResource(R.string.watch_status_label).uppercase(),
                    fontSize   = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color      = if (isConnected) WmaxGreen else WmaxRed,
                    letterSpacing = 1.sp
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text       = if (isConnected) "⌚  $connectedWatchName" else "⌚  " + stringResource(R.string.watch_disconnected),
                    fontSize   = 15.sp,
                    fontWeight = FontWeight.SemiBold,
                    color      = TextPri
                )
                Text(
                    text     = if (isConnected) "Ma'lumotlar qabul qilinmoqda" else "Soatingizni telefonga yaqinlashtiring",
                    fontSize = 12.sp,
                    color    = TextSec
                )
            }
            Text(
                text = if (isConnected) stringResource(R.string.watch_connected) else stringResource(R.string.watch_disconnected),
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = if (isConnected) WmaxGreen else WmaxRed
            )
        }
    }
}

// ── Card 2: Vitals ────────────────────────────────────────────────────────────
@Composable
private fun VitalsCard(reading: ReadingInModel?) {
    SectionCard(label = stringResource(R.string.vitals_card_label)) {
        if (reading != null) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                VitalChip(
                    modifier = Modifier.weight(1f),
                    label    = stringResource(R.string.vitals_hr),
                    value    = reading.hrMean?.let { "%.0f".format(it) } ?: "--",
                    unit     = "bpm",
                    chipBg   = WmaxRedBg,
                    valueColor = WmaxRed
                )
                VitalChip(
                    modifier = Modifier.weight(1f),
                    label    = stringResource(R.string.vitals_spo2),
                    value    = reading.spo2?.let { "%.1f".format(it) } ?: "--",
                    unit     = "%",
                    chipBg   = WmaxSkyBg,
                    valueColor = WmaxSky
                )
                VitalChip(
                    modifier = Modifier.weight(1f),
                    label    = stringResource(R.string.vitals_steps),
                    value    = reading.steps?.toString() ?: "0",
                    unit     = "",
                    chipBg   = WmaxGreenBg,
                    valueColor = WmaxGreen
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text      = if (reading.worn) "⌚ " + stringResource(R.string.vitals_worn_yes) else "✗ " + stringResource(R.string.vitals_worn_no),
                    fontSize  = 12.sp,
                    color     = if (reading.worn) WmaxGreen else TextSec,
                    fontWeight = FontWeight.Medium
                )
                Text(
                    text     = reading.ts.take(16).replace("T", "  "),
                    fontSize = 11.sp,
                    color    = TextMuted
                )
            }
        } else {
            Box(
                modifier          = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                contentAlignment  = Alignment.Center
            ) {
                Text(
                    text     = stringResource(R.string.vitals_waiting),
                    fontSize = 13.sp,
                    color    = TextMuted,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}

@Composable
private fun VitalChip(
    modifier:   Modifier,
    label:      String,
    value:      String,
    unit:       String,
    chipBg:     Color,
    valueColor: Color
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(10.dp))
            .background(chipBg)
            .padding(horizontal = 10.dp, vertical = 10.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(label, fontSize = 10.sp, color = TextSec, fontWeight = FontWeight.Medium)
        Spacer(Modifier.height(4.dp))
        Text(value, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = valueColor)
        if (unit.isNotBlank()) {
            Text(unit, fontSize = 10.sp, color = TextMuted)
        }
    }
}

// ── Card 3: Queue ─────────────────────────────────────────────────────────────
@Composable
private fun QueueCard(unsyncedCount: Int, isSyncing: Boolean, onSyncRequested: () -> Unit) {
    val empty = unsyncedCount == 0
    SectionCard(
        label = stringResource(R.string.queue_card_label),
        labelColor = if (empty) WmaxGreen else WmaxAmber
    ) {
        Row(
            modifier              = Modifier.fillMaxWidth(),
            verticalAlignment     = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text       = if (empty) stringResource(R.string.queue_empty) else stringResource(R.string.queue_items, unsyncedCount),
                    fontSize   = 15.sp,
                    fontWeight = FontWeight.SemiBold,
                    color      = if (empty) WmaxGreen else WmaxAmber
                )
                Text(
                    text     = if (empty) "Server bilan sinxron" else "Internet ulanganda avtomatik yuboriladi",
                    fontSize = 11.sp,
                    color    = TextSec,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
            Spacer(Modifier.width(12.dp))
            if (!empty) {
                Button(
                    onClick = onSyncRequested,
                    enabled = !isSyncing,
                    colors  = ButtonDefaults.buttonColors(containerColor = WmaxGreen),
                    shape   = RoundedCornerShape(10.dp),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 10.dp)
                ) {
                    if (isSyncing) {
                        CircularProgressIndicator(Modifier.size(14.dp), color = Color.White, strokeWidth = 2.dp)
                    } else {
                        Text(stringResource(R.string.btn_sync), fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}

// ── Card 4: SOS Action ────────────────────────────────────────────────────────
@Composable
private fun SosActionCard(onSosClicked: () -> Unit) {
    Card(
        modifier  = Modifier.fillMaxWidth(),
        shape     = RoundedCornerShape(16.dp),
        colors    = CardDefaults.cardColors(containerColor = WmaxRedBg),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(
                text       = stringResource(R.string.sos_card_title).uppercase(),
                fontSize   = 10.sp,
                fontWeight = FontWeight.Bold,
                color      = WmaxRed,
                letterSpacing = 1.sp
            )
            Button(
                onClick  = onSosClicked,
                modifier = Modifier.fillMaxWidth().height(48.dp),
                colors   = ButtonDefaults.buttonColors(containerColor = WmaxRed),
                shape    = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text       = stringResource(R.string.sos_btn_label),
                    fontSize   = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color      = Color.White
                )
            }
        }
    }
}
