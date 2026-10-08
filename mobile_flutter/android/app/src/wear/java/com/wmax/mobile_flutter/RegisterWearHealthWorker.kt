package com.wmax.mobile_flutter

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat
import androidx.work.Worker
import androidx.work.WorkerParameters

class RegisterWearHealthWorker(
    context: Context,
    params: WorkerParameters,
) : Worker(context, params) {
    override fun doWork(): Result {
        val heartRatePermission = if (Build.VERSION.SDK_INT >= 36) {
            "android.permission.health.READ_HEART_RATE"
        } else {
            Manifest.permission.BODY_SENSORS
        }
        if (ContextCompat.checkSelfPermission(applicationContext, heartRatePermission)
            != PackageManager.PERMISSION_GRANTED
        ) {
            return Result.failure()
        }
        val backgroundPermission = if (Build.VERSION.SDK_INT >= 36) {
            "android.permission.health.READ_HEALTH_DATA_IN_BACKGROUND"
        } else {
            "android.permission.BODY_SENSORS_BACKGROUND"
        }
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(applicationContext, backgroundPermission)
            != PackageManager.PERMISSION_GRANTED
        ) {
            return Result.failure()
        }
        return if (WearHealthServices.registerBlocking(applicationContext) == null) {
            if (WearHealthOutbox.flushBlocking(applicationContext)) Result.success() else Result.retry()
        } else {
            Result.retry()
        }
    }
}
