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
        if (ContextCompat.checkSelfPermission(applicationContext, Manifest.permission.BODY_SENSORS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            return Result.failure()
        }
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(applicationContext, "android.permission.BODY_SENSORS_BACKGROUND")
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
