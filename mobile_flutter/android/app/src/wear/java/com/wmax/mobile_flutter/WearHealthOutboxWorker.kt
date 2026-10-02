package com.wmax.mobile_flutter

import android.content.Context
import androidx.work.Worker
import androidx.work.WorkerParameters

class WearHealthOutboxWorker(
    context: Context,
    params: WorkerParameters,
) : Worker(context, params) {
    override fun doWork(): Result = if (WearHealthOutbox.flushBlocking(applicationContext)) {
        Result.success()
    } else {
        Result.retry()
    }
}
