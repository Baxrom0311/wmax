package com.wmax.mobile_flutter

import android.content.Context

object WearHealthServices {
    @JvmStatic
    fun capabilitySnapshot(context: Context): Map<String, Any> = mapOf(
        "wear_os" to false,
        "passive_data_types" to emptyList<String>(),
        "exercise_types" to emptyList<String>(),
    )

    @JvmStatic
    fun register(context: Context, callback: WearHealthRegistrationCallback) {
        callback.onComplete(false, "NOT_WEAR_BUILD")
    }
}
