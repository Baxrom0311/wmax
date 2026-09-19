package uz.wmax.watch.presentation

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.wear.compose.material.Button
import androidx.wear.compose.material.ButtonDefaults
import androidx.wear.compose.material.CircularProgressIndicator
import androidx.wear.compose.material.Text
import kotlinx.coroutines.delay
import uz.wmax.watch.R

/**
 * Haptic feedback helper for emergency gestures on Wear OS.
 */
fun vibrateDevice(context: Context, durationMs: Long = 100) {
    try {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            vibratorManager?.defaultVibrator?.vibrate(
                VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE)
            )
        } else {
            @Suppress("DEPRECATION")
            val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            @Suppress("DEPRECATION")
            vibrator?.vibrate(durationMs)
        }
    } catch (_: Exception) {}
}

/**
 * Stage 1: 3-Second Hold SOS Emergency Button (Circular Screen Optimized).
 * Fits the bottom curve of the round watch display with large touch target.
 */
@Composable
fun SosHoldButton(
    onTriggerCountdown: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var isPressed by remember { mutableStateOf(false) }
    var holdProgress by remember { mutableFloatStateOf(0f) }

    LaunchedEffect(isPressed) {
        if (isPressed) {
            val startTime = System.currentTimeMillis()
            vibrateDevice(context, 40)
            while (isPressed && holdProgress < 1f) {
                val elapsed = System.currentTimeMillis() - startTime
                holdProgress = (elapsed / 2500f).coerceIn(0f, 1f)
                if (holdProgress >= 1f) {
                    vibrateDevice(context, 350)
                    onTriggerCountdown()
                    isPressed = false
                    holdProgress = 0f
                    break
                }
                delay(16)
            }
        } else {
            holdProgress = 0f
        }
    }

    Box(
        contentAlignment = Alignment.Center,
        modifier = modifier
            .size(68.dp)
            .pointerInput(Unit) {
                detectTapGestures(
                    onPress = {
                        isPressed = true
                        tryAwaitRelease()
                        isPressed = false
                    },
                    onTap = {
                        vibrateDevice(context, 150)
                        onTriggerCountdown()
                    }
                )
            }
    ) {
        // Radial progress stroke when held
        if (holdProgress > 0f) {
            CircularProgressIndicator(
                progress = holdProgress,
                modifier = Modifier.fillMaxSize(),
                indicatorColor = Color(0xFFEF4444),
                trackColor = Color(0x33EF4444),
                strokeWidth = 4.dp
            )
        }

        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .size(60.dp)
                .background(
                    brush = Brush.radialGradient(
                        colors = listOf(Color(0xFFEF4444), Color(0xFFB91C1C), Color(0xFF7F1D1D))
                    ),
                    shape = CircleShape
                )
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = "SOS",
                    color = Color.White,
                    fontWeight = FontWeight.Black,
                    fontSize = 17.sp,
                    letterSpacing = 0.5.sp
                )
                if (isPressed) {
                    Text(
                        text = stringResource(R.string.sos_hold),
                        color = Color(0xFFFECACA),
                        fontSize = 7.5.sp,
                        maxLines = 1
                    )
                }
            }
        }
    }
}

/**
 * Stage 2: Standard Touch Screen Countdown Screen.
 */
