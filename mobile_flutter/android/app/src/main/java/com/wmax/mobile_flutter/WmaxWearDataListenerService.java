package com.wmax.mobile_flutter;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;

import com.google.android.gms.wearable.DataEvent;
import com.google.android.gms.wearable.DataEventBuffer;
import com.google.android.gms.wearable.DataMapItem;
import com.google.android.gms.wearable.MessageEvent;
import com.google.android.gms.wearable.Wearable;
import com.google.android.gms.wearable.WearableListenerService;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

public class WmaxWearDataListenerService extends WearableListenerService {
    private static final String HEALTH_DATA_PATH = "/wmax/health-data";

    @Override
    public void onDataChanged(DataEventBuffer events) {
        try {
            for (DataEvent event : events) {
                if (event.getType() != DataEvent.TYPE_CHANGED) {
                    continue;
                }
                Uri uri = event.getDataItem().getUri();
                if (uri.getPath() == null || !uri.getPath().startsWith(HEALTH_DATA_PATH + "/")) {
                    continue;
                }
                String payload = DataMapItem.fromDataItem(event.getDataItem()).getDataMap().getString("payload");
                if (payload != null && !payload.trim().isEmpty() && enqueuePayload(this, payload)) {
                    Wearable.getDataClient(this).deleteDataItems(uri);
                }
            }
        } finally {
            events.release();
        }
    }

    static ArrayList<String> getQueuedPayloads(Context context) {
        synchronized (WmaxWearDataListenerService.class) {
            SharedPreferences prefs = context.getSharedPreferences("wmax_wear_queue", Context.MODE_PRIVATE);
            return new ArrayList<>(prefs.getStringSet("payloads", new HashSet<>()));
        }
    }

    static void acknowledgePayloads(Context context, ArrayList<String> acknowledged) {
        if (acknowledged == null || acknowledged.isEmpty()) {
            return;
        }
        synchronized (WmaxWearDataListenerService.class) {
            SharedPreferences prefs = context.getSharedPreferences("wmax_wear_queue", Context.MODE_PRIVATE);
            Set<String> remaining = new HashSet<>(prefs.getStringSet("payloads", new HashSet<>()));
            remaining.removeAll(acknowledged);
            prefs.edit().putStringSet("payloads", remaining).commit();
        }
    }

    private static boolean enqueuePayload(Context context, String payload) {
        synchronized (WmaxWearDataListenerService.class) {
            SharedPreferences prefs = context.getSharedPreferences("wmax_wear_queue", Context.MODE_PRIVATE);
            Set<String> current = new HashSet<>(prefs.getStringSet("payloads", new HashSet<>()));
            current.add(payload);
            return prefs.edit().putStringSet("payloads", current).commit();
        }
    }

    @Override
    public void onMessageReceived(MessageEvent messageEvent) {
        if (!HEALTH_DATA_PATH.equals(messageEvent.getPath())) {
            return;
        }
        String payload = new String(messageEvent.getData(), StandardCharsets.UTF_8);
        if (payload.trim().isEmpty()) {
            return;
        }
        enqueuePayload(this, payload);
    }
}
