package com.wmax.mobile_flutter

import android.content.Context

object WearHealthServices {
    @JvmStatic
    fun register(context: Context, callback: WearHealthRegistrationCallback) {
        callback.onComplete(false, "NOT_WEAR_BUILD")
    }
}
