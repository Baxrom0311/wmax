package com.wmax.mobile_flutter

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager

class WearBootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED) return
        val request = OneTimeWorkRequestBuilder<RegisterWearHealthWorker>().build()
        WorkManager.getInstance(context).enqueueUniqueWork(
            "register_wear_health_services",
            ExistingWorkPolicy.KEEP,
            request,
        )
    }
}
