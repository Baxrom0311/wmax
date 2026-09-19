package uz.wmax.watch.presentation

import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
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
 * Stage 1: 3-Second Hold SOS Emergency Button (Prevents accidental trigger by elderly patients).
 */
@Composable
fun SosHoldButton(
    onTriggerCountdown: () -> Unit,
    modifier: Modifier = Modifier
) {
    var isPressed by remember { mutableStateOf(false) }
    var holdProgress by remember { mutableFloatStateOf(0f) }

    LaunchedEffect(isPressed) {
        if (isPressed) {
            val startTime = System.currentTimeMillis()
            while (isPressed && holdProgress < 1f) {
                val elapsed = System.currentTimeMillis() - startTime
                holdProgress = (elapsed / 3000f).coerceIn(0f, 1f)
                if (holdProgress >= 1f) {
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
            .size(62.dp)
            .pointerInput(Unit) {
                detectTapGestures(
                    onPress = {
                        isPressed = true
                        tryAwaitRelease()
                        isPressed = false
                    }
                )
            }
    ) {
        // Outer circular progress during hold
        if (holdProgress > 0f) {
            CircularProgressIndicator(
                progress = holdProgress,
                modifier = Modifier.fillMaxSize(),
                indicatorColor = Color(0xFFB3261E),
                strokeWidth = 4.dp
            )
        }

        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .size(56.dp)
                .background(Color(0xFFB3261E), CircleShape)
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "SOS",
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 17.sp
                )
                if (isPressed) {
                    Text(
                        text = stringResource(R.string.sos_hold),
                        color = Color(0xFFFFD8D6),
                        fontSize = 8.sp
                    )
                }
            }
        }
    }
}

/**
 * Stage 2: 10-Second Countdown Confirmation Screen before transmitting emergency alert.
 */
@Composable
fun SosCountdownConfirmScreen(
    onConfirmed: () -> Unit,
    onCancelled: () -> Unit
) {
    var secondsLeft by remember { mutableIntStateOf(10) }

    LaunchedEffect(Unit) {
        while (secondsLeft > 0) {
            delay(1000)
            secondsLeft -= 1
        }
        onConfirmed()
    }

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1C1B1F))
            .padding(16.dp)
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = stringResource(R.string.sos_sending),
                color = Color(0xFFFF897D),
                fontWeight = FontWeight.Bold,
                fontSize = 14.sp
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = "$secondsLeft",
                color = Color.White,
                fontWeight = FontWeight.Black,
                fontSize = 42.sp
            )

            Text(
                text = stringResource(R.string.sos_help_notice),
                color = Color(0xFFC4C7C5),
                fontSize = 11.sp,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(10.dp))

            Button(
                onClick = onCancelled,
                colors = ButtonDefaults.buttonColors(
                    backgroundColor = Color(0xFF49454F),
                    contentColor = Color.White
                ),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(38.dp)
            ) {
                Text(stringResource(R.string.cancel), fontSize = 12.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}

/**
 * Stage 3: Dispatched confirmation with 30s cancellation window.
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
            .background(Color(0xFF140C0B))
            .padding(14.dp)
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = stringResource(R.string.sos_sent),
                color = Color(0xFF73DA9E),
                fontWeight = FontWeight.Bold,
                fontSize = 15.sp
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = stringResource(R.string.sos_sent_notice),
                color = Color(0xFFE6E1E5),
                fontSize = 10.sp,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            if (cancelWindowSeconds > 0) {
                Button(
                    onClick = onCancelRequested,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = Color(0xFF8C1D18),
                        contentColor = Color.White
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(34.dp)
                ) {
                    Text("${stringResource(R.string.cancel)} ($cancelWindowSeconds)", fontSize = 11.sp)
                }
            } else {
                Button(
                    onClick = onDone,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = Color(0xFF2E7D5B),
                        contentColor = Color.White
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(34.dp)
                ) {
                    Text(stringResource(R.string.understood), fontSize = 11.sp)
                }
            }
        }
    }
}
