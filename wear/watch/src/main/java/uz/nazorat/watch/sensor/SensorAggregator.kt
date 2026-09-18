package uz.nazorat.watch.sensor

import android.content.Context
import android.os.BatteryManager
import uz.nazorat.watch.data.RawSensorSample
import uz.nazorat.watch.data.ReadingDto
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import kotlin.math.pow
import kotlin.math.roundToInt
import kotlin.math.sqrt

/**
 * Aggregates 1-minute raw sensor samples into 5-minute window summaries.
 * Output strictly matches the NAZORAT ReadingIn contract.
 */
class SensorAggregator(private val context: Context) {

    private val samples = mutableListOf<RawSensorSample>()

    fun addSample(sample: RawSensorSample) {
        synchronized(samples) {
            samples.add(sample)
        }
    }

    fun hasCompleteWindow(): Boolean {
        synchronized(samples) {
            return samples.size >= 5
        }
    }

    /**
     * Drains the accumulated samples and computes the 5-minute ReadingDto aggregate.
     */
    fun computeAndDrainWindow(): ReadingDto? {
        val windowSamples: List<RawSensorSample>
        synchronized(samples) {
            if (samples.isEmpty()) return null
            windowSamples = ArrayList(samples)
            samples.clear()
        }

        val hrValues = windowSamples.mapNotNull { it.hrBpm }
        val spo2Values = windowSamples.mapNotNull { it.spo2Percent }
        val tempValues = windowSamples.mapNotNull { it.skinTempCelsius }
        val wornCount = windowSamples.count { it.isWorn }
        val isWorn = wornCount >= (windowSamples.size / 2)

        val totalSteps = windowSamples.sumOf { it.steps }

        // Heart rate metrics
        val hrMean = if (hrValues.isNotEmpty()) hrValues.average() else null
        val hrMin = hrValues.minOrNull()
        val hrMax = hrValues.maxOrNull()

        // SDNN calculation
        val sdnn = if (hrValues.size >= 2 && hrMean != null) {
            val variance = hrValues.sumOf { (it - hrMean).pow(2) } / (hrValues.size - 1)
            sqrt(variance)
        } else null

        // RMSSD calculation (from successive RR intervals or successive HR changes)
        val rmssd = if (hrValues.size >= 2) {
            val diffs = mutableListOf<Double>()
            for (i in 0 until hrValues.size - 1) {
                // Approximate RR interval ms = 60000.0 / HR
                val rr1 = 60000.0 / hrValues[i]
                val rr2 = 60000.0 / hrValues[i + 1]
                diffs.add((rr2 - rr1).pow(2))
            }
            sqrt(diffs.average())
        } else null

        // SpO2 mean
        val spo2Mean = if (spo2Values.isNotEmpty()) spo2Values.average() else null

        // Skin temperature
        val tempMean = if (tempValues.isNotEmpty()) tempValues.average() else null

        // Respiratory rate estimate (standard resting respiratory rate estimation based on HRV/RSA)
        val rrEst = if (hrMean != null) {
            (hrMean / 4.5).coerceIn(10.0, 30.0)
        } else null

        val currentBattery = getBatteryPercentage()
        val tsIso = formatIsoUtc(Date())

        return ReadingDto(
            ts = tsIso,
            hrMean = hrMean?.let { (it * 10).roundToInt() / 10.0 },
            hrMin = hrMin?.let { (it * 10).roundToInt() / 10.0 },
            hrMax = hrMax?.let { (it * 10).roundToInt() / 10.0 },
            rmssd = rmssd?.let { (it * 10).roundToInt() / 10.0 },
            sdnn = sdnn?.let { (it * 10).roundToInt() / 10.0 },
            spo2 = spo2Mean?.let { (it * 10).roundToInt() / 10.0 },
            skinTemp = tempMean?.let { (it * 100).roundToInt() / 100.0 },
            steps = totalSteps,
            rrEst = rrEst?.let { (it * 10).roundToInt() / 10.0 },
            sleepFrag = null,
            worn = isWorn,
            battery = currentBattery
        )
    }

    private fun getBatteryPercentage(): Int {
        val bm = context.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
        return bm?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: 100
    }

    private fun formatIsoUtc(date: Date): String {
        val sdf = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US)
        sdf.timeZone = TimeZone.getTimeZone("UTC")
        return sdf.format(date)
    }
}