@Composable
fun SosCountdownConfirmScreen(
    onConfirmed: () -> Unit,
    onCancelled: () -> Unit
) {
    val context = LocalContext.current
    var secondsLeft by remember { mutableIntStateOf(5) }

    LaunchedEffect(Unit) {
        while (secondsLeft > 0) {
            vibrateDevice(context, 70)
            delay(1000)
            secondsLeft -= 1
        }
        vibrateDevice(context, 500)
        onConfirmed()
    }

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF3B0707))
            .padding(20.dp)
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.fillMaxSize()
        ) {
            Text(
                text = stringResource(R.string.sos_sending),
                color = Color(0xFFFCA5A5),
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp,
                letterSpacing = 1.sp
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "$secondsLeft",
                color = Color.White,
                fontWeight = FontWeight.Black,
                fontSize = 54.sp
            )

            Text(
                text = stringResource(R.string.sos_help_notice),
                color = Color(0xFFE2E8F0),
                fontSize = 11.sp,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(12.dp))

            Button(
                onClick = {
                    vibrateDevice(context, 50)
                    onCancelled()
                },
                colors = ButtonDefaults.buttonColors(
                    backgroundColor = Color(0xFF1E293B),
                    contentColor = Color.White
                ),
                modifier = Modifier
                    .fillMaxWidth(0.78f)
                    .height(38.dp)
            ) {
                Text(
                    text = stringResource(R.string.cancel),
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

/**
 * Stage 3: Standard Touch Screen Dispatched Screen.
 */
@Composable
fun SosDispatchedScreen(
    onCancelRequested: () -> Unit,
    onDone: () -> Unit
) {
    var cancelWindowSeconds by remember { mutableIntStateOf(30) }

    LaunchedEffect(Unit) {
        while (cancelWindowSeconds > 0) {
            delay(1000)
            cancelWindowSeconds -= 1
        }
    }

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF064E3B))
            .padding(20.dp)
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.fillMaxSize()
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(Color(0xFF10B981), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Text("✓", color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Black)
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = stringResource(R.string.sos_sent),
                color = Color(0xFF6EE7B7),
                fontWeight = FontWeight.ExtraBold,
                fontSize = 15.sp
            )

            Spacer(modifier = Modifier.height(2.dp))

            Text(
                text = stringResource(R.string.sos_sent_notice),
                color = Color(0xFFF1F5F9),
                fontSize = 11.sp,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(12.dp))

            if (cancelWindowSeconds > 0) {
                Button(
                    onClick = onCancelRequested,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = Color(0xFF991B1B),
                        contentColor = Color.White
                    ),
                    modifier = Modifier
                        .fillMaxWidth(0.82f)
                        .height(36.dp)
                ) {
                    Text(
                        "${stringResource(R.string.cancel)} ($cancelWindowSeconds)",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            } else {
                Button(
                    onClick = onDone,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = Color(0xFF047857),
                        contentColor = Color.White
                    ),
                    modifier = Modifier
                        .fillMaxWidth(0.82f)
                        .height(36.dp)
                ) {
                    Text(
                        stringResource(R.string.understood),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

/**
 * Distinct Hardware Side Button SOS: 3-Second Rapid Emergency Countdown.
 * Triggers when the patient presses the physical side button on the Galaxy Watch.
 */
@Composable
fun HardwareSosCountdownScreen(
    currentHr: Double,
    currentSpo2: Double,
    onConfirmed: () -> Unit,
    onCancelled: () -> Unit
) {
    val context = LocalContext.current
    var secondsLeft by remember { mutableIntStateOf(3) }

    LaunchedEffect(Unit) {
        while (secondsLeft > 0) {
            vibrateDevice(context, 75)
            delay(120)
            vibrateDevice(context, 75)
            delay(800)
            secondsLeft -= 1
        }
        vibrateDevice(context, 600)
        onConfirmed()
    }

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .fillMaxSize()
            .background(
                brush = Brush.radialGradient(
                    colors = listOf(Color(0xFF581C87), Color(0xFF450A0A), Color.Black)
                )
            )
            .padding(16.dp)
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.fillMaxSize()
        ) {
            Text(
                text = stringResource(R.string.hardware_sos_title),
                color = Color(0xFFE9D5FF),
                fontWeight = FontWeight.ExtraBold,
                fontSize = 12.sp,
                letterSpacing = 0.5.sp
            )

            Text(
                text = stringResource(R.string.hardware_sos_desc),
                color = Color(0xFFFCA5A5),
                fontSize = 9.sp,
                fontWeight = FontWeight.Medium
            )

            Spacer(modifier = Modifier.height(2.dp))

            Text(
                text = "$secondsLeft",
                color = Color.White,
                fontWeight = FontWeight.Black,
                fontSize = 52.sp
            )

            // Vitals snapshot during emergency
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center,
                modifier = Modifier
                    .background(Color(0x33FFFFFF), RoundedCornerShape(8.dp))
                    .padding(horizontal = 8.dp, vertical = 2.dp)
            ) {
                Text("❤️ %.0f bpm".format(currentHr), fontSize = 10.sp, color = Color.White, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.width(6.dp))
                Text("SpO2 %.0f%%".format(currentSpo2), fontSize = 10.sp, color = Color(0xFF38BDF8), fontWeight = FontWeight.Bold)
            }

            Spacer(modifier = Modifier.height(8.dp))

            Button(
                onClick = {
                    vibrateDevice(context, 50)
                    onCancelled()
                },
                colors = ButtonDefaults.buttonColors(
                    backgroundColor = Color(0xFF1E293B),
                    contentColor = Color.White
                ),
                modifier = Modifier
                    .fillMaxWidth(0.78f)
                    .height(34.dp)
            ) {
                Text(
                    text = stringResource(R.string.cancel),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

/**
 * Distinct Hardware Side Button SOS Dispatched Screen.
 */
@Composable
fun HardwareSosDispatchedScreen(
    onCancelRequested: () -> Unit,
    onDone: () -> Unit
) {
    var cancelWindowSeconds by remember { mutableIntStateOf(30) }

    LaunchedEffect(Unit) {
        while (cancelWindowSeconds > 0) {
            delay(1000)
            cancelWindowSeconds -= 1
        }
    }

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1E1B4B))
            .padding(18.dp)
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.fillMaxSize()
        ) {
            Box(
                modifier = Modifier
                    .size(38.dp)
                    .background(Color(0xFF8B5CF6), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Text("⚡", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Black)
            }

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = stringResource(R.string.hardware_sos_sent),
                color = Color(0xFFDDD6FE),
                fontWeight = FontWeight.ExtraBold,
                fontSize = 12.5.sp,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(2.dp))

            Text(
                text = stringResource(R.string.hardware_sos_sent_desc),
                color = Color(0xFFE2E8F0),
                fontSize = 10.sp,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(10.dp))

            if (cancelWindowSeconds > 0) {
                Button(
                    onClick = onCancelRequested,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = Color(0xFF7C3AED),
                        contentColor = Color.White
                    ),
                    modifier = Modifier
                        .fillMaxWidth(0.82f)
                        .height(34.dp)
                ) {
                    Text(
                        "${stringResource(R.string.cancel)} ($cancelWindowSeconds)",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            } else {
                Button(
                    onClick = onDone,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = Color(0xFF047857),
                        contentColor = Color.White
                    ),
                    modifier = Modifier
                        .fillMaxWidth(0.82f)
                        .height(34.dp)
                ) {
                    Text(
                        stringResource(R.string.understood),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}
