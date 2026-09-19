package uz.wmax.phone.presentation

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.android.gms.wearable.Wearable
import com.google.gson.Gson
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import uz.wmax.phone.data.db.AppDatabase
import uz.wmax.phone.data.model.ReadingInModel
import uz.wmax.phone.network.WmaxApiService
import uz.wmax.phone.network.PatientLoginPayload
import uz.wmax.phone.sync.SyncWorker

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val database = AppDatabase.getInstance(this)
        val readingDao = database.readingDao()

        setContent {
            MaterialTheme {
                PhoneApp(readingDao = readingDao)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PhoneApp(readingDao: uz.wmax.phone.data.db.ReadingDao) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("wmax_phone_prefs", Context.MODE_PRIVATE) }

    var backendUrl by remember {
        mutableStateOf(prefs.getString("backend_url", WmaxApiService.DEFAULT_BASE_URL) ?: WmaxApiService.DEFAULT_BASE_URL)
    }
    var patientId by remember { mutableStateOf(prefs.getString("patient_id", null)) }
    var phone by remember { mutableStateOf("") }
    var pin by remember { mutableStateOf("") }
    var ingestKey by remember { mutableStateOf(prefs.getString("ingest_api_key", "") ?: "") }
    var authStatus by remember { mutableStateOf<String?>(null) }
    var isLoggingIn by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    var connectedWatchName by remember { mutableStateOf<String?>(null) }
    var isSyncing by remember { mutableStateOf(false) }

    val unsyncedCount by readingDao.getUnsyncedCountFlow().collectAsState(initial = 0)
    val latestReadingEntity by readingDao.getLatestReadingFlow().collectAsState(initial = null)

    val gson = remember { Gson() }
    val latestReading: ReadingInModel? = remember(latestReadingEntity) {
        latestReadingEntity?.let {
            try {
                gson.fromJson(it.payloadJson, ReadingInModel::class.java)
            } catch (e: Exception) {
                null
            }
        }
    }

    // Monitor connected watch nodes
    LaunchedEffect(Unit) {
        while (true) {
            try {
                val nodes = Wearable.getNodeClient(context).connectedNodes.await()
                connectedWatchName = nodes.firstOrNull()?.displayName
            } catch (e: Exception) {
                connectedWatchName = null
            }
            delay(5000)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("WMAX Hamroh", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFFFAFAF8),
                    titleContentColor = Color(0xFF1C1B1F)
                )
            )
        },
        containerColor = Color(0xFFFAFAF8)
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Card 1: Watch Connection
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Aqlli soat holati", fontSize = 13.sp, color = Color(0xFF8A8780))
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .background(
                                    color = if (connectedWatchName != null) Color(0xFF2E7D5B) else Color(0xFFB3261E),
                                    shape = CircleShape
                                )
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = if (connectedWatchName != null) "Ulangan: $connectedWatchName" else "Soat ulanmagan",
                            fontSize = 15.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = Color(0xFF1C1B1F)
                        )
                    }
                }
            }

            // Card 2: Offline Buffer Queue
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Oflayn navbat buferi (Room DB)", fontSize = 13.sp, color = Color(0xFF8A8780))
                    Spacer(modifier = Modifier.height(6.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "$unsyncedCount ta o'lchov navbatda",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (unsyncedCount > 0) Color(0xFFC77A0A) else Color(0xFF2E7D5B)
                        )
                        Button(
                            onClick = {
                                isSyncing = true
                                SyncWorker.enqueueSync(context, expedited = true)
                                isSyncing = false
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = Color(0xFF2E7D5B)
                            ),
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            if (isSyncing) {
                                CircularProgressIndicator(modifier = Modifier.size(16.dp), color = Color.White)
                            } else {
                                Text("Sinxronlash", fontSize = 13.sp)
                            }
                        }
                    }
                }
            }

            // Card 3: Latest Biometric Reading Preview
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Oxirgi o'lchov", fontSize = 13.sp, color = Color(0xFF8A8780))
                    Spacer(modifier = Modifier.height(10.dp))
                    if (latestReading != null) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column {
                                Text("Puls (HR)", fontSize = 12.sp, color = Color(0xFF8A8780))
                                Text(
                                    text = latestReading.hrMean?.let { "%.1f bpm".format(it) } ?: "--",
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFFB3261E)
                                )
                            }
                            Column {
                                Text("SpO2", fontSize = 12.sp, color = Color(0xFF8A8780))
                                Text(
                                    text = latestReading.spo2?.let { "%.1f %%".format(it) } ?: "--",
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFF2E7D5B)
                                )
                            }
                            Column {
                                Text("Qadam", fontSize = 12.sp, color = Color(0xFF8A8780))
                                Text(
                                    text = latestReading.steps?.toString() ?: "0",
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFF1C1B1F)
                                )
                            }
                            Column {
                                Text("Holat", fontSize = 12.sp, color = Color(0xFF8A8780))
                                Text(
                                    text = if (latestReading.worn) "Taqilgan" else "Yechilgan",
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    color = Color(0xFF1C1B1F)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Vaqti: ${latestReading.ts}",
                            fontSize = 11.sp,
                            color = Color(0xFF8A8780)
                        )
                    } else {
                        Text(
                            text = "Soatdan o'lchovlar kutilmoqda...",
                            fontSize = 14.sp,
                            color = Color(0xFF8A8780)
                        )
                    }
                }
            }

            // Patient authentication and server settings
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Text(stringResource(uz.wmax.phone.R.string.settings_title), fontSize = 13.sp, color = Color(0xFF8A8780))
                    OutlinedTextField(
                        value = backendUrl,
                        onValueChange = {
                            backendUrl = it
                            prefs.edit().putString("backend_url", it).apply()
                        },
                        label = { Text(stringResource(uz.wmax.phone.R.string.backend_url_label)) },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = phone,
                        onValueChange = { phone = it },
                        label = { Text(stringResource(uz.wmax.phone.R.string.phone_label)) },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = pin,
                        onValueChange = { pin = it },
                        label = { Text(stringResource(uz.wmax.phone.R.string.pin_label)) },
                        modifier = Modifier.fillMaxWidth()
                    )
                    Button(
                        enabled = !isLoggingIn && phone.isNotBlank() && pin.isNotBlank(),
                        onClick = {
                            scope.launch {
                                isLoggingIn = true
                                authStatus = null
                                try {
                                    val api = WmaxApiService.create(backendUrl)
                                    val login = api.patientLogin(PatientLoginPayload(phone.trim(), pin.trim()))
                                    val tokens = login.body()
                                    if (!login.isSuccessful || tokens == null || tokens.role != "patient") {
                                        throw IllegalStateException("HTTP ${login.code()}")
                                    }
                                    val me = api.getMe("Bearer ${tokens.access_token}")
                                    val principal = me.body()
                                    if (!me.isSuccessful || principal == null || principal.role != "patient") {
                                        throw IllegalStateException("Patient profile unavailable")
                                    }
                                    patientId = principal.id
                                    prefs.edit()
                                        .putString("backend_url", backendUrl)
                                        .putString("patient_id", principal.id)
                                        .putString("access_token", tokens.access_token)
                                        .putString("refresh_token", tokens.refresh_token)
                                        .apply()
                                    pin = ""
                                    authStatus = context.getString(uz.wmax.phone.R.string.login_success, principal.full_name)
                                } catch (e: Exception) {
                                    authStatus = context.getString(uz.wmax.phone.R.string.login_failed)
                                } finally {
                                    isLoggingIn = false
                                }
                            }
                        }
                    ) { Text(stringResource(uz.wmax.phone.R.string.login_action)) }
                    Text(
                        patientId?.let { stringResource(uz.wmax.phone.R.string.patient_bound, it) }
                            ?: stringResource(uz.wmax.phone.R.string.patient_not_bound),
                        fontSize = 12.sp
                    )
                    authStatus?.let { Text(it, fontSize = 12.sp) }
                    OutlinedTextField(
                        value = ingestKey,
                        onValueChange = {
                            ingestKey = it
                            prefs.edit().putString("ingest_api_key", it).apply()
                        },
                        label = { Text(stringResource(uz.wmax.phone.R.string.device_key_label)) },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }
    }
}
